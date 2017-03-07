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


def plot_diagnostics(A):
    # Will be used to plot amplitude vs. position and amplitude vs. phase.
    # For shot 159243, one time of interest is about 791 ms (101.1 kHz ECE Freq)
    t0 = 791
    rel_data = A.results[0][1]["mirnov_data"]
    times = A.results[0][1]["time"]
    # Closest index and time in the mirnov data set (as defined by good_indices in Analysis...)
    n, t = jt.find_closest(times,t0)

    # Closest index and time in the raw data set
    dev = pf.getDevice("DIIID")
    mag = dev.acq.getdata(159243, "DIIID_toroidal_mag").reduce_time([300,1400])
    npr, tpr = jt.find_closest(mag.timebase.tolist(), t0)

    rel_data_angles = np.angle(rel_data)
    #diff_angles = (np.diff(rel_data_angles)) % (2. * np.pi)
    #diff_angles[diff_angles > np.pi] -= (2. * np.pi)
    # positions in degrees
    positions = [20., 67., 97., 127., 132., 137., 157., 200., 247., 277., 307., 312., 322., 340.]
    phases = rel_data_angles[n].tolist()
    amps = [ ]
    for prb in mag.signal:
        amps.append(prb[npr])

    plt.plot(positions,amps,"r")
    plt.xlabel("Position ($^\circ$)")
    plt.ylabel("Amplitude")
    plt.grid()
    plt.show()
    plt.plot(phases,amps,"b")
    plt.xlabel("Phase")
    plt.ylabel("Amplitude")
    plt.grid()
    plt.show()
    return


if __name__ == '__main__':
    # First we try looking at only one shot at a time.
    A1 = Analysis(shots=159243,time_windows=[300,1400],device="DIIID",probes="DIIID_toroidal_mag")
    A1.run_analysis()
    plot_diagnostics(A1)
