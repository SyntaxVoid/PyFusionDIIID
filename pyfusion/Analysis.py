##
# John Gresl -- Feb 19 2017
##
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


def plot_seperate_clusters(A, clust_arr, ax=None, doplot=True, dosave=None):
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


def stft_pickle_workaround(input_data):
    # This looks a little funny. Because of how python treats multiprocessing, any function
    # using mp must be at the highest level (not within a class) to operate correctly.
    return copy.deepcopy(input_data[0].get_stft(input_data[1]))


def stft_ece_pickle_workaround(input_data):
    # This looks a little funny. Because of how python treats multiprocessing, any function
    # using mp must be at the highest level (not within a class) to operate correctly.
    return copy.deepcopy(input_data[0].get_stft_ece(input_data[1]))

class Analysis:
    def __init__(self, shots, time_windows=None, device="DIIID", probes="DIIID_toroidal_mag",
                 samples=1024, overlap=4, cutoffs=None, datamining_settings=None, n_cpus=4, markersize=14):
        # Put in description and example run of this... #
        self.shots = shots if type(shots) is list else [shots]
        # Ensuring time_windows is the proper shape to guarantee consistent behaviour.
        if time_windows is None:  # We fill time_windows with copies of our default time window
            time_windows = []
            for _ in range(len(self.shots)):
                time_windows.append([300, 2300])
        else:
            if type(time_windows[0]) is not list:
                # Then time_windows looks like [300,2300] but it must look like [[300,2300],[300,2300],...]
                tmp = []
                for _ in range(len(self.shots)):
                    tmp.append(time_windows)
                time_windows = copy.deepcopy(tmp)
        self.time_windows = time_windows
        self.input_data_iter = itertools.izip(self.shots, self.time_windows)
        self.device = device
        self.probes = probes
        self.time_windows = time_windows
        self.samples = samples
        self.overlap = overlap
        self.cutoffs = cutoffs if cutoffs is not None else \
            {"min_svs": 2, "power_cutoff": 0.000, "lower_freq": 0.1, "uppder_freq":150}
        self.datamining_settings = datamining_settings if datamining_settings is not None else \
            {'n_clusters': 16, 'n_iterations': 20, 'start': 'k_means', 'verbose': 0, 'method': 'EM_VMM', "seeds":None}
        self.n_cpus = n_cpus
        self.results = None
        self.raw_mirnov_data = None
        self.raw_time = None
        self.feature_object = None
        self.z = None
        self.fig = None
        self.ax = None
        self.axf = None
        self.fig2 = None
        self.ax2 = None
        self.axf2 = None
        self.im = None
        self.pl = None
        self.markersize = markersize
        return

    def get_mags(self, shot, probes):
        dev = pf.getDevice(self.device)
        time_window = self.time_windows[self.shots.index(shot)]
        mag = dev.acq.getdata(shot, probes).reduce_time(time_window)
        return mag

    def get_stft(self, shot):
        mag = self.get_mags(shot, self.probes)
        data_fft = mag.generate_frequency_series(self.samples, self.samples/self.overlap)
        # SETTINGS #
        n_pts = 8
        lower_freq = 45
        upper_freq = 150
        cutoff_by = "sigma_eq"
        filter_cutoff = 85
        filter_item = "EM_VMM_kappas"
        # /SETTINGS #
        good_indices = ext.find_peaks(data_fft, n_pts=n_pts, lower_freq=lower_freq, upper_freq=upper_freq)
        rel_data = ext.return_values(data_fft.signal, good_indices)
        tmp = len(ext.return_non_freq_dependent(data_fft.frequency_base, good_indices))
        misc_data_dict = {"time": ext.return_time_values(data_fft.timebase, good_indices),
                          "freq": ext.return_non_freq_dependent(data_fft.frequency_base, good_indices),
                          "shot": np.ones(tmp, dtype=int)*shot,
                          "mirnov_data": +rel_data}
        print("######################"*50)
        self.raw_fft = data_fft
        self.raw_mirnov_data = data_fft.signal
        self.raw_time = data_fft.timebase
        rel_data_angles = np.angle(rel_data)
        diff_angles = (np.diff(rel_data_angles)) % (2.*np.pi)
        diff_angles[diff_angles > np.pi] -= (2.*np.pi)
        z = ext.perform_data_datamining(diff_angles, misc_data_dict, self.datamining_settings)
        self.temp_z = z
        instance_array_cur, misc_data_dict_cur = \
            ext.filter_by_kappa_cutoff(z, ave_kappa_cutoff=filter_cutoff, ax=None,
                                       cutoff_by=cutoff_by, filter_item=filter_item)
        instance_array = np.array(instance_array_cur)
        misc_data_dict = misc_data_dict_cur
        return instance_array, misc_data_dict, mag.signal, mag.timebase

    def get_stft_wrapper(self, input_data):
        return copy.deepcopy(self.get_stft(input_data[0]))

    def run_analysis(self, method="stft", savefile=None):
        if method == "stft":
            func = stft_pickle_workaround
        else:
            func = None
        # tmp_data_iter = itertools.izip(itertools.repeat(self),itertools.izip(self.shots,self.time_windows))
        tmp_data_iter = itertools.izip(itertools.repeat(self), self.shots, self.time_windows)
        if self.n_cpus > 1:
            pool = Pool(processes=self.n_cpus, maxtasksperchild=3)
            self.results = pool.map(func, tmp_data_iter)
            pool.close()
            pool.join()
        else:
            self.results = map(func, tmp_data_iter)
        start = True
        instance_array = 0
        misc_data_dict = 0
        for n, res in enumerate(self.results):
            if res[0] is not None:
                if start:
                    instance_array = copy.deepcopy(res[0])
                    misc_data_dict = copy.deepcopy(res[1])
                    start = False
                else:
                    instance_array = np.append(instance_array, res[0], axis=0)
                    for i in misc_data_dict.keys():
                        misc_data_dict[i] = np.append(misc_data_dict[i], res[1][i], axis=0)
            else:
                print("One shot may have failed!")
        self.feature_object = clust.feature_object(instance_array=instance_array, misc_data_dict=misc_data_dict,
                                                   instance_array_amps=+misc_data_dict["mirnov_data"])
        self.z = self.feature_object.cluster(**self.datamining_settings)
        if savefile is not None:
            self.feature_object.dump_data(savefile)
        return

    def plot_clusters(self):
        fontsize = 35
        plot_colors = {1: "#ff0000", 2: "#ff9400", 3: "#ffe100", 4: "#bfff00", 5: "#2aff00",
                       6: "#00ffa9", 7: "#00f6ff", 8: "#0090ff", 9: "#0033ff", 10:"#8700ff",
                       11:"#cb00ff", 12:"#ff00f2", 13:"#ff006a"}
        mpl.rcParams["axes.linewidth"] = 4.0
        markersize = self.markersize
        nshots = len(self.shots)
        if nshots > 2:
            nrows, ncols = jt.squareish_grid(nshots, swapxy=True)
            self.fig, self.ax = plt.subplots(nrows=nrows, ncols=ncols, sharex=True, sharey=True)
            self.axf = self.ax.flatten()
            self.fig2, self.ax2 = plt.subplots(nrows=nrows, ncols=ncols, sharex=True, sharey=True)
            self.axf2 = self.ax2.flatten()
            for cur_ax, cur_ax2, shot, tmp in zip(self.axf, self.axf2, self.shots, self.results):
                assign = self.z.cluster_assignments
                details = self.z.cluster_details["EM_VMM_kappas"]
                shot_details = self.z.feature_obj.misc_data_dict["shot"]
                time_base = tmp[3]
                sig = tmp[2]
                dt = np.mean(np.diff(time_base))
                tmp_sig = sig[0, :]
                self.im = cur_ax.specgram(tmp_sig, NFFT=1024, Fs=1./dt,
                                          noverlap=128, xextent=[time_base[0], time_base[-1]])
                self.im = cur_ax2.specgram(tmp_sig, NFFT=1024, Fs=1./dt,
                                           noverlap=128, xextent=[time_base[0], time_base[-1]])
                for i in np.unique(assign):
                    mask = (assign == i) * (shot_details == shot)
                    if np.sum(mask) > 1 and np.mean(details[i, :]) > 5:
                        if i not in plot_colors:
                            self.pl = cur_ax.plot(self.z.feature_obj.misc_data_dict['time'][mask],
                                                  self.z.feature_obj.misc_data_dict['freq'][mask],
                                                  'o', markersize=markersize)
                            plot_colors[i] = self.pl[0].get_color()
                        else:
                            self.pl = cur_ax.plot(self.z.feature_obj.misc_data_dict['time'][mask],
                                                  self.z.feature_obj.misc_data_dict['freq'][mask],
                                                  'o', markersize=markersize, color=plot_colors[i])
            print(plot_colors)
            tmp = len(self.time_windows)
            for _ in range(tmp):
                shot = str(self.shots[_])
                self.axf[_].set_xlim(self.time_windows[_])
                self.axf2[_].set_xlim(self.time_windows[_])
                self.axf[_].set_ylim([0, 250])
                self.axf2[_].set_ylim([0, 250])
                self.axf[_].text(680, 200, shot, bbox=dict(facecolor="green", alpha=0.90), fontsize=fontsize)
                self.axf2[_].text(680, 200, shot, bbox=dict(facecolor="green", alpha=0.90), fontsize=fontsize)
        elif nshots == 1:
            # No subplots. Just a single plot.
            self.fig = plt.figure(1)
            self.fig2 = plt.figure(2)
            assign = self.z.cluster_assignments
            details = self.z.cluster_details["EM_VMM_kappas"]
            shot_details = self.z.feature_obj.misc_data_dict["shot"]
            shot = self.shots[0]
            res = self.results[0]
            time_base = res[3]
            sig = res[2]
            dt = np.mean(np.diff(time_base))
            tmp_sig = sig[0, :]
            plt.figure(1)
            self.im = plt.specgram(tmp_sig, NFFT=1024, Fs=1. / dt,
                                   noverlap=128, xextent=[time_base[0], time_base[-1]])
            plt.figure(2)
            self.im = plt.specgram(tmp_sig, NFFT=1024, Fs=1. / dt,
                                   noverlap=128, xextent=[time_base[0], time_base[-1]])
            for i in np.unique(assign):
                plt.figure(2)
                mask = (assign == i) * (shot_details == shot)
                if np.sum(mask) > 1 and np.mean(details[i, :]) > 5:
                    if i not in plot_colors:
                        self.pl = plt.plot(self.z.feature_obj.misc_data_dict['time'][mask],
                                           self.z.feature_obj.misc_data_dict['freq'][mask],
                                           'o', markersize=markersize)
                        plot_colors[i] = self.pl[0].get_color()
                    else:
                        self.pl = plt.plot(self.z.feature_obj.misc_data_dict['time'][mask],
                                           self.z.feature_obj.misc_data_dict['freq'][mask],
                                           'o', markersize=markersize, color=plot_colors[i])
            plt.figure(1)
            plt.xlim(self.time_windows[0])
            plt.ylim([50, 150])
            # plt.xticks(np.arange(self.time_windows[0][0], self.time_windows[0][1], 5.0))
            plt.yticks(np.arange(50, 150, 5.0))
            x0 = self.time_windows[0][0] + 0.35 * (self.time_windows[0][1] - self.time_windows[0][0])
            y0 = 50 + 0.9*(150-50)
            plt.text(x0, y0, str(shot) + ": " + self.probes, bbox=dict(facecolor="green", alpha=0.9), fontsize=fontsize)
            # plt.plot([790, 790], [50, 150], "black", linewidth=3)
            # plt.plot(self.time_windows[0], [67.9, 67.9], "black", linewidth=3)
            # plt.plot(self.time_windows[0], [79.1, 79.1], "black", linewidth=3)
            # plt.plot(self.time_windows[0], [101.1, 101.1], "black", linewidth=3)
            # plt.plot(self.time_windows[0], [107.4, 107.4], "black", linewidth=3)
            # # plt.plot(self.time_windows[0], [113.3, 113.3], "black", linewidth=3)
            plt.figure(2)
            plt.xlim(self.time_windows[0])
            plt.ylim([50, 150])
            # plt.xticks(np.arange(self.time_windows[0][0], self.time_windows[0][1], 5.0))
            plt.yticks(np.arange(50, 150, 5.0))
            plt.text(x0, y0, str(shot) + ": " + self.probes, bbox=dict(facecolor="green", alpha=0.9), fontsize=fontsize)
            # plt.plot([790, 790], [50, 150], "black", linewidth=3)
            # plt.plot(self.time_windows[0], [67.9, 67.9], "black", linewidth=3)
            # plt.plot(self.time_windows[0], [79.1, 79.1], "black", linewidth=3)
            # plt.plot(self.time_windows[0], [101.1, 101.1], "black", linewidth=3)
            # plt.plot(self.time_windows[0], [107.4, 107.4], "black", linewidth=3)
            # # plt.plot(self.time_windows[0], [113.3, 113.3], "black", linewidth=3)
        self.fig.subplots_adjust(hspace=0, wspace=0)
        self.fig2.subplots_adjust(hspace=0, wspace=0)
        self.fig.text(0.5, 0.065, "Time (ms)", ha="center", fontsize=fontsize-10)
        self.fig.text(0.1, 0.5, "Freq (kHz)", va="center", rotation="vertical", fontsize=fontsize-10)
        self.fig2.text(0.5, 0.065, "Time (ms)", ha="center", fontsize=fontsize-10)
        self.fig2.text(0.1, 0.5, "Freq (kHz)", va="center", rotation="vertical", fontsize=fontsize-10)
        self.fig.canvas.draw()
        self.fig.show()
        self.fig2.canvas.draw()
        self.fig2.show()
        return

    def plot_diagnostics(self, time_window, t0, f0, idx="", doplot=True, dosave=None, clustarr=None):
        # Will be used to plot amplitude vs. position and amplitude vs. phase.
        pi = np.pi
        fft = self.raw_fft
        raw_mirnov = fft.signal
        raw_times = fft.timebase
        raw_freqs = fft.frequency_base

        nt, t_actual = jt.find_closest(raw_times, t0)
        nf, f_actual = jt.find_closest(raw_freqs, f0)
        print("Requested t={}ms. Got t={}ms. dt={}ms".format(t0, t_actual, abs(t0 - t_actual)))
        print("Requested f={}kHz. Got f={}kHz. df={}kHz".format(f0, f_actual, abs(f0 - f_actual)))

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
            positions = [36 * 0, 36 * 1, 36 * 2, 36 * 3, 36 * 4, 36 * 5, 36 * 6, 36 * 7, 36 * 8, 36 * 9]
        tmp = self.results[0]
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
        ax1.set_xticks(np.arange(0, 360 + 1, 60))
        ax1.set_xlim([0, 360])
        ax1.grid()

        ax2.plot(positions, phases, "k*-", linewidth=2)
        ax2.set_xlabel("Probe Positions ($^\circ$)", fontsize=16)
        ax2.set_ylabel("Phase", fontsize=16)
        ax2.set_xlim([0, 360])
        ax2.set_xticks(np.arange(0, 360 + 1, 60))
        ax2.set_yticks([-pi, -3 * pi / 4, -pi / 2, -pi / 4, 0, pi / 4, pi / 2, 3 * pi / 4, pi])
        ax2.set_yticklabels(["$-\pi$", r"$-\frac{3\pi}{4}$", r"$-\frac{\pi}{2}$", r"$-\frac{\pi}{4}$", "$0$",
                             r"$\frac{\pi}{2}$", r"$\pi$", r"$\frac{3\pi}{2}$", r"$\pi$"])
        ax2.set_ylim([-pi, pi])
        ax2.grid()

        mask1 = (self.z.cluster_assignments == 1)
        mask2 = (self.z.cluster_assignments == 2)
        mask3 = (self.z.cluster_assignments == 3)

        ax3.specgram(tmp_sig, NFFT=1024, Fs=1. / dt,
                     noverlap=128, xextent=[time_base[0], time_base[-1]])
        if idx.lower() == "tor":
            plot_seperate_clusters(self, [ ], ax3)
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
            plot_seperate_clusters(self, "all", ax3)
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

    ### ECE ###
    def get_stft_ece(self, shot):
        mag = self.get_mags(shot, self.probes)
        self.mag = mag
        data_fft = mag.generate_frequency_series(self.samples, self.samples / self.overlap)
        # SETTINGS #
        n_pts = 8
        lower_freq = 45
        upper_freq = 150
        cutoff_by = "sigma_eq"
        filter_cutoff = 20
        filter_item = "EM_GMM_variances_sc"
        # /SETTINGS #
        good_indices = ext.find_peaks(data_fft, n_pts=n_pts, lower_freq=lower_freq, upper_freq=upper_freq)
        rel_data = ext.return_values(data_fft.signal, good_indices)
        tmp = len(ext.return_non_freq_dependent(data_fft.frequency_base, good_indices))
        misc_data_dict = {"time": ext.return_time_values(data_fft.timebase, good_indices),
                          "freq": ext.return_non_freq_dependent(data_fft.frequency_base, good_indices),
                          "shot": np.ones(tmp, dtype=int) * shot,
                          "mirnov_data": +rel_data}
        print("######################" * 50)
        self.raw_fft = data_fft
        self.raw_mirnov_data = data_fft.signal
        self.raw_time = data_fft.timebase
        rel_data_angles = np.angle(rel_data)
        diff_angles = (np.diff(rel_data_angles)) % (2. * np.pi)
        diff_angles[diff_angles > np.pi] -= (2. * np.pi)

        diff_amps = np.abs(np.diff(jt.complex_mag_list(rel_data)))

        # This is where ECE is different. Use magnitudes as clustering instead of angles
        z = ext.perform_data_datamining(diff_amps, misc_data_dict, self.datamining_settings)
        self.temp_z = z

        instance_array_cur, misc_data_dict_cur = \
            ext.filter_by_kappa_cutoff(z, ave_kappa_cutoff=filter_cutoff, ax=None,
                                       cutoff_by=cutoff_by, filter_item=filter_item)

        instance_array = np.array(instance_array_cur)
        misc_data_dict = misc_data_dict_cur
        return instance_array, misc_data_dict, mag.signal, mag.timebase

    def get_stft_ece_wrapper(self, input_data):
        return copy.deepcopy(self.get_stft_ece(input_data[0]))

    def run_analysis_ece(self, method="stft", savefile=None):
        if method == "stft":
            func = stft_ece_pickle_workaround
        else:
            func = None
        # tmp_data_iter = itertools.izip(itertools.repeat(self),itertools.izip(self.shots,self.time_windows))
        tmp_data_iter = itertools.izip(itertools.repeat(self), self.shots, self.time_windows)
        if self.n_cpus > 1:
            pool = Pool(processes=self.n_cpus, maxtasksperchild=3)
            self.results = pool.map(func, tmp_data_iter)
            pool.close()
            pool.join()
        else:
            self.results = map(func, tmp_data_iter)
        start = True
        instance_array = 0
        misc_data_dict = 0
        for n, res in enumerate(self.results):
            if res[0] is not None:
                if start:
                    instance_array = copy.deepcopy(res[0])
                    misc_data_dict = copy.deepcopy(res[1])
                    start = False
                else:
                    instance_array = np.append(instance_array, res[0], axis=0)
                    for i in misc_data_dict.keys():
                        misc_data_dict[i] = np.append(misc_data_dict[i], res[1][i], axis=0)
            else:
                print("One shot may have failed!")
        self.feature_object = clust.feature_object(instance_array=instance_array, misc_data_dict=misc_data_dict,
                                                   instance_array_amps=+misc_data_dict["mirnov_data"])
        self.z = self.feature_object.cluster(**self.datamining_settings)
        if savefile is not None:
            self.feature_object.dump_data(savefile)
        return
        ### /ECE ###

if __name__ == '__main__':
    shots = 159243
    time_windows = [750, 850]
    A1 = Analysis(shots=shots, time_windows=time_windows, probes="DIIID_toroidal_mag", markersize=15,
                  datamining_settings= {'n_clusters': 8, 'n_iterations': 20, 'start': 'k_means', 'verbose': 0, 'method': 'EM_VMM',
                   "seeds": None})
    A1.run_analysis()
    A1.plot_clusters()

    #raw_input("Press any key to continue. . .")
    #A2 = Analysis(shots=159243, time_windows=[750, 850], probes="DIIID_poloidal322_mag")
    #A2.run_analysis()
    #A2.plot_clusters()
