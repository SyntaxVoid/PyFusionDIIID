# John Gresl 1/9/2017
from multiprocessing import Pool
import pyfusion as pf
import numpy as np
import copy, os, time, itertools
import matplotlib.pyplot as plt
import cPickle as pickle
import pyfusion.clustering as clust
import idlsave
import pyfusion.clustering.extract_features_scans as ext
import DIIID_Retrieval as D3DR
import jtools as jt
import collections

def make_data_dict(shot, data_fft, good_indices):
    # Returns an ordered data dictionary with certain parameters. In the future maybe I could generalize this
    # to store arbitrary user defined meta data...
    d = collections.OrderedDict()
    d["shot"] = []
    d["time"] = ext.return_time_values(data_fft.timebase, good_indices)
    d["freq"] = ext.return_non_freq_dependent(data_fft.frequency_base, good_indices)
    d["shot"].extend(np.ones(len(d["freq"]), dtype=int) * shot)
    #d["mirnov_data"] = ext.return_values(data_fft.signal, good_indices)
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

def add_to_database(sav_file,database_path):
    # I dont think I need this yet.
    # Want it to load all of the values stored in the IDL save file and then add any new entries
    # to the database.
    # -> Check if there are any new times to add. Any times that don't have an appropriate value
    # should receive NaN status.
    # -> For any times that do exist, add any new categories and all of their vlaues.
    d = idlsave.read(sav_file).data_dict
    # Field names are stored in: d.dtype.fields.keys() but they are repeated.
    # For instance, if "ip" is a field, "IP" will also be a field.
    fields_in_IDL = d.dtype.fields.keys()
    unique_fields = []
    for f in fields_in_IDL:
        if f.lower() in unique_fields:
            continue
        unique_fields.append(f.lower())
    fields_in_IDL = copy.deepcopy(unique_fields)

    # Go into the database and see what fields already exist
    with open(database_path) as db:
        is_data = False
        previous_line = ""
        while not is_data:
            cur_line = db.readline()
            if cur_line[0] == "#":
                previous_line = cur_line
            else:
                is_data = True
    fields_in_database = previous_line[1:].strip().split()

    # THE IDL save file gives me an array that I can turn into an ordered dict.
    # I would like to combine the IDL save file


    return

def write_pyfusion_events(shot, data_fft, main_location = "database.txt",
                          n_pts = 20, lower_freq = 1, upper_freq = 50000):
    # Look for the peaks in the FFT data (Which are *** probably *** modes).
    # rel_data contains ONLY the peaks as identified within good_indices
    good_indices = ext.find_peaks(data_fft, n_pts = n_pts, lower_freq = lower_freq, upper_freq = upper_freq)
    misc_data_dict = make_data_dict(shot, data_fft, good_indices)
    jt.write_columns(main_location,"# TEST HEADER",misc_data_dict)
    return


def run_fft(shot,time_window=None,samples=1024,overlap=4):
    if time_window is None:
        time_window = [200, 1000]
    dev = pf.getDevice("DIIID")  # Gets the device
    mag = dev.acq.getdata(shot, "DIIID_toroidal_mag")  # Gets tge magnitudes of the different signals
    mag = mag.reduce_time(time_window)  # Reduces mag to only include the time window we're interested in
    data_fft = mag.generate_frequency_series(samples, samples / overlap)
    return data_fft


def make_event_database(shot, data_fft, location = "event_database.txt",
                        n_pts = 20, lower_freq = 1, upper_freq = 50000):
    # Look for the peaks in the FFT data (Which are *** probably *** modes).
    # rel_data contains ONLY the peaks as identified within good_indices
    good_indices = ext.find_peaks(data_fft, n_pts = n_pts, lower_freq = lower_freq, upper_freq = upper_freq)
    misc_data_dict = make_data_dict(shot, data_fft, good_indices)
    jt.write_event_database(location,"# Event Database of Frequency Peaks",misc_data_dict)
    return



if __name__ == '__main__':
    shot = 159243
    time_window = [350,550]
    data_fft = run_fft(shot,time_window = time_window)
    #write_pyfusion_events(shot,data_fft,main_location="../Databases/first_database.txt")
    make_event_database(shot,data_fft,location="../Databases/event_database.txt")
    od = jt.idlsav_to_ordered_dict("../IDL/shot1592243time350to550ms.sav")
    jt.write_master_database("../Databases/shot159243time350to550.txt","# Shot 159243 from 350ms - 550ms",od)
    # Write master database --
    # 1. Make IDL save file
    # 2. Read IDL save file
    # 3. Save as ordered dict, make sure times are unique!!*!!



