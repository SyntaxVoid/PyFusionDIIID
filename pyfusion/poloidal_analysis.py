from multiprocessing import Pool
import pyfusion as pf
import numpy as np
import copy, os, time, itertools
import matplotlib.pyplot as plt
import cPickle as pickle
import pyfusion.clustering as clust
import pyfusion.clustering.extract_features_scans as ext


def get_single(shot, time_window=None):
    if time_window == None:
        time_window = [2000, 5000]
    cache_name = '/u/haskeysr/tmp/{}.pickle'.format(shot)
    start_time = time.time()
    dev = pf.getDevice('DIIID')
    mag = dev.acq.getdata(shot, 'DIIID_toroidal_mag')
    print('Data fetch time {:.2f}s'.format(time.time() - start_time))
    mag_red = mag.reduce_time(time_window)
    samples = 1024
    overlap = 4
    data = mag_red.subtract_mean(copy=False).normalise(method='v', separate=True, copy=True)
    data_segmented = data.segment(samples, overlap=overlap, datalist=1)
    settings = {'min_svs': 2, 'power_cutoff': 0.000, 'lower_freq': 0, 'upper_freq': 200000}
    misc_data_dict = {'svs': [], 'RMS': [], 'time': [], 'freq': [], 'mirnov_data': [], 'shot': []}
    instance_array_list = []
    for seg_loc in range(len(data_segmented)):
        if ((seg_loc % 50) == 0):
            print shot, seg_loc, 'of', len(data_segmented)
        data_seg = data_segmented[seg_loc]
        fs_set = data_seg.flucstruc()
        valid_fs = []
        for fs in fs_set:
            tmp_valid = (fs.p > settings['power_cutoff']) and (len(fs.svs()) >= settings['min_svs']) and (
            fs.freq > settings['lower_freq']) and (fs.freq < settings['upper_freq'])
            if tmp_valid:
                valid_fs.append(fs)
        for fs in valid_fs:
            misc_data_dict['svs'].append(len(fs.svs()))
            misc_data_dict['RMS'].append((np.mean(data.scales ** 2)) ** 0.5)
            misc_data_dict['time'].append(fs.t0)
            misc_data_dict['freq'].append(fs.freq)
            misc_data_dict['shot'].append(shot)
            phases = np.array([tmp_phase.delta for tmp_phase in fs.dphase])
            phases[np.abs(phases) < 0.001] = 0
            instance_array_list.append(phases)
    for i in misc_data_dict.keys():
        misc_data_dict[i] = np.array(misc_data_dict[i])
    instance_array = np.array(instance_array_list)
    return instance_array, misc_data_dict, mag.signal, mag.timebase


def get_stft(shot, time_window=None):
    '''STFT-clustering to extract features from a single shot
    '''
    if time_window == None: time_window = [1000, 5000]
    dev = pf.getDevice('DIIID')
    mag = dev.acq.getdata(shot, 'DIIID_toroidal_mag')
    mag_red = mag.reduce_time(time_window)
    samples = 1024
    overlap = 4
    data_fft = mag_red.generate_frequency_series(samples, samples / overlap)
    # Some settings
    n_pts = 10
    lower_freq = 1
    cutoff_by = 'sigma_eq'
    filter_cutoff = 75
    datamining_settings = None
    upper_freq = 500000
    filter_item = 'EM_VMM_kappas'
    # Find peaks int fft data (i.e probably modes), and only keep those:
    good_indices = ext.find_peaks(data_fft, n_pts=n_pts, lower_freq=lower_freq, upper_freq=upper_freq)
    rel_data = ext.return_values(data_fft.signal, good_indices)
    # Put together some meta-data that should be useful later
    misc_data_dict = {}
    misc_data_dict['time'] = ext.return_time_values(data_fft.timebase, good_indices)
    misc_data_dict['freq'] = ext.return_non_freq_dependent(data_fft.frequency_base, good_indices)
    misc_data_dict['shot'] = np.ones(len(misc_data_dict['freq']), dtype=int) * shot
    # Not really meta-data, but can be useful to keep this for later
    misc_data_dict['mirnov_data'] = +rel_data
    # Calculate the phase differences between probes - this is the thing used for datamining!
    rel_data_angles = np.angle(rel_data)
    diff_angles = (np.diff(rel_data_angles)) % (2. * np.pi)
    # Also important to map to -pi, pi
    diff_angles[diff_angles > np.pi] -= (2. * np.pi)
    # STFT-clustering includes a clustering step before we get to the main clustering.
    # This is essentially to filter out any rubbish
    datamining_settings = {'n_clusters': 8, 'n_iterations': 20, 'start': 'k_means', 'verbose': 0, 'method': 'EM_VMM'}
    z = ext.perform_data_datamining(diff_angles, misc_data_dict, datamining_settings)
    dt = np.mean(np.diff(mag.timebase))
    # Only keep instances that belong to well defined clusters - i.e useful information instead of noise
    instance_array_cur, misc_data_dict_cur = ext.filter_by_kappa_cutoff(z, ave_kappa_cutoff=filter_cutoff, ax=None,
                                                                        cutoff_by=cutoff_by, filter_item=filter_item)
    # Return this data from a single shot to be used in the big clustering step that involves all the shots
    instance_array = np.array(instance_array_cur)
    misc_data_dict = misc_data_dict_cur
    return instance_array, misc_data_dict, mag.signal, mag.timebase

