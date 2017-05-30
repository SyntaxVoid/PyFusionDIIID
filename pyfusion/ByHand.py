# John Gresl
# Script for checking how a human would normally identify clusters by hand

import matplotlib.pyplot as plt
import numpy as np
from Analysis import *
pi = np.pi


def plot_clusters(A, clust_arr, ax=None, doplot=True, dosave=None):
    # Inputs:
    #   A: Result from Analysis class (A.run_analysis() must have already been run.
    #   clust_arr: Array of the clusters we want to plot. eg: [1,4,6] will plot clusters 1,4 and 6
    #   ax: if ax is supplied, will plot it on the specified axes
    # Outputs:
    #   A graph.
    if clust_arr == "all":
        clust_arr = np.unique(A.z.cluster_assignments)
    class CycledList:
        def __init__(self, arr):
            self.arr = arr
            return
        def __getitem__(self, key):
            return self.arr[np.mod(key, len(self.arr))]

    plot_colors = CycledList(["silver", "darkorchid", "royalblue", "red", "chartreuse", "gold", "olivedrab",
                              "mediumspringgreen", "lightseagreen", "darkcyan", "deepskyblue",
                              "c", "sienna","m", "mediumvioletred", "lightsalmon"])
    if ax is None:
        plt.figure(figsize=(11,8.5), dpi=100, facecolor="w", edgecolor="k")
        plt.specgram(A.results[0][2][0, :], NFFT=1024, Fs=1./np.mean(np.diff(A.results[0][3])),
                     noverlap=128, xextent=[A.results[0][3][0], A.results[0][3][-1]])
        for cl in clust_arr:
            mask = (A.z.cluster_assignments==cl)
            plt.plot(A.z.feature_obj.misc_data_dict["time"][mask],
                     A.z.feature_obj.misc_data_dict["freq"][mask],
                     color=plot_colors[cl], marker="o", linestyle="None",
                     markersize=A.markersize)
        # Cause I'm lazy.
        if dosave is not None and "toroidal" in dosave.lower():
            plt.title("Shot 159243 Toroidal Array")
        if dosave is not None and "poloidal" in dosave.lower():
            plt.title("Shot 159243 Poloidal Array")
        plt.xlabel("Time (ms)")
        plt.ylabel("Freq (kHz)")
        plt.xlim([750,850])
        plt.ylim([45,250])
        if doplot:
            plt.show()
        if dosave is not None:
            plt.savefig(dosave)
    else:
        ax.specgram(A.results[0][2][0, :], NFFT=1024, Fs=1. / np.mean(np.diff(A.results[0][3])),
                     noverlap=128, xextent=[A.results[0][3][0], A.results[0][3][-1]])
        for cl in clust_arr:
            mask = (A.z.cluster_assignments == cl)
            ax.plot(A.z.feature_obj.misc_data_dict["time"][mask],
                     A.z.feature_obj.misc_data_dict["freq"][mask],
                     color=plot_colors[cl], marker="o", linestyle="None",
                     markersize=A.markersize)
    return


