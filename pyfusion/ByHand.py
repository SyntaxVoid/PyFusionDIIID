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
pi = np.pi


def plot_diagnostics(A, time_window, t0, f0, id="", doplot=True, dosave=None):
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
    if id.lower() == "tor":
        positions = [20., 67., 97., 127., 132., 137., 157., 200., 247., 277., 307., 312., 322., 340.]
    elif id.lower() == "pol":
        positions = [000.0, 018.4, 036.0, 048.7, 059.2, 069.6, 078.0, 085.1, 093.4, 100.7, 107.7,
                     114.9, 121.0, 129.2, 143.6, 165.3, 180.1, 195.0, 216.3, 230.8, 238.9, 244.9,
                     253.5, 262.1, 271.1, 279.5, 290.6, 300.6, 311.8, 324.2, 341.9]
    tmp = A.results[0]
    time_base = tmp[3]
    sig = tmp[2]
    dt = np.mean(np.diff(time_base))
    tmp_sig = sig[0, :]

    plt.figure(num=None, figsize=(11,8.5), dpi=100, facecolor="w", edgecolor="k")
    mpl.rcParams['mathtext.fontset'] = 'stix'
    mpl.rcParams['font.family'] = 'STIXGeneral'
    mpl.pyplot.title(r'ABC123 vs $\mathrm{ABC123}^{123}$')
    ax1 = plt.subplot2grid((2, 3), (0, 0))
    ax2 = plt.subplot2grid((2, 3), (1, 0))
    ax3 = plt.subplot2grid((2, 3), (0, 1), rowspan=2, colspan=2)

    ax1.plot(positions, amps, "k*-", linewidth=2)
    ax1.set_xlabel("Probe Positions ($^\circ$)", fontsize=16)
    ax1.set_ylabel("Amplitudes", fontsize=16)
    ax1.set_xticks(np.arange(0,360+1,60))
    ax1.set_xlim([0, 360])
    ax1.grid()

    ax2.plot(positions, phases, "k*-", linewidth=2)
    ax2.set_xlabel("Probe Positions ($^\circ$)", fontsize=16)
    ax2.set_ylabel("Phase", fontsize=16)
    ax2.set_xlim([0, 360])
    ax2.set_xticks(np.arange(0, 360 + 1, 60))
    ax2.set_yticks([-pi, -3*pi/4, -pi/2, -pi/4, 0, pi/4, pi/2, 3*pi/4, pi])
    ax2.set_yticklabels(["$-\pi$", r"$-\frac{3\pi}{4}$", r"$-\frac{\pi}{2}$", r"$-\frac{\pi}{4}$", "$0$",
                         r"$\frac{\pi}{2}$", r"$\pi$", r"$\frac{3\pi}{2}$", r"$\pi$"])
    ax2.set_ylim([-pi,pi])
    ax2.grid()

    mask1 = (A.z.cluster_assignments == 1)
    mask2 = (A.z.cluster_assignments == 2)
    mask3 = (A.z.cluster_assignments == 3)

    ax3.specgram(tmp_sig, NFFT=1024, Fs=1. / dt,
                 noverlap=128, xextent=[time_base[0], time_base[-1]])
    ax3.plot(A.z.feature_obj.misc_data_dict["time"][mask1],
             A.z.feature_obj.misc_data_dict["freq"][mask1],
             "ro", markersize=A.markersize)
    ax3.plot(A.z.feature_obj.misc_data_dict["time"][mask2],
             A.z.feature_obj.misc_data_dict["freq"][mask2],
             "go", markersize=A.markersize)
    ax3.plot(A.z.feature_obj.misc_data_dict["time"][mask3],
             A.z.feature_obj.misc_data_dict["freq"][mask3],
             "co", markersize=A.markersize)
    ax3.set_xlabel("Time (ms)", fontsize=16)
    ax3.set_ylabel("Freq (kHz)", fontsize=16)


    ax3.plot([t0, t0], [45, 250], "k")
    ax3.plot(time_window, [f0,f0], "k")
    ax3.set_xlim(time_window)
    ax3.set_ylim([45, 250])

    plt.suptitle("Shot 159243 ({}) at t = {} ms, f = {} kHz".format(id,t,f), fontsize=24)
    plt.subplots_adjust(wspace=0.4)
    fname = "../Plots/Shot159243_{}_{}_{}.png".format(id,t0,f0)
    if doplot:
        plt.show()
    if dosave is not None:
        plt.savefig(dosave)
    return


if __name__ == '__main__':
    dms_tor = {'n_clusters': 16, 'n_iterations': 20, 'start': 'k_means', 'verbose': 0, 'method': 'EM_VMM', "seeds":[732]}
    dms_pol = {'n_clusters': 16, 'n_iterations': 20, 'start': 'k_means', 'verbose': 0, 'method': 'EM_VMM', "seeds":None}
    # Want to compare ~20 different data points from different modes (10 torroidal / 10 poloidal)
    Ator = Analysis(shots=159243, time_windows=[750, 850], probes="DIIID_toroidal_mag",
                    n_cpus=1, markersize=8, datamining_settings=dms_tor)
    Apol = Analysis(shots=159243, time_windows=[750, 850], probes="DIIID_poloidal322_mag",
                    n_cpus=1, markersize=8, datamining_settings = dms_pol)
    Ator.run_analysis()
    Apol.run_analysis()

    mask1 = (Ator.z.cluster_assignments == 1)
    mask2 = (Ator.z.cluster_assignments == 2)
    mask3 = (Ator.z.cluster_assignments == 3)
    cluster1times = Ator.feature_object.misc_data_dict["time"][mask1]
    cluster2times = Ator.feature_object.misc_data_dict["time"][mask2]
    cluster3times = Ator.feature_object.misc_data_dict["time"][mask3]
    cluster1freqs = Ator.feature_object.misc_data_dict["freq"][mask1]
    cluster2freqs = Ator.feature_object.misc_data_dict["freq"][mask2]
    cluster3freqs = Ator.feature_object.misc_data_dict["freq"][mask3]

    # These points were picked by looking at a graph of the clusters
    # Cluster 1
    times1 =  [805.807,805.295,810.415]
    freqs1 =  [70.8, 70.3125, 71.78]
    # Cluster 2
    times2 = [791.471, 793.007, 788.399]
    freqs2 = [87.4, 89.844, 92.773]
    # Cluster 3
    times3 = [801.711, 806.318, 797.615, 809.39]
    freqs3 = [85.938, 90.820, 82.0311, 89.84]

    TIMES = times1+times2+times3
    FREQS = freqs1+freqs2+freqs3

    for (t,f) in zip(TIMES,FREQS):
        plot_diagnostics(Ator,[750,850],t,f,"Tor")
        plot_diagnostics(Apol, [750, 850], t, f, "Pol")





    # A = Analysis(shots=159243, time_windows=[750, 850], device="DIIID", probes="DIIID_toroidal_mag",n_cpus=1)
    # A.run_analysis()
    # times = [790,795,810]
    # freqs = [69.5,93.2,75]
    # for t,f in zip(times,freqs):
    #     plot_diagnostics(A, [750, 850], t, f)

