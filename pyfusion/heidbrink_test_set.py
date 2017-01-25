'''
Email from Heidbrink:
John,
  Here's a shotlist assembled with the goal of making sure you know what you are doing.
  These are all discharges with 200 kHz sampling on the magnetics.
  We often sample at 500 kHz for our dedicated experiments.
  The activity isn't particularly interesting.
  Most shots have the instability that's called a neoclassical tearing mode (NTM).
  But it's easy to check what we should get.
  There's a simpler program that calculates the toroidal mode number from the phase
  difference of two probes.
  You run it like this:
> newspec
newspec> sh 153067,xmin 2900,xmax 3100,pl

It plots the modes with color coding for the mode number.
I think your clustering analysis should group the steady n=2 modes that occur on many of the shots together.
We'll see.  A time window of 200 ms is sufficient for all of these shots.

SHOT  TMIN (ms)
153067 2900
153071 2900
153072 2900
152932 2600
152938 3100
157399 2400
157400 2400
157401 2400
157402 2400
'''
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
    if time_window == None: time_window = [1000, 5000]
    dev = pf.getDevice('DIIID')
    mag = dev.acq.getdata(shot, 'DIIID_toroidal_mag')
    # mag contains the signal and timebase of the raw data
    # In [171]: mag.signal.shape
    # Out[171]: (14, 2039808)
    # In [172]: mag.timebase.shape
    # Out[174]: (2039808,)

    # Reduce the data to the time window we care about
    mag_red = mag.reduce_time(time_window)

    # Settings for performing the fft, i.e break the above signal into chunks 1024 samples long
    # and allow subsequent chunks to overlap
    samples = 1024;
    overlap = 4
    data_fft = mag_red.generate_frequency_series(samples, samples / overlap)

    # Some settings
    n_pts = 20;
    lower_freq = 1;
    cutoff_by = 'sigma_eq';
    filter_cutoff = 55;
    datamining_settings = None;
    upper_freq = 500000;
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

    instance_array_amps = +rel_data

    # STFT-clustering includes a clustering step before we get to the main clustering.
    # This is essentially to filter out any rubbish
    datamining_settings = {'n_clusters': 16, 'n_iterations': 20, 'start': 'k_means', 'verbose': 0, 'method': 'EM_VMM'}
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

def create_feature_object(shots,time_windows,savename):
    input_data_iter = itertools.izip(shots, time_windows)
    wrapper = get_stft_wrapper
    #n_cpus = 4
    #pool = Pool(processes=n_cpus, maxtasksperchild=3)
    results = map(wrapper, input_data_iter)
    #pool.close()
    #pool.join()
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
    print("Before clustering.")
    feat_obj = clust.feature_object(instance_array=instance_array,
                                    instance_array_amps=+misc_data_dict['mirnov_data'],
                                    misc_data_dict=misc_data_dict)
    feat_obj.dump_data(savename)
    return

if __name__ == "__main__":
    shots = [153067, 153071, 153072, 152932, 152938, 157399, 157400, 157401, 157402]
    time_windows = [[2800, 3000], [2800, 3000], [2800, 3000], [2500, 2700], [3000, 3200],
                   [2300, 2500], [2300, 2500], [2300, 2500], [2300, 2500]]
    savename="heidbrink_test_set_feature_object.pickle"
    create_feature_object(shots,time_windows,savename)
    datamining_settings = {'n_clusters': 16, 'n_iterations': 20,
                           'start': 'k_means', 'verbose': 0, 'method': 'EM_VMM'}
