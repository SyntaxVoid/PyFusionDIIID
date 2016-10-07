# DIIID_Retrieval.py
# Auxiliary functions to help obtain data from DIII-D
# Last edited by John Gresl Oct 02 2016

import pyfusion as PF
import pyfusion.clustering.extract_features_scans as ext
import numpy as np
import copy, time

# Global Variables #
DEVICE_NAME = "DIIID"
PROBES = "DIIID_toroidal_mag"
DEFAULT_TIME_WINDOW = [300, 1200]
SAMPLES = 1024
OVERLAP = 4


def print_if_true(condition, msg):
    # Used to save lines in main program.
    # Inputs:
    #   condition: Will print 'msg' if condition is True.
    #   msg: string of message to print.
    if condition:
        print(msg)
    return


def get_shot_data(shot, time_window=None, verbose=False):
    # Inputs:
    #   shot:           Shot Number
    #   probes:     Name of data to fetch defined in pyfusion.cfg. Ex: DIIID_toroidal_mag
    #       (^^^Need a better name^^^)
    #   time_window:    Window of interest in miliseconds
    #   verbose:        If True, will print supplementary information.
    # Outputs:
    #   (**Figure out later**)
    time_window = DEFAULT_TIME_WINDOW if time_window is None else time_window
    start_time = time.time()
    device = PF.getDevice(DEVICE_NAME)
    diagnostics = device.acq.getdata(shot, PROBES)
    print_if_true(verbose, "Data fetch time: {:.2f} seconds".format(time.time() - start_time))
    diagnostics = diagnostics.reduce_time(time_window)
    data = diagnostics.subtract_mean(copy=False).normalise(method='v', seperate=True, copy=True)
    segmented_data = data.segment(SAMPLES, overlap=OVERLAP, datalist=1)
    settings = {"min_svs": 2, "power_cutoff": 0.006, "lower_freq": 0, "upper_freq": 200000}
    misc_data_dict = {"svs": [], "RMS": [], "time": [], "freq": [], "shot": []}
    instance_array_list = []
    for segment_location in range(len(segmented_data)):
        print_if_true(((segment_location % 50) == 0) and verbose,
                      "{} {} of {}".format(shot, segment_location, len(segmented_data)))
        segment = segmented_data[segment_location]
        fs_set = segment.flucstruc()
        valid_fs = []
        for fs in fs_set:
            tmp = all([fs.p > settings['power_cutoff'],
                       len(fs.svs()) >= settings['min_svs'],
                       fs.freq > settings['lower_freq'],
                       fs.freq < settings['upper_freq']])
            if tmp:
                valid_fs.append(fs)
        for fs in valid_fs:
            misc_data_dict['svs'].append(len(fs.svs()))
            misc_data_dict['RMS'].append((np.mean(data.scales**2))**0.5)
            misc_data_dict['time'].append(fs.t0)
            misc_data_dict['freq'].append(fs.freq)
            misc_data_dict['shot'].append(shot)
            phases = np.array([tmp_phase.delta for tmp_phase in fs.dphase])
            phases[np.abs(phases) < 0.001] = 0
            instance_array_list.append(phases)
    for i in misc_data_dict.keys():
        misc_data_dict[i] = np.array(misc_data_dict[i])
    instance_array = np.array(instance_array_list)
    return instance_array, misc_data_dict, diagnostics.signal, diagnostics.timebase


def get_stft(shot, time_window=None, verbose=False):
    time_window = DEFAULT_TIME_WINDOW if time_window is None else time_window
    start_time = time.time()
    device = PF.getDevice(DEVICE_NAME)
    diagnostics = device.acq.getdata(shot,PROBES)
    print_if_true(verbose, "Data fetch time: {:.2f} seconds".format(time.time() - start_time))
    diagnostics = diagnostics.reduce_time(time_window)
    diagnostics_fft = diagnostics.generate_frequency_series(SAMPLES, SAMPLES/OVERLAP)
    '''Parameters'''
    n_pts = 20
    lower_freq = 1
    cutoff_by = "sigma_eq"
    filter_cutoff = 55
    upper_freq = 500000
    filter_item = "EM_VMM_kappas"
    '''End Parameters'''
    good_indices = ext.find_peaks(diagnostics_fft, n_pts=n_pts, lower_freq=lower_freq, upper_freq=upper_freq)
    rel_data = ext.return_values(diagnostics_fft.signal, good_indices)
    misc_data_dict = {"mirnov_data": +rel_data,
                      "time": ext.return_time_values(diagnostics_fft.timebase, good_indices),
                      "freq": ext.return_non_freq_dependent(diagnostics_fft.frequency_base, good_indices),
                      "shot": np.ones(len(ext.return_non_freq_dependent(diagnostics_fft.frequency_base, good_indices)),
                                      dtype=int)*shot}
    rel_data_angles = np.angle(rel_data)
    diff_angles = (np.diff(rel_data_angles)) % (2.*np.pi)
    diff_angles[diff_angles > np.pi] -= (2.*np.pi)
    datamining_settings = {"n_clusters": 16, "n_iterations": 20, "start": "k_means", "verbose": 0, "method": "EM_VMM"}
    z = ext.perform_data_datamining(diff_angles, misc_data_dict, datamining_settings)
    instance_array_cur, misc_data_dict_cur = ext.filter_by_kappa_cutoff(z, ave_kappa_cutoff=filter_cutoff,
                                                                        ax=None, cutoff_by=cutoff_by,
                                                                        filter_item=filter_item)
    instance_array = np.array(instance_array_cur)
    misc_data_dict = misc_data_dict_cur
    return instance_array, misc_data_dict, diagnostics.signal, diagnostics.timebase


def get_shot_data_wrapper(input_data, verbose=False):
    print_if_true(verbose, "In get_shot_data wrapper.")
    return copy.deepcopy(get_shot_data(input_data[0], time_window=input_data[1], verbose=verbose))


def get_stft_wrapper(input_data, verbose=False):
    print_if_true(verbose, "In get_stft wrapper.")
    return copy.deepcopy(get_stft(input_data[0], time_window=input_data[1], verbose=verbose))