def plot_diagnostics(A, time_window, t0, f0, idx="", doplot=True, dosave=None, clustarr=None):
    # Will be used to plot amplitude vs. position and amplitude vs. phase.
    fft = A.raw_fft
    raw_mirnov = fft.signal
    raw_times = fft.timebase
    raw_freqs = fft.frequency_base

    nt, t_actual = jt.find_closest(raw_times, t0)
    nf, f_actual = jt.find_closest(raw_freqs, f0)
    print("Requested t={}ms. Got t={}ms. dt={}ms".format(t0, t_actual, abs(t0-t_actual)))
    print("Requested f={}kHz. Got f={}kHz. df={}kHz".format(f0, f_actual, abs(f0-f_actual)))

    complex_amps = []
    tmp = raw_mirnov[nt]
    for prb in tmp:
        complex_amps.append(prb[nf])
    amps = jt.complex_mag_list(complex_amps)
    phases = np.angle(complex_amps)
    positions = []
    if idx.lower() == "tor":
        positions = [20., 67., 97., 127., 132., 137., 157., 200., 247., 277., 307., 312., 322., 340.]
    elif idx.lower() == "pol":
        positions = [000.0, 018.4, 036.0, 048.7, 059.2, 069.6, 078.0, 085.1, 093.4, 100.7, 107.7,
                     114.9, 121.0, 129.2, 143.6, 165.3, 180.1, 195.0, 216.3, 230.8, 238.9, 244.9,
                     253.5, 262.1, 271.1, 279.5, 290.6, 300.6, 311.8, 324.2, 341.9]
    elif idx.lower() == "ece3":
        positions = [36*0,36*1,36*2,36*3,36*4,36*5,36*6,36*7,36*8,36*9]
    tmp = A.results[0]
    time_base = tmp[3]
    sig = tmp[2]
    dt = np.mean(np.diff(time_base))
    tmp_sig = sig[0, :]

    plt.figure(num=None, figsize=(11, 8.5), dpi=100, facecolor="w", edgecolor="k")
    mpl.rcParams['mathtext.fontset'] = 'stix'
    mpl.rcParams['font.family'] = 'STIXGeneral'
    mpl.pyplot.title(r'ABC123 vs $\mathrm{ABC123}^{123}$')
    ax1 = plt.subplot2grid((2, 3), (0, 0))
    ax2 = plt.subplot2grid((2, 3), (1, 0))
    ax3 = plt.subplot2grid((2, 3), (0, 1), rowspan=2, colspan=2)

    ax1.plot(positions, amps, "k*-", linewidth=2)
    ax1.set_xlabel("Probe Positions ($^\circ$)", fontsize=16)
    ax1.set_ylabel("Amplitudes", fontsize=16)
    ax1.set_xticks(np.arange(0, 360+1, 60))
    ax1.set_xlim([0, 360])
    ax1.grid()

    ax2.plot(positions, phases, "k*-", linewidth=2)
    ax2.set_xlabel("Probe Positions ($^\circ$)", fontsize=16)
    ax2.set_ylabel("Phase", fontsize=16)
    ax2.set_xlim([0, 360])
    ax2.set_xticks(np.arange(0, 360+1, 60))
    ax2.set_yticks([-pi, -3*pi/4, -pi/2, -pi/4, 0, pi/4, pi/2, 3*pi/4, pi])
    ax2.set_yticklabels(["$-\pi$", r"$-\frac{3\pi}{4}$", r"$-\frac{\pi}{2}$", r"$-\frac{\pi}{4}$", "$0$",
                         r"$\frac{\pi}{2}$", r"$\pi$", r"$\frac{3\pi}{2}$", r"$\pi$"])
    ax2.set_ylim([-pi, pi])
    ax2.grid()

    mask1 = (A.z.cluster_assignments == 1)
    mask2 = (A.z.cluster_assignments == 2)
    mask3 = (A.z.cluster_assignments == 3)

    ax3.specgram(tmp_sig, NFFT=1024, Fs=1. / dt,
                 noverlap=128, xextent=[time_base[0], time_base[-1]])
    if idx.lower() == "tor":
        plot_clusters(A,[1, 2, 3], ax3)
        # ax3.plot(A.z.feature_obj.misc_data_dict["time"][mask1],
        #          A.z.feature_obj.misc_data_dict["freq"][mask1],
        #          "ro", markersize=A.markersize)
        # ax3.plot(A.z.feature_obj.misc_data_dict["time"][mask2],
        #          A.z.feature_obj.misc_data_dict["freq"][mask2],
        #          "go", markersize=A.markersize)
        # ax3.plot(A.z.feature_obj.misc_data_dict["time"][mask3],
        #          A.z.feature_obj.misc_data_dict["freq"][mask3],
        #          "co", markersize=A.markersize)
    if idx.lower() == "ece3":
        plot_clusters(A, "all", ax3)
    elif idx.lower() == "pol":
        pass
    ax3.set_xlabel("Time (ms)", fontsize=16)
    ax3.set_ylabel("Freq (kHz)", fontsize=16)

    ax3.plot([t0, t0], [45, 250], "k")
    ax3.plot(time_window, [f0, f0], "k")
    ax3.set_xlim(time_window)
    ax3.set_ylim([45, 250])

    plt.suptitle("Shot 159243 ({}) at t = {} ms, f = {} kHz".format(idx, t_actual, f_actual), fontsize=24)
    plt.subplots_adjust(wspace=0.4)
    if doplot:
        plt.show()
    if dosave is not None:
        plt.savefig(dosave)
    return

