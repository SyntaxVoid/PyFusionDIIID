# John Gresl 1/9/2017
from multiprocessing import Pool
import pyfusion as pf
import numpy as np
import copy, os, time, itertools
import matplotlib.pyplot as plt
import cPickle as pickle
import pyfusion.clustering as clust
import pyfusion.clustering.extract_features_scans as ext


def get_single(shot, time_window=None):
    if time_window==None:
        time_window = [2000,5000]
    cache_name = '/u/haskeysr/tmp/{}.pickle'.format(shot)
    start_time = time.time()
    dev = pf.getDevice('DIIID')
    mag = dev.acq.getdata(shot,'DIIID_toroidal_mag')
    print('Data fetch time {:.2f}s'.format(time.time() - start_time))
    mag_red = mag.reduce_time(time_window)
    samples= 1024
    overlap = 4
    data_fft = mag_red.generate_frequency_series(samples, samples/overlap)
    data_diff = np.diff(mag_red.timebase)
    data = mag_red.subtract_mean(copy=False).normalise(method='v',separate=True,copy=True)
    data_segmented = data.segment(samples, overlap = overlap, datalist = 1)
    settings = {'min_svs':2,'power_cutoff':0.006,'lower_freq':4000,'upper_freq':200000}
    settings = {'min_svs':2,'power_cutoff':0.000,'lower_freq':0,'upper_freq':200000}
    misc_data_dict = {'svs':[], 'RMS':[],'time':[],'freq':[],'mirnov_data':[],'shot':[]}
    instance_array_list = []
    for seg_loc in range(len(data_segmented)):
        if ((seg_loc%50)==0):
            print shot, seg_loc, 'of', len(data_segmented)
        data_seg = data_segmented[seg_loc]
        time_seg_average_time = np.mean([data_seg.timebase[0],data_seg.timebase[-1]])
        fs_set = data_seg.flucstruc()
        valid_fs = []
        for fs in fs_set:
            tmp_valid = (fs.p > settings['power_cutoff']) and (len(fs.svs()) >= settings['min_svs']) and (fs.freq>settings['lower_freq']) and (fs.freq<settings['upper_freq'])
            if tmp_valid:
                valid_fs.append(fs)
        for fs in valid_fs:
            #for i in self.fs_values: self.misc_data_dict[i].append(getattr(fs,i))
            misc_data_dict['svs'].append(len(fs.svs()))
            # for i in self.meta_data:
            #     try:
            #         self.misc_data_dict[i].append(copy.deepcopy(self.data.meta[i]))
            #     except KeyError:
            #         self.misc_data_dict[i].append(None)
            misc_data_dict['RMS'].append((np.mean(data.scales**2))**0.5)
            misc_data_dict['time'].append(fs.t0)#time_seg_average_time)
            #misc_data_dict['time'].append(time_seg_average_time)
            misc_data_dict['freq'].append(fs.freq)
            misc_data_dict['shot'].append(shot)
            phases = np.array([tmp_phase.delta for tmp_phase in fs.dphase])
            phases[np.abs(phases)<0.001]=0
            instance_array_list.append(phases)
    for i in misc_data_dict.keys():
        misc_data_dict[i]=np.array(misc_data_dict[i])
    instance_array = np.array(instance_array_list)
    return instance_array, misc_data_dict, mag.signal, mag.timebase



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
    make_db(1,"test_database.txt")

