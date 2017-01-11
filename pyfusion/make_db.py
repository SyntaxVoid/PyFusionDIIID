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


def write_pyfusion_events(shot,location,time_window = None):
    #
    #
    #
    if time_window is None:
        time_window = [200,1000]
    do_write = jt.ensure_valid_path(location)
    if not do_write:
        print("Invalid file path... Please start over.")
        return None
    dev = pf.getDevice("DIIID")  # Gets the device
    mag = dev.acq.getdata(shot,"DIIID_toroidal_mag") # Gets tge magnitudes of the different signals
    mag = mag.reduce_time(time_window) # Reduces mag to only include the time window we're interested in

    # FFT Settings
    samples = 1024
    overlap = 4
    data_fft = mag.generate_frequency_series(samples, samples/overlap)

    # Other Settings
    n_pts = 20
    lower_freq = 1
    upper_freq = 50000
    cutoff_by = "sigma_eq"
    filter_cutoff = 55
    filter_item = "EM_VMM_kappas"
    datamining_settings = None

    # Look for the peaks in the FFT data (Which are *** probably *** modes).
    # rel_data contains ONLY the peaks as identified within good_indices
    good_indices = ext.find_peaks(data_fft, n_pts = n_pts, lower_freq = lower_freq, upper_freq = upper_freq)
    rel_data = ext.return_values(data_fft.signal, good_indices)

    # Gather some metadata
    misc_data_dict = collections.OrderedDict()
    misc_data_dict["time"] = ext.return_time_values(data_fft.timebase, good_indices)
    misc_data_dict["freq"] = ext.return_non_freq_dependent(data_fft.frequency_base, good_indices)
    misc_data_dict["shot"] = np.ones(len(misc_data_dict["freq"]),dtype=int)*shot

    jt.write_columns(location,"# TEST HEADER",misc_data_dict)





    # Might be useful for later...
    misc_data_dict["mirnov_data"] = +rel_data





    return


def make_db(shot, location, header = ""):

    if os.path.isfile(location):
        # Verify that there is not a database at the location already. If there is,
        # ask the user if they would like to overwrite the file.
        valid_ans = ["y","yes","n","no"]
        ans = raw_input("File already exists at:\n\t{}.\nWould you like to overwrite this file? (y/n)\n".format(location)).lower().strip()
        while ans not in valid_ans:
            ans = raw_input("\"{}\" is not a valid input. Please select a choice from {}. . .\n".format(ans, valid_ans)).lower().strip()
        print(ans)
    with open(location,"w") as database:
        if header == "":
            header = '''# Shot {}\n# START DATA'''.format(shot)
        database.write(header)
        database.write("\ntest111...")
    return

if __name__ == '__main__':
    write_pyfusion_events(159243,"test_database.txt")

