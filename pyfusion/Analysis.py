##
# John Gresl -- Feb 19 2017
##
import copy, itertools
from multiprocessing import Pool
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import pyfusion as pf
import pyfusion.clustering as clust
import pyfusion.clustering.extract_features_scans as ext
import jtools as jt

def stft_pickle_workaround(input_data):
    return copy.deepcopy(input_data[0].get_stft(input_data[1]))

class Analysis:
    def __init__(self, shots, time_windows=None, device = "DIIID", probes = "DIIID_toroidal_mag",
                 samples=1024, overlap=4, cutoffs=None, datamining_settings=None,
                 n_cpus = 4):
        # Put in description and example run of this... #

        self.shots = shots if type(shots) is list else [shots]
        # Ensuring time_windows is the proper shape to guarantee consistent behaviour.
        if time_windows is None: # We fill time_windows with copies of our default time window
            time_windows = [ ]
            for n in range(len(self.shots)):
                time_windows.append([300,2300])
        else:
            if type(time_windows[0]) is not list:
                # Then time_windows looks like [300,2300] but it must look like [[300,2300],[300,2300],...]
                tmp = [ ]
                for n in range(len(self.shots)):
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
            {"min_svs": 2, "power_cutoff": 0.000, "lower_freq": 0, "uppder_freq": 200000}
        self.datamining_settings = datamining_settings if cutoffs is not None else \
            {'n_clusters': 16, 'n_iterations': 20, 'start': 'k_means', 'verbose': 0, 'method': 'EM_VMM'}
        self.n_cpus = n_cpus
        return

    def get_mags(self,shot,probes):
        dev = pf.getDevice(self.device)
        time_window = self.time_windows[self.shots.index(shot)]
        mag = dev.acq.getdata(shot,probes).reduce_time(time_window)
        return mag

    def get_stft(self,shot):
        mag = self.get_mags(shot,self.probes)
        data_fft = mag.generate_frequency_series(self.samples, self.samples/self.overlap)
        ## SETTINGS ##
        n_pts = 10
        lower_freq = 1
        upper_freq = 500000
        cutoff_by = "sigma_eq"
        filter_cutoff = 75
        filter_item = "EM_VMM_kappas"
        ##/SETTINGS ##
        good_indices = ext.find_peaks(data_fft, n_pts=n_pts, lower_freq=lower_freq, upper_freq=upper_freq)
        rel_data = ext.return_values(data_fft.signal, good_indices)
        misc_data_dict = {}
        misc_data_dict["time"] = ext.return_time_values(data_fft.timebase, good_indices)
        misc_data_dict["freq"] = ext.return_non_freq_dependent(data_fft.frequency_base, good_indices)
        misc_data_dict["shot"] = np.ones(len(misc_data_dict["freq"]), dtype=int)*shot
        misc_data_dict["mirnov_data"] = +rel_data
        rel_data_angles = np.angle(rel_data)
        diff_angles = (np.diff(rel_data_angles))%(2.*np.pi)
        diff_angles[diff_angles > np.pi] -= (2.*np.pi)
        z = ext.perform_data_datamining(diff_angles, misc_data_dict, self.datamining_settings)
        instance_array_cur, misc_data_dict_cur = \
            ext.filter_by_kappa_cutoff(z, ave_kappa_cutoff=filter_cutoff, ax=None,
                                       cutoff_by=cutoff_by, filter_item=filter_item)
        instance_array = np.array(instance_array_cur)
        misc_data_dict = misc_data_dict_cur
        return instance_array, misc_data_dict, mag.signal, mag.timebase

    def get_stft_wrapper(self,input_data):
        return copy.deepcopy(self.get_stft(input_data[0]))

    def run_analysis(self,method="stft",savefile=None):
        if method == "stft":
            func = stft_pickle_workaround
        #tmp_data_iter = itertools.izip(itertools.repeat(self),itertools.izip(self.shots,self.time_windows))
        tmp_data_iter = itertools.izip(itertools.repeat(self),self.shots,self.time_windows)
        if self.n_cpus > 1:
            pool = Pool(processes = self.n_cpus, maxtasksperchild=3)
            self.results = pool.map(func, tmp_data_iter)
            pool.close()
            pool.join()
        else:
            self.results = map(func, tmp_data_iter)
        start = True
        instance_array = 0
        misc_data_dict = 0
        for n,res in enumerate(self.results):
            if res[0] is not None:
                if start:
                    instance_array = copy.deepcopy(res[0])
                    misc_data_dict = copy.deepcopy(res[1])
                    start = False
                else:
                    instance_array = np.append(instance_array, res[0],axis=0)
                    for i in misc_data_dict.keys():
                        misc_data_dict[i] = np.append(misc_data_dict[i], res[1][i], axis=0)
            else:
                print("One shot may have failed!")
        self.feature_object = clust.feature_object(instance_array=instance_array, misc_data_dict=misc_data_dict,
                                              instance_array_amps = +misc_data_dict["mirnov_data"])
        self.z = self.feature_object.cluster(**self.datamining_settings)
        if savefile is not None:
            self.feature_object.dump_data(savefile)
        return

    def plot_clusters(self):
        mpl.rcParams["axes.linewidth"] = 2.0
        nshots = len(self.shots)
        if nshots > 2:
            nrows,ncols = jt.squareish_grid(nshots,swapxy=True)
            fig, ax = plt.subplots(nrows = nrows, ncols=ncols, sharex=True, sharey=True)
            axf = ax.flatten()
            plt.xlabel("Time (ms)")
            plt.ylabel("Freq (kHz)")
            fig2, ax2 = plt.subplots(nrows=nrows, ncols=ncols, sharex=True, sharey=True)
            axf2 = ax2.flatten()
            plt.xlabel("Time (ms)")
            plt.ylabel("Freq (kHz)")
            plot_colors = {}
            for cur_ax, cur_ax2, shot, tmp in zip(axf, axf2, self.shots, self.results):
                assign = self.z.cluster_assignments
                details = self.z.cluster_details["EM_VMM_kappas"]
                shot_details = self.z.feature_obj.misc_data_dict["shot"]
                time_base = tmp[3]
                sig = tmp[2]
                dt = np.mean(np.diff(time_base))
                tmp_sig = sig[0,:]
                im = cur_ax.specgram(tmp_sig, NFFT=1024, Fs=1./dt, noverlap=128, xextent=[time_base[0], time_base[-1]])
                im = cur_ax2.specgram(tmp_sig, NFFT=1024, Fs=1./dt, noverlap=128, xextent=[time_base[0], time_base[-1]])
                for i in np.unique(assign):
                    mask = (assign == i) * (shot_details == shot)
                    if np.sum(mask) > 1 and np.mean(details[i, :]) > 5:
                        if i not in plot_colors:
                            markersize = 5
                            pl = cur_ax.plot(self.z.feature_obj.misc_data_dict['time'][mask],
                                             self.z.feature_obj.misc_data_dict['freq'][mask], 'o', markersize=markersize)
                            # pl = cur_ax.scatter(z.feature_obj.misc_data_dict['time'][mask], z.feature_obj.misc_data_dict['freq'][mask], alpha=0.3)
                            plot_colors[i] = pl[0].get_color()
                            # plot_colors[i] = (pl.get_facecolor(), pl.get_edgecolor())
                        else:
                            pl = cur_ax.plot(self.z.feature_obj.misc_data_dict['time'][mask],
                                             self.z.feature_obj.misc_data_dict['freq'][mask], 'o', markersize=markersize,
                                             color=plot_colors[i])
        tmp = len(self.time_windows)
        for _ in range(tmp):
            axf[_].set_xlim(self.time_windows[_])
            axf2[_].set_xlim(self.time_windows[_])
            axf[_].set_ylim([0, 250])
            axf2[_].set_ylim([0, 250])
        axf.set_xlabel("Time (ms)")
        axf2.set_xlabel("Time (ms)")
        axf.set_ylabel("Freq (kHz)")
        axf2.set_ylabel("Freq (kHz)")
        fig.subplots_adjust(hspace=0,wspace=0)
        fig2.subplots_adjust(hspace=0,wspace=0)
        fig.canvas.draw()
        fig.show()
        fig2.canvas.draw()
        fig2.show()
        return



if __name__ == '__main__':
    shots = range(159243,159247+1)
    time_windows = [300,1400]
    probes = "DIIID_toroidal_mag"
    A1 = Analysis(shots = shots, time_windows = time_windows, probes = probes, n_cpus = 4)
    A1.run_analysis()
    A1.plot_clusters()
