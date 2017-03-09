# John Gresl
# Script for checking how a human would normally identify clusters by hand
import copy
import itertools
from multiprocessing import Pool
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import pyfusion as pf
import pyfusion.clustering as clust
import pyfusion.clustering.extract_features_scans as ext
import jtools as jt

from Analysis import *


def help_me(A):



    return


def plot_diagnostics(A, time_window, t0):
    # Will be used to plot amplitude vs. position and amplitude vs. phase.
    # For shot 159243, one time of interest is about 791 ms (101.1 kHz ECE Freq)
    rel_data = A.results[0][1]["mirnov_data"]
    times = A.results[0][1]["time"]
    # Closest index and time in the mirnov data set (as defined by good_indices in Analysis...)
    n, t = jt.find_closest(times, t0)

    # Closest index and time in the raw data set
    #dev = pf.getDevice("DIIID")
    #mag = dev.acq.getdata(159243, "DIIID_toroidal_mag").reduce_time(time_window)
    #npr, tpr = jt.find_closest(mag.timebase.tolist(), t0)

    #print(t-tpr)
    rel_data_angles = np.angle(rel_data)
    # diff_angles = (np.diff(rel_data_angles)) % (2. * np.pi)
    # diff_angles[diff_angles > np.pi] -= (2. * np.pi)
    # positions in degrees
    positions = [20., 67., 97., 127., 132., 137., 157., 200., 247., 277., 307., 312., 322., 340.]
    phases = rel_data_angles[n].tolist()

    complex_amps = rel_data[n]
    amps = jt.complex_mag_list(complex_amps)

    d = {"amps":amps,"phases":phases,"positions":positions}
    print("Requested t={}ms. Got t={}ms. dt={}ms.".format(t0,t,abs(t0-t)))
    #jt.print_dict(d,"[~~~]")
    format_str = "{:.14f} {:.14f} {:.14f}"
    # print("Amplitudes     Phases        Positions")
    # for i in range(14):
    #     print(format_str.format(d["amps"][i],d["phases"][i],d["positions"][i]))
    # print("INDEX: {}\nTIME: {}".format(n,t))
    # print("Length of rel_data: {}".format(len(rel_data)))
    # print("Time Verif: {}".format(times[n]))

    tmp = A.results[0]
    # assign = A.z.cluster_assignments
    # details = A.z.cluster_details["EM_VMM_kappas"]
    # shot_details = A.z.feature_obj.misc_data_dict["shot"]
    time_base = tmp[3]
    sig = tmp[2]
    dt = np.mean(np.diff(time_base))
    tmp_sig = sig[0, :]

    ax1 = plt.subplot2grid((2, 3), (0, 0))
    ax2 = plt.subplot2grid((2, 3), (1, 0))
    ax3 = plt.subplot2grid((2, 3), (0, 1), rowspan=2, colspan=2)

    ax1.plot(positions, amps, "k*-", linewidth=2)
    ax1.set_xlabel("Probe Positions ($^\circ$)")
    ax1.set_ylabel("Amplitudes of each probe")
    ax1.set_xlim([0, 360])
    ax1.grid()

    ax2.plot(positions, phases, "k*-", linewidth=2)
    ax2.set_xlabel("Probe Positions ($^\circ$)")
    ax2.set_ylabel("Phase")
    ax2.set_xlim([0, 360])
    ax2.grid()

    ax3.specgram(tmp_sig, NFFT=1024, Fs=1. / dt,
                 noverlap=128, xextent=[time_base[0], time_base[-1]])
    ax3.plot([t0, t0], [45, 250], linewidth=3)
    ax3.set_xlim(time_window)
    ax3.set_ylim([45, 250])

    plt.suptitle("Shot 159243 at t = {} ms".format(t), fontsize=24)
    plt.show()

    return


if __name__ == '__main__':
    # First we try looking at only one shot at a time.
    A = Analysis(shots=159243, time_windows=[750, 850], device="DIIID", probes="DIIID_toroidal_mag",n_cpus=1)
    A.run_analysis()
    rel_data_peaks = A.results[0][1]["mirnov_data"]
    times_peaks = A.results[0][1]["time"]
    rel_data = A.raw_mirnov_data
    time = A.raw_time
    plot_diagnostics(A, [750, 850], 790)
