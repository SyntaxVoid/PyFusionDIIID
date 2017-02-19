

if __name__ == '__main__':
    from multiprocessing import Pool
    import pyfusion as pf
    import numpy as np
    import copy, os, time, itertools
    import matplotlib.pyplot as plt
    import cPickle as pickle
    import pyfusion.clustering as clust
    import pyfusion.clustering.extract_features_scans as ext

    dev = pf.getDevice("DIIID")
    mag = dev.acq.getdata(159243,"DIIID_poloidal322_mag")



