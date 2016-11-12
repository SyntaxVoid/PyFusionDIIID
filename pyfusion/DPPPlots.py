# DPPPlots.py
# Main running script for obtaining data
# Last edited by John Gresl Oct 2 2016
import copy
from multiprocessing import Pool

import itertools
import numpy as np
from matplotlib import pyplot as plt

import DIIID_Retrieval as D3DR
import pyfusion.clustering as clust


def run():
    verbose = True
    #shots = [159243,159244,159245,159246]
    shots = [159243]
    time_window = D3DR.DEFAULT_TIME_WINDOW
    nrows = 2
    ncols = 2
    figure, axes = plt.subplots(nrows=nrows, ncols=ncols, sharex=True, sharey=True)
    axf = axes.flatten()
    rep = itertools.repeat
    input_data_iter = itertools.izip(shots, rep(time_window))
    n_cpus = 4
    wrapper = D3DR.get_stft_wrapper
    if n_cpus > 1:
        pool = Pool(processes=n_cpus, maxtasksperchild=3)
        D3DR.print_if_true(verbose, "Creating pool map. . .")
        results = pool.map(wrapper, input_data_iter)
        D3DR.print_if_true(verbose, "Waiting for pool to close. . .")
        pool.close()
        D3DR.print_if_true(verbose, "Joining pool. . .")
        pool.join()
        D3DR.print_if_true(verbose, "Pool finished. . .")
    else:
        results = map(wrapper, input_data_iter)
    start = 1
    for i, tmp in enumerate(results):
        D3DR.print_if_true(verbose, "Result {:2d}".format(i))
        if tmp[0] is not None:
            if start == 1:
                instance_array = copy.deepcopy(tmp[0])
                misc_data_dict = copy.deepcopy(tmp[1])
                start = 0
            else:
                instance_array = np.append(instance_array, tmp[0], axis=0)
                for j in misc_data_dict.keys():
                    misc_data_dict[j] = np.append(misc_data_dict[j], tmp[1][j], axis=0)
        else:
            print("One shot may have failed. . .")
    feat_obj = clust.feature_object(instance_array=instance_array,
                                    instance_array_amps=+misc_data_dict["mirnov_data"],
                                    misc_data_dict=misc_data_dict)
    datamining_settings = {'n_clusters': 10, 'n_iterations': 20,
                           'start': 'k_means', 'verbose': 0, 'method': 'EM_VMM'}
    z = feat_obj.cluster(**datamining_settings)
    z.plot_VM_distributions()
    z.plot_dimension_histograms()
    dims = [[i, i+1] for i in range(13)]
    z.plot_phase_vs_phase(compare_dimensions=dims)
    z.plot_cumulative_phases()

    figure1, axes1 = plt.subplots(nrows=nrows, ncols=ncols, sharex=True, sharey=True)
    axf1 = axes1.flatten()
    figure2, axes2 = plt.subplots(nrows=nrows, ncols=ncols, sharex=True, sharey=True)
    axf2 = axes2.flatten()
    plot_colors = {}

    for cur_ax1, cur_ax2, shot, tmp in zip(axf1, axf2, shots, results):
        assign = z.cluster_assignments
        details = z.cluster_details["EM_VMM_kappas"]
        shot_details = z.feature_obj.misc_data_dict["shot"]
        timebase = tmp[3]
        sig = tmp[2]
        dt = np.mean(np.diff(timebase))
        tmp_sig = sig[0, :]
        im1 = cur_ax1.specgram(tmp_sig, NFFT=D3DR.SAMPLES, Fs=1./dt, noverlap=128, xextent=[timebase[0], timebase[-1]])
        im2 = cur_ax2.specgram(tmp_sig, NFFT=D3DR.SAMPLES, Fs=1./dt, noverlap=128, xextent=[timebase[0], timebase[-1]])
        for i in np.unique(assign):
            mask = (assign == i) * (shot_details == shot)
            if np.sum(mask) > 1 and np.mean(details[i, :]) > 5:
                if i not in plot_colors:
                    markersize = 5
                    pl = cur_ax1.plot(z.feature_obj.misc_data_dict["time"][mask],
                                      z.feature_obj.misc_data_dict["freq"][mask],
                                      "o", markersize=markersize)
                    plot_colors[i] = pl[0].get_color()
                else:
                    pl = cur_ax1.plot(z.feature_obj.misc_data_dict['time'][mask],
                                      z.feature_obj.misc_data_dict['freq'][mask],
                                      "o", markersize=markersize, color=plot_colors[i])
    #axf1[0].set_xlim(time_window)
    #axf2[0].set_xlim(time_window)
    print("Changing SpecGram limits here")
    axf1[0].set_xlim([400,700])
    axf2[0].set_xlim([400,700])
    axf1[0].set_ylim([50,150])
    axf2[0].set_ylim([50,150])
    figure1.subplots_adjust(bottom=0.02, left=0.02, right=0.95, top=0.95, wspace=0.01, hspace=0.01)
    figure2.subplots_adjust(bottom=0.02, left=0.02, right=0.95, top=0.95, wspace=0.01, hspace=0.01)
    figure1.canvas.draw()
    figure2.canvas.draw()
    plt.show()
    return


if __name__ == "__main__":
    run()

