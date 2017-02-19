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
    mag = dev.acq.getdata(shot,"DIIID_poloidal322_mag")
    mag = mag.reduce_time(time_window)
    n_signals = len(mag.channels)
    print("{} Signals".format(n_signals))
    time = mag.timebase.tolist()

    nrows=6
    ncols=6
    fig,ax=plt.subplots(nrows=nrows,ncols=ncols,sharex=True,sharey=True)
    axf = ax.flatten()
    fig.suptitle("SHOT {}".format(shot))
    for n,cur_ax in enumerate(axf):
        if n < n_signals:
            sig = mag.signal[n].tolist()
            name = mag.channels[n].name
            cur_ax.grid()
            im = cur_ax.plot(time,sig)
            cur_ax.text((time_window[1]+time_window[0])/2-50,700,name,fontsize=11)
    fig.canvas.draw()
    fig.show()


if __name__ == '__main__':
    shot = 159243
    time_window = [300,1400]
    run(shot,time_window)