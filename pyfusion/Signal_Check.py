from multiprocessing import Pool
import pyfusion as pf
import numpy as np
import copy, os, time, itertools
import matplotlib.pyplot as plt
import cPickle as pickle
import pyfusion.clustering as clust
import pyfusion.clustering.extract_features_scans as ext




def run(shot,time_window):
    dev = pf.getDevice("DIIID")
    mag = dev.acq.getdata(shot,"DIIID_toroidal_mag")
    mag = mag.reduce_time(time_window)
    n_signals = len(mag.channels)
    print("{} Signals".format(n_signals))
    time = mag.timebase.tolist()

    nrows=4
    ncols=4
    fig,ax=plt.subplots(nrows=nrows,ncols=ncols,sharex=True,sharey=True)
    axf = ax.flatten()
    plt.grid()
    for n,cur_ax in enumerate(axf):
        sig = mag.signal[n].tolist()
        name = mag.channels[n].name
        im = cur_ax.plot(time,sig)
        cur_ax.text((time_window[1]+time_window[0])/2.3,400,name,fontsize=20)
    fig.canvas.draw()
    fig.show()


if __name__ == '__main__':
    shot = 157399
    time_window = [3000,3200]
    run(shot,time_window)