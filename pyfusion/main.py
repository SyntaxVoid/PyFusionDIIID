# main.py
import copy
from multiprocessing import Pool

import itertools
import numpy as np
from matplotlib import pyplot as plt

import DIIID_Retrieval as D3DR
import pyfusion.clustering as clust


# noinspection PyInterpreter,PyInterpreter
def fetch_and_write_interesting_events(shots_and_times,f,n_cpus=1):
    # John Gresl 11/22/2016
    # Input:
    #   shots_and_times is a dictionary with each shot as a key and a time window tuple as the value
    #       ex: shots_and_times = {159243: (300,1500), 154242: (200,1200)}
    # Output:
    #   Writes a text file at location f in the format:
    #   (shot_number): (interesting_times seperated by a comma)

    # Check for input data integrity
    for k,v in shots_and_times.items:
        assert type(k) == int, "Invalid Shot Number: {}".format(k)
        assert v[0] < v[1], "Invalid Time Window for shot {}: ({},{})".format(k, v[0], v[1])
    assert type(f) == str, "Invalid file name. Must be type 'str'. You provided type {}".format(type(f))

    # Find interesting events
    shots = []
    times = []
    for k,v in shots_and_times.items:
        shots.append(k)
        times.append([v[0],v[1]])
    input_data_iter = itertools.izip(shots, times)
    wrapper = D3DR.get_stft_wrapper
    if n_cpus > 1:
        pool = Pool(processes=n_cpus, maxtasksperchild=3)
        results = pool.map(wrapper, input_data_iter)
        pool.close()
        pool.join()
    else:
        results = map(wrapper, input_data_iter)
    start = 1
    for i, tmp in enumerate(results):
        if tmp[0] is not None:
            if start == 1:
                instance_array = copy.deepcopy(tmp[0])
                misc_data_dict = copy.deepcopy(tmp[1])
                start=0
            else:
                instance_array = np.append(instance_array, tmp[0], axis=0)
                for j in misc_data_dict.keys():
                    misc_data_dict[j] = np.append(misc_data_dict[j], tmp[1][j], axis=0)
        else:
            print("*"*35+"\n***One shot may have failed. . .***\n"+"*"*35)
    feat_obj = clust.feature_object(instance_array=instance_array, instance_array_amps=+misc_data_dict["mirnov_data"],
                                    mist_data_dict=misc_data_dict)
    datamining_settings = {'n_clusters': 10, 'n_iterations': 20,
                           'start': 'k_means', 'verbose': 0, 'method': 'EM_VMM'}
    z = feat_obj.cluster(**datamining_settings)
    return



if __name__ == '__main__':
    # Variables I need to define here: shots, time_windows, n_cpus


    pass