def avg_amplitude(A, time_window, t, f, idx="", doplot=True, dosave=None, clustarr=None):
    fft = A.raw_fft
    raw_mirnov = fft.signal
    raw_times = fft.timebase
    raw_freqs = fft.frequency_base
    start = 1
    all_amps = [ ]
    for t0,f0 in zip(t,f):
        nt, t_actual = jt.find_closest(raw_times, t0)
        nf, f_actual = jt.find_closest(raw_freqs, f0)
        print("Requested t={}ms. Got t={}ms. dt={}ms".format(t0, t_actual, abs(t0 - t_actual)))
        print("Requested f={}kHz. Got f={}kHz. df={}kHz".format(f0, f_actual, abs(f0 - f_actual)))

        complex_amps = []
        tmp = raw_mirnov[nt]
        for prb in tmp:
            complex_amps.append(prb[nf])
        amps = jt.complex_mag_list(complex_amps)
        amps = np.array(amps)
        all_amps.append(amps)
    # print(all_amps)
    amps_average = sum(all_amps) / len(t)
    positions = []
    if idx.lower() == "tor":
        positions = [20., 67., 97., 127., 132., 137., 157., 200., 247., 277., 307., 312., 322., 340.]
    elif idx.lower() == "pol":
        positions = [000.0, 018.4, 036.0, 048.7, 059.2, 069.6, 078.0, 085.1, 093.4, 100.7, 107.7,
                     114.9, 121.0, 129.2, 143.6, 165.3, 180.1, 195.0, 216.3, 230.8, 238.9, 244.9,
                     253.5, 262.1, 271.1, 279.5, 290.6, 300.6, 311.8, 324.2, 341.9]
    elif idx.lower() == "ece3":
        positions = [36 * 0, 36 * 1, 36 * 2, 36 * 3, 36 * 4, 36 * 5, 36 * 6, 36 * 7, 36 * 8, 36 * 9]
    tmp = A.results[0]
    time_base = tmp[3]
    sig = tmp[2]
    dt = np.mean(np.diff(time_base))
    tmp_sig = sig[0, :]

    plt.figure(num=None, figsize=(11, 8.5), dpi=100, facecolor="w", edgecolor="k")
    ax1 = plt.gca()
    mpl.rcParams['mathtext.fontset'] = 'stix'
    mpl.rcParams['font.family'] = 'STIXGeneral'
    for amp in all_amps:
        ax1.plot(positions,amp, "k-", linewidth = 0.1)
    ax1.plot(positions, amps_average, "k*-", linewidth=3)
    ax1.set_xlabel("Probe Positions ($^\circ$)", fontsize=16)
    ax1.set_ylabel("Amplitudes", fontsize=16)
    ax1.set_xticks(np.arange(0, 360 + 1, 60))
    ax1.set_xlim([0, 360])
    ax1.grid()

    if doplot:
        plt.show()
    if dosave is not None:
        plt.savefig(dosave)
    return


