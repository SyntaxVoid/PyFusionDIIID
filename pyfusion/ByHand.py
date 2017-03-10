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


def plot_diagnostics(A, time_window, t0, f0):
    # Will be used to plot amplitude vs. position and amplitude vs. phase.
    # For shot 159243, one time of interest is about 791 ms (101.1 kHz ECE Freq)
    fft = A.raw_fft
    raw_mirnov = fft.signal
    raw_times = fft.timebase
    raw_freqs = fft.frequency_base

    nt, t = jt.find_closest(raw_times,t0)
    nf, f = jt.find_closest(raw_freqs, f0)
    print("Requested t={}ms. Got t={}ms. dt={}ms".format(t0,t,abs(t0-t)))
    print("Requested f={}kHz. Got f={}kHz. df={}kHz".format(f0, f, abs(f0 - f)))

    complex_amps = []
    tmp = raw_mirnov[nt]
    for prb in tmp:
        complex_amps.append(prb[nf])
    amps = jt.complex_mag_list(complex_amps)
    phases = np.angle(complex_amps)
    # positions in degrees
    positions = [20., 67., 97., 127., 132., 137., 157., 200., 247., 277., 307., 312., 322., 340.]

    tmp = A.results[0]
    assign = A.z.cluster_assignments
    details = A.z.cluster_details["EM_VMM_kappas"]
    shot_details = A.z.feature_obj.misc_data_dict["shot"]
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
    # Plot a small square around the point of interest and zoom in
    ax3.plot([t0, t0], [45, 250], "k")
    ax3.plot(time_window, [f0,f0], "k")
    ax3.set_xlim(time_window)
    ax3.set_ylim([45, 250])

    plt.suptitle("Shot 159243 at t = {} ms, f = {} kHz".format(t,f), fontsize=24)
    #plt.subplot_tool()
    #file_format_str = "../Plots/Shot{}_Time{}_Freq{}.png"
    #plt.savefig(file_format_str.format(A.shots[0],t0,f0))
    plt.show()
    return


if __name__ == '__main__':
    # Want to compare ~20 different data points from different modes (10 torroidal / 10 poloidal)
    Ator = Analysis(shots=159243, time_windows=[750, 850], device="DIIIID", probes="DIIID_toroidal_mag", n_cpus=1)
    Apol = Analysis(shots=159243, time_windows=[750, 850], device="DIIIID", probes="DIIID_poloidal322_mag", n_cpus=1)

    # 10 (time,freq) tuples from clustering. 3 in one cluster, 3 in another and 4 in the final (arbitrary)
    #


    # A = Analysis(shots=159243, time_windows=[750, 850], device="DIIID", probes="DIIID_toroidal_mag",n_cpus=1)
    # A.run_analysis()
    # times = [790,795,810]
    # freqs = [69.5,93.2,75]
    # for t,f in zip(times,freqs):
    #     plot_diagnostics(A, [750, 850], t, f)