def get_single_wrapper(input_data):
    print 'in wrapper svd'
    return copy.deepcopy(get_single(input_data[0], time_window=input_data[1]))

def get_stft_wrapper(input_data):
    print 'in wrapper stft'
    return copy.deepcopy(get_stft(input_data[0], time_window=input_data[1]))



if __name__ == '__main__':
    shot_list = range(159243,159257+1)
    time_window = [300,1400]
    input_data_iter = itertools.izip(shot_list,itertools.repeat(time_window))
    wrapper = get_stft_wrapper
    n_cpus = 4
    if n_cpus > 1:
        pool_size = n_cpus
        pool = Pool(processes=pool_size, maxtasksperchild=3)
        results = pool.map(wrapper, input_data_iter)
        pool.close()
        pool.join()
    else:
        results = map(wrapper, input_data_iter)
start = 1
for i, tmp in enumerate(results):
    print i
    if tmp[0] != None:
        if start == 1:
            instance_array = copy.deepcopy(tmp[0])
            misc_data_dict = copy.deepcopy(tmp[1])
            start = 0
        else:
            instance_array = np.append(instance_array, tmp[0], axis=0)
            for i in misc_data_dict.keys():
                misc_data_dict[i] = np.append(misc_data_dict[i], tmp[1][i], axis=0)
    else:
        print 'One shot may have failed....'
    feat_obj = clust.feature_object(instance_array=instance_array, instance_array_amps=+misc_data_dict['mirnov_data'],
                                misc_data_dict=misc_data_dict)
    datamining_settings = {'n_clusters': 8, 'n_iterations': 20,
                       'start': 'k_means', 'verbose': 0, 'method': 'EM_VMM'}
    z = feat_obj.cluster(**datamining_settings)

    print("Plotting...")

    nrows = 6
    ncols = 6
    fig, ax = plt.subplots(nrows=nrows, ncols=ncols, sharex=False, sharey=False)
    axf = ax.flatten()
    fig2, ax2 = plt.subplots(nrows=nrows, ncols=ncols, sharex=False, sharey=False)
    axf2 = ax2.flatten()
    plot_colors = {}
    for cur_ax, cur_ax2, shot, tmp in zip(axf, axf2, shot_list, results):
        assign = z.cluster_assignments
        details = z.cluster_details['EM_VMM_kappas']
        shot_details = z.feature_obj.misc_data_dict['shot']
        timebase = tmp[3]
        sig = tmp[2]
        dt = np.mean(np.diff(timebase))
        # tmp_sig = np.sqrt(np.sum(sig**2,axis=0))
        tmp_sig = sig[0, :]
        im = cur_ax.specgram(tmp_sig, NFFT=1024, Fs=1. / dt, noverlap=128, xextent=[timebase[0], timebase[-1]])
        im = cur_ax2.specgram(tmp_sig, NFFT=1024, Fs=1. / dt, noverlap=128, xextent=[timebase[0], timebase[-1]])
        for i in np.unique(assign):
            mask = (assign == i) * (shot_details == shot)
            if np.sum(mask) > 1 and np.mean(details[i, :]) > 5:
                if i not in plot_colors:
                    markersize = 5
                    pl = cur_ax.plot(z.feature_obj.misc_data_dict['time'][mask], z.feature_obj.misc_data_dict['freq'][mask],
                                     'o', markersize=markersize)
                    # pl = cur_ax.scatter(z.feature_obj.misc_data_dict['time'][mask], z.feature_obj.misc_data_dict['freq'][mask], alpha=0.3)
                    plot_colors[i] = pl[0].get_color()
                    # plot_colors[i] = (pl.get_facecolor(), pl.get_edgecolor())
                else:
                    pl = cur_ax.plot(z.feature_obj.misc_data_dict['time'][mask], z.feature_obj.misc_data_dict['freq'][mask],
                                     'o', markersize=markersize, color=plot_colors[i])
                    # pl = cur_ax.scatter(z.feature_obj.misc_data_dict['time'][mask], z.feature_obj.misc_data_dict['freq'][mask], facecolor=plot_colors[i][0],edgecolor=plot_colors[i][1],alpha=0.3)
                    # cur_ax.plot(misc_data_dict['time'][shot_details==shot], misc_data_dict['freq'][shot_details==shot], '.',color='white',markersize=5)
    # axf[0].set_xlim(time_window)
    # axf2[0].set_xlim(time_window)

    tmp = len(shot_list)
    for _ in range(tmp):
        axf[_].set_xlim(time_window)
        axf2[_].set_xlim(time_window)
        axf[_].set_ylim([0, 100])
        axf2[_].set_ylim([0, 100])
    # axf[0].set_xlim([2800,3000])
    # axf2[0].set_xlim([2800,3000])

    # fig.subplots_adjust(bottom=0.02, left=0.02, right=0.95, top=0.95,wspace=0.01,hspace=0.01)
    # fig2.subplots_adjust(bottom=0.02, left=0.02, right=0.95, top=0.95,wspace=0.01,hspace=0.01)
    fig.canvas.draw()
    fig.show()
    fig2.canvas.draw()
    fig2.show()