def plot_ece_signals(A, n):
    x = A.mag.timebase
    y = []
    f, ax = plt.subplots(n,sharex=True)
    for i in range(n):
        y = A.mag.signal[i]
        ax[i].plot(x,y)
    plt.show()
    return


if __name__ == '__main__':

    dms_tor = {'n_clusters': 16, 'n_iterations': 20, 'start': 'k_means',
               'verbose': 0, 'method': 'EM_VMM', "seeds": [732]}
    dms_pol = {'n_clusters': 16, 'n_iterations': 20, 'start': 'k_means',
               'verbose': 0, 'method': 'EM_VMM', "seeds": [2321]}
    #Ator = Analysis(shots=159243, time_windows=[750, 850], probes="DIIID_toroidal_mag",
    #                n_cpus=1, markersize=8, datamining_settings=dms_tor)
    Apol = Analysis(shots=159243, time_windows=[750, 850], probes="DIIID_poloidal322_mag",
                    n_cpus=1, markersize=8, datamining_settings=dms_pol)
    #Ator.run_analysis()
    Apol.run_analysis()

    # Cluster 1
    times1 = [805.807, 805.295, 810.415]
    freqs1 = [70.8, 70.3125, 71.78]
    # Cluster 2
    times2 = [791.471, 793.007, 788.399]
    freqs2 = [87.4, 89.844, 92.773]
    # Cluster 3
    times3 = [801.711, 806.318, 797.615, 809.39]
    freqs3 = [85.938, 90.820, 82.0311, 89.84]

    TIMES = times1+times2+times3
    FREQS = freqs1+freqs2+freqs3

    ## Plot the first 3 clusters in a specgram
    clusts = [3,7,12]
    plot_clusters(Apol,clusts)

    ## Make plots for the first 3 clusters
    for cluster in clusts:
        mask = (Apol.z.cluster_assignments == cluster)
        times = Apol.z.feature_obj.misc_data_dict["time"][mask]
        freqs = Apol.z.feature_obj.misc_data_dict["freq"][mask]
        avg_amplitude(Apol, [750, 850], times, freqs, "pol")

    #avg_amplitude(Apol, [750, 850], TIMES, FREQS, "pol")


    #plot_clusters(Ator,[],doplot=False,dosave="../Plots/Shot159243Toroidal")
    # plot_clusters(Apol,[],doplot=False,dosave="../Plots/Shot159243Poloidal")
    # tor_save_name = "../Plots/Shot159243_Tor_{}_{}.png"
    # pol_save_name = "../Plots/Shot159243_Pol_{}_{}.png"
    # for (t, f) in zip(TIMES, FREQS):
    #     tor_file = tor_save_name.format(t, f)
    #     pol_file = pol_save_name.format(t, f)
    #     plot_diagnostics(Ator, [750, 850], t, f, "Tor", doplot=False, dosave=tor_file)
    #     plot_diagnostics(Apol, [750, 850], t, f, "Pol", doplot=False, dosave=pol_file)

    ## I want to create an "average" plot of amplitudes for many times and frequencies.

    # ECE datamining settings
    # dms = {'n_clusters': 16, 'method': 'EM_GMM'}
    # Aece = Analysis(shots=159243, time_windows=[750,850],probes="ECE_array3",
    #                 n_cpus=1,markersize=8, datamining_settings = dms)
    # Aece.run_analysis_ece()
    # plot_diagnostics(Aece,time_window=[750,850],t0=790,f0=120,idx="ece3")

    #times_ece = [795.06, 791.985, 751.025]
    #freqs_ece = [122.5586, 101.0742, 101.0742]
    #for (t,f) in zip(times_ece, freqs_ece):
    #    imag = "..Plots/Shot159243_ECE3_{}_{}.png".format(t,f)
    #    plot_diagnostics(Aece,[750,850],t,f,"ECE3",doplot=False,dosave=imag)


    #plot_clusters(Aece,clust_arr="all")


    #plot_ece_signals(Aece,1)
