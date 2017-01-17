# John Gresl 1/9/2017
from multiprocessing import Pool
import pyfusion as pf
import numpy as np
import copy, os, time, itertools
import matplotlib.pyplot as plt
import cPickle as pickle
import pyfusion.clustering as clust
import pyfusion.clustering.extract_features_scans as ext
import DIIID_Retrieval as D3DR
import jtools as jt
import collections

def make_data_dict(shot, data_fft, good_indices):
    # Returns an ordered data dictionary with certain parameters. In the future maybe I could generalize this
    # to store arbitrary user defined meta data...
    d = collections.OrderedDict()
    d["time"] = ext.return_time_values(data_fft.timebase, good_indices)
    d["freq"] = ext.return_non_freq_dependent(data_fft.frequency_base, good_indices)
    d["shot"] = np.ones(len(d["freq"]), dtype=int)*shot
    d["mirnov_data"] = ext.return_values(data_fft.signal, good_indices)
    return d


def write_times(shot, data_dict, location):
    # Will write a text file with only the times we are interested in for a given shot.
    # The text file can then be fed to IDL to fetch other meta data.
    do_write = jt.ensure_valid_path(location)
    if not do_write:
        print("Invalid file path... Please start over.")
        return None
    cur_time = None
    times = data_dict["time"]
    with open(location, "w") as text_file:
        text_file.write("# SHOT {}".format(shot))
        for time in times:
            if time != cur_time:
                cur_time = time
                text_file.write("\n"+str(cur_time))
    return


def write_pyfusion_events(shot, data_fft, main_location = "database.txt", write_time_database = False,
                          time_location = "database_times.txt", n_pts = 20, lower_freq = 1, upper_freq = 50000):
    do_write = jt.ensure_valid_path(main_location)
    if not do_write:
        print("Invalid file path... Please start over.")
        return None
    # Look for the peaks in the FFT data (Which are *** probably *** modes).
    # rel_data contains ONLY the peaks as identified within good_indices
    good_indices = ext.find_peaks(data_fft, n_pts = n_pts, lower_freq = lower_freq, upper_freq = upper_freq)
    misc_data_dict = make_data_dict(shot, data_fft, good_indices)
    jt.write_columns(main_location,"# TEST HEADER",misc_data_dict)

    if write_time_database:
        write_times(shot,misc_data_dict,time_location)
    return


def run_fft(shot,time_window=None,samples=1024,overlap=4):
    if time_window is None:
        time_window = [200, 1000]
    dev = pf.getDevice("DIIID")  # Gets the device
    mag = dev.acq.getdata(shot, "DIIID_toroidal_mag")  # Gets tge magnitudes of the different signals
    mag = mag.reduce_time(time_window)  # Reduces mag to only include the time window we're interested in
    data_fft = mag.generate_frequency_series(samples, samples / overlap)
    return data_fft

if __name__ == '__main__':
    shot = 159243
    data_fft = run_fft(shot,time_window = [200,800])
    write_pyfusion_events(shot,data_fft,main_location="../Databases/first_database.txt", write_time_database=True,
                          time_location="../Databases/first_database_times.txt")




