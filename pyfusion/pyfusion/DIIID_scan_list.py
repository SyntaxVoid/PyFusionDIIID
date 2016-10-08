# DIIID_scan_list.py
import numpy as np


def database_of_scans(name):
    # Will return an array of shots based on the given name
    # Current options are:
    #   1. test_shots
    # John Gresl Oct 7 2016
    if name.lower() == "test_shots":
        return np.arange(159243,159250) # TODO: ADD START TIMES AND END TIMES
    print("Name is invalid!")
    return []

def return_scan_details(names):
    out_shot_list = []
    out_start_time = []
    out_end_time = []
    if names.__class__ == str:
        names = [names]
    for name in names:
        shot_list, start_time, end_time = database_of_scans(name)
        out_start_time.extend([start_time] * len(shot_list))
        out_end_time.extend([end_time] * len(shot_list))
        out_shot_list.extend(shot_list)
    return out_shot_list, out_start_time, out_end_time
