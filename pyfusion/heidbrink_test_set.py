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
import copy
from multiprocessing import Pool

import itertools
import numpy as np
from matplotlib import pyplot as plt

import DIIID_Retrieval as D3DR
import pyfusion.clustering as clust

def run_multiple(shots,time_windows):
    nrows = int(np.sqrt(len(shots)))
    ncols = int(np.ceil(len(shots) / nrows))
    figure, axes = plt.subplots(nrows=nrows, ncols=ncols, sharex=True, sharey=True)
    axf = axes.flatten()
    input_data_iter = itertools.izip(shots,time_windows)
    n_cpus = 4
    wrapper = D3DR.get_stft_wrapper
    if n_cpus > 1:
        pool = Pool(processes=n_cpus, maxtasksperchild=3)
        results = pool.map(wrapper, input_data_iter)
        pool.close()
        pool.join()
    else:
        results = map(wrapper, input_data_iter)
    start = 1
    for i, tmp in enumerate(results):
        if tmp[0] is not None:
            if start ==1:
                instance_array = copy.deepcopy(tmp[0])
                misc_data_dict = copy.deepcopy(tmp[1])
                start = 0
            else:
                instance_array = np.append(instance_array, tmp[0], axis=0)
                for j in misc_data_dict.keys():
                    misc_data_dict[j] = np.append(misc_data_dict[j], tmp[1][j], axis=0)
        else:
            print("One shot may have failed!")
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




if __name__ == '__main__':
    shots = [153067, 153071, 153072, 152932, 152938, 157399, 157400, 157401, 157402]
    time_windows = [[2800,3000],[2800,3000],[2800,3000],[2500,2700],[3000,3200],
                    [2300,2500],[2300,2500],[2300,2500],[2300,2500]]
    run_multiple(shots,time_windows)