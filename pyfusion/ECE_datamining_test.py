from multiprocessing import Pool
import pyfusion as pf
import numpy as np
import copy, os, time, itertools
import matplotlib.pyplot as plt
import cPickle as pickle
import pyfusion.clustering as clust
import pyfusion.clustering.extract_features_scans as ext




if __name__ == '__main__':
    shot = 159243
    time_window = [300,1400]
    dev = pf.getDevice("DIIID")
    mag = dev.acq.getdata(shot, "ECEF_array_red")
    mag_red = mag.reduce_time(time_window)
    samples=1024
    overlap = 4
    data_fft = mag_red.generate_frequency_series(samples,samples/overlap)

    n_pts = 20
    lower_freq = 1
    cutoff_by = "sigma_eq"
    filter_cutoff = 70
    dms = None
    upper_freq = 500000
    filter_item = "EM_VMM_kappas"

    good_indices = ext.find_peaks(data_fft, n_pts=n_pts, lower_freq=lower_freq, upper_freq=upper_freq)
    rel_data = ext.return_values(data_fft.signal, good_indices)

    mdd = {}
    mdd["time"] = ext.return_time_values(data_fft.timebase, good_indices)
    mdd["freq"] = ext.return_non_freq_dependent(data_fft.frequency_base, good_indices)
    mdd["shot"] = np.ones(len(mdd["freq"]), dtype=int)*shot
    mdd["mirnov_data"] = rel_data


    rel_data_angles = np.angle(rel_data)
    diff_angles = (np.diff(rel_data_angles))%(2.*np.pi)

    diff_angles[diff_angles>np.pi] -= (2.*np.pi)
    ia_amps = +rel_data
    dms = {"n_clusters":16, "n_iterations":20, "start": "k_means", "verbose":0, "method": "EM_VMM"}
    z = ext.perform_data_datamining(diff_angles, mdd, dms)

    dt = np.mean(np.diff(mag.timebase))
    ia_cur, mdd_cur = ext.filter_by_kappa_cutoff(z, ave_kappa_cutoff = filter_cutoff, ax = None,
                                                 cutoff_by = cutoff_by, filter_item = filter_item)

    ia = np.array(ia_cur)
    mdd = mdd_cur

    divisor = np.sum(np.abs(mdd['mirnov_data']), axis=1)
    mdd['mirnov_data_backup'] = copy.deepcopy(mdd['mirnov_data'])
    mdd['mirnov_data'] = copy.deepcopy(mdd['mirnov_data_backup'])
    mdd['mirnov_data'] = np.abs(mdd['mirnov_data'] / divisor[:, np.newaxis])

    feat_obj = clust.feature_object(instance_array=ia, instance_array_amps=+mdd['mirnov_data'],
                                    misc_data_dict=mdd)
    dms = {'n_clusters': 16, 'n_iterations': 20,
                           'start': 'k_means', 'verbose': 0, 'method': 'EM_VMM'}
    dms = {'n_clusters': 12, 'sin_cos': 0,
                           'verbose': 0, 'method': 'k_means'}
    z = feat_obj.cluster(amplitude=True, **dms)

    z.plot_VM_distributions()

    z.plot_clusters_amp_lines()

    assign = z.cluster_assignments

    fig, ax = z.plot_time_freq_all_clusters()
    fig2, ax2 = plt.subplots(ncols=2, sharex=True, sharey=True)
    sig = mag_red.signal
    timebase = mag_red.timebase
    dt = np.mean(np.diff(timebase))
    tmp_sig = sig[3, :]
    for i in ax.flatten():
        im = i.specgram(tmp_sig, NFFT=1024, Fs=1. / dt, noverlap=128, xextent=[timebase[0], timebase[-1]],
                        cmap='viridis', zorder=-1)
        im[-1].set_clim([-80, -40])
    for i in np.atleast_1d(ax2).flatten():
        im = i.specgram(tmp_sig, NFFT=1024, Fs=1. / dt, noverlap=128, xextent=[timebase[0], timebase[-1]],
                        cmap='viridis', zorder=-1)
        im[-1].set_clim([-80, -40])

    plot_colors = {}
    for i in np.unique(assign):
        mask = (assign == i)
        if np.sum(mask) > 1:
            if i not in plot_colors:
                markersize = 5
                pl = ax2[0].plot(z.feature_obj.misc_data_dict['time'][mask], z.feature_obj.misc_data_dict['freq'][mask],
                                 'o', markersize=markersize)
    fig2.canvas.draw()
    fig2.show()
    fig.canvas.draw()
    fig.show()
