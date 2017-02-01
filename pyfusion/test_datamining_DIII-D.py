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


def get_stft(shot, time_window = None):
    '''STFT-clustering to extract features from a single shot
    '''
    if time_window == None: time_window=[1000,5000]

    # Get the raw data for this shot
    dev = pf.getDevice('DIIID')
    mag = dev.acq.getdata(shot,'DIIID_toroidal_mag')
    # mag contains the signal and timebase of the raw data
    # In [171]: mag.signal.shape
    # Out[171]: (14, 2039808)
    # In [172]: mag.timebase.shape
    # Out[174]: (2039808,)

    # Reduce the data to the time window we care about
    mag_red = mag.reduce_time(time_window)

    # Settings for performing the fft, i.e break the above signal into chunks 1024 samples long
    # and allow subsequent chunks to overlap
    samples = 1024; overlap = 4
    data_fft = mag_red.generate_frequency_series(samples,samples/overlap)

    # Some settings
    n_pts = 10; lower_freq = 1; cutoff_by = 'sigma_eq'; filter_cutoff = 55;
    datamining_settings = None; upper_freq = 500000; filter_item = 'EM_VMM_kappas'

    # Find peaks int fft data (i.e probably modes), and only keep those:
    good_indices = ext.find_peaks(data_fft, n_pts=n_pts, lower_freq=lower_freq, upper_freq=upper_freq)
    rel_data = ext.return_values(data_fft.signal,good_indices)

    # Put together some meta-data that should be useful later
    misc_data_dict = {}
    misc_data_dict['time'] = ext.return_time_values(data_fft.timebase, good_indices)
    misc_data_dict['freq'] = ext.return_non_freq_dependent(data_fft.frequency_base,good_indices)
    misc_data_dict['shot'] = np.ones(len(misc_data_dict['freq']),dtype=int)*shot

    # Not really meta-data, but can be useful to keep this for later
    misc_data_dict['mirnov_data'] = +rel_data

    # Calculate the phase differences between probes - this is the thing used for datamining!
    rel_data_angles = np.angle(rel_data)
    diff_angles = (np.diff(rel_data_angles))%(2.*np.pi)
    # Also important to map to -pi, pi
    diff_angles[diff_angles>np.pi] -= (2.*np.pi)

    instance_array_amps = +rel_data

    # STFT-clustering includes a clustering step before we get to the main clustering.
    # This is essentially to filter out any rubbish 
    datamining_settings = {'n_clusters':8, 'n_iterations':20, 'start': 'k_means','verbose':0, 'method':'EM_VMM'}
    z = ext.perform_data_datamining(diff_angles, misc_data_dict, datamining_settings)

    dt = np.mean(np.diff(mag.timebase))

    # Only keep instances that belong to well defined clusters - i.e useful information instead of noise
    instance_array_cur, misc_data_dict_cur = ext.filter_by_kappa_cutoff(z, ave_kappa_cutoff = filter_cutoff, ax = None, cutoff_by = cutoff_by, filter_item = filter_item)

    # Return this data from a single shot to be used in the big clustering step that involves all the shots
    instance_array = np.array(instance_array_cur)
    misc_data_dict = misc_data_dict_cur
    return instance_array, misc_data_dict, mag.signal, mag.timebase

def get_single_wrapper(input_data):
    print 'in wrapper svd'
    return copy.deepcopy(get_single(input_data[0], time_window=input_data[1]))

def get_stft_wrapper(input_data):
    print 'in wrapper stft'
    return copy.deepcopy(get_stft(input_data[0], time_window=input_data[1]))
    

# List of shots that we are interested in, and the time window that we care about in those shots:
#shot_list = [159243,159244]
#time_window = [300,1400]
#shot_list = [153067, 153071, 153072, 152932, 152938, 157399, 157400, 157401, 157402]
#time_windows = [[2800, 3000], [2800, 3000], [2800, 3000], [2500, 2700], [3000, 3200],
#                   [2300, 2500], [2300, 2500], [2300, 2500], [2300, 2500]]
shot_list = [153071,153072,152932, 152938, 157399, 157400, 157401, 157402]
time_windows = [[2800,3000],[2800,3000], [2800, 3000], [2500, 2700], [3000, 3200],
                [2300, 2500], [2300, 2500], [2300, 2500], [2300, 2500]]
# Bundle the above data together, note if we wanted we could have different time windows for each shot
#input_data_iter = itertools.izip(shot_list, itertools.repeat(time_window))
input_data_iter = itertools.izip(shot_list, time_windows)
# First stage is to extract features from the raw signals for each shot
# I.e create the things that we are going to use the clustering algorithm on.
# So how do you find interesting 'spectral features' in timeseries data?
# There are two methods that I have used a fair bit, the first is SVD analysis:
#   See chapter 3.1 and 3.2 of David Pretty's thesis
# The second method is called STFT-clustering, see section 2 and 3 of:
#  http://dx.doi.org/10.1016/j.cpc.2014.03.008

# The choice of "wrapper" decides which of the above two methods is going to
#be used, note the wrappers are required for the multi-processing,
#look int he wrapper functions to see the function that ultimately
#gets called wrapper = get_single_wrapper
wrapper = get_stft_wrapper

# We take advantage of the fact that each shot can be analysed
# independently, so we can use multiple CPUs to speed things up
n_cpus = 1

# Only go through the extra effort required for multiprocessing if n_cpu is greater than 1
if n_cpus>1:
    pool_size = n_cpus
    # Setup the multiprocessing
    # results will be a list where each item contains the identified 
    pool = Pool(processes=pool_size, maxtasksperchild=3)
    results = pool.map(wrapper, input_data_iter)
    pool.close()
    pool.join()
else:
    results = map(wrapper, input_data_iter)

# At this stage 
# results[0][0] and results[0][1] are  arrays of the phase differences for all interesting features identified in the shot and a dictionary which contains some meta data such as shot number, and frequency
# results[1][0] and results[1][1] are the same as above except for the second shot in the list, etc...
# In [76]: results[0][0].shape
# Out[76]: (12816, 13)

# In [77]: results[0][1]['freq'].shape
# Out[77]: (12816,)

# Next we want to combine the data from all the shots (i.e items in the results list) into a single phase differences array (called instance_array), and a single dictionary containing meta-data (misc_data_dict)
start = 1
for i,tmp in enumerate(results):
    print i
    if tmp[0]!=None:
        if start==1:
            instance_array = copy.deepcopy(tmp[0])
            misc_data_dict = copy.deepcopy(tmp[1])
            start = 0
        else:
            instance_array = np.append(instance_array, tmp[0],axis=0)
            for i in misc_data_dict.keys():
                misc_data_dict[i] = np.append(misc_data_dict[i], tmp[1][i],axis=0)
    else:
        print 'One shot may have failed....'

# Now all of the data from all of the shots is contained in instance_array, and misc_data_dict
# Note the dimensions: for this case we have identified 19678 interesting things, there are 13 phase differences between channels
# Each index in misc_data_dict[XXXX] matches up with the column number in instance_array
# In [81]: instance_array.shape
# Out[81]: (19678, 13)

# In [82]: misc_data_dict['shot'].shape
# Out[82]: (19678,)

# In [83]: misc_data_dict['freq'].shape
# Out[83]: (19678,)

# In [84]: misc_data_dict['time'].shape
# Out[84]: (19678,)

# I.e the phases differences, time, shot number, and frequency for the 10th interesting thing are:
# In [85]: instance_array[10,:]
# Out[85]: 
# array([ 0.62393259, -1.16184058,  0.35121318,  0.02464877, -0.05007769,
#         0.17279242,  0.03985014,  0.03270833,  0.20733238,  0.06055794,
#        -0.25735253,  0.12476335,  0.036808  ])

# In [86]: misc_data_dict['time'][10]
# Out[86]: 304.09499999999997

# In [87]: misc_data_dict['shot'][10]
# Out[87]: 159243

# In [88]: misc_data_dict['freq'][10]
# Out[88]: 30.273399999999999


# Next we create a "feature_object" which has all of this information
# We do this because this feature_object is what is used for the clustering
feat_obj = clust.feature_object(instance_array = instance_array, instance_array_amps = +misc_data_dict['mirnov_data'], misc_data_dict = misc_data_dict)
# Note feat_obj.instance_array and feat_obj.misc_data_dict are the instance arrays from above 

# At any time now you can save feat_obj as it is
# feat_obj.dump_data("hello.pickle")
# And then reload it at a later time:
# feat_obj2 = clust.feature_object(filename='hello.pickle')

# Now we are ready to do the actual datamining
# We need to choose which settings to use:
datamining_settings = {'n_clusters':16, 'n_iterations':20, 
                       'start': 'k_means','verbose':0, 'method':'EM_VMM'}

# Perform the datamining, and return an object with the results!
z = feat_obj.cluster(**datamining_settings)
# z.cluster_assignments is a list of integers which identify which cluster each of the items in instance_array belong to
# In [89]: z.cluster_assignments
# Out[101]: array([9, 0, 9, ..., 4, 5, 4])
# z.cluster_details is a dictionary containing statistical information about each of the clusters
# Also note that z.feature_obj is the same as feat_obj from earler

# "z" is also stored in the following list feat_obj.clustered_objects
# if you do z2 = feat_obj.cluster(**datamining_settings) again using different settings then:
# feat_obj.clustered_objects[0] is z, and feat_obj.clustered_objects[1] is z2
# We can make some interesting plots using the returned object 
# This is very useful when combined with being able to save feat_obj as described earlier
# i.e feat_obj.dump_data("hello.pickle")

# We can make some plots:
#z.plot_VM_distributions()
#z.plot_dimension_histograms()
#dims = [[i,i+1] for i in range(13)]
#z.plot_phase_vs_phase(compare_dimensions=dims)
#z.plot_cumulative_phases()

#If you want to investigate cluster #4 in more detail
# In [116]: mask=(z.cluster_assignments==4)
#
# In [117]: mask
# Out[117]: array([False, False, False, ...,  True, False,  True], dtype=bool)
# Now we can use this mask to find out the phase differences for all the instances that are in that cluster:
# In [118]: feat_obj.instance_array[mask,:]

# We can also get at the meta data for that particular cluster! shot #'s, time's, frequencies, etc...
# In [159]: feat_obj.misc_data_dict['shot'][mask]
# Out[159]: array([159244, 159244, 159244, ..., 159244, 159244, 159244])

# In [160]: feat_obj.misc_data_dict['freq'][mask]
# Out[160]: array([ 175.293,  175.293,  175.293, ...,  168.457,  175.293,  175.293])

# In [161]: feat_obj.misc_data_dict['time'][mask]
# Out[161]: 
# array([  894.431,   301.023,   301.535, ...,  1396.191,  1398.239,
#         1398.751])

# This information can be used to go and get any extra information that you want to get
print("Plotting...")


#nrows = int(np.sqrt(len(shot_list)))
#ncols = int(np.ceil(len(shot_list)/nrows))
nrows = 3
ncols = 3
fig, ax = plt.subplots(nrows = nrows, ncols=ncols, sharex=False, sharey=False)
axf = ax.flatten()
fig2, ax2 = plt.subplots(nrows = nrows, ncols=ncols, sharex=False, sharey=False)
axf2 = ax2.flatten()
plot_colors = {}
for cur_ax, cur_ax2, shot, tmp in zip(axf, axf2, shot_list, results):
    assign = z.cluster_assignments
    details = z.cluster_details['EM_VMM_kappas']
    shot_details = z.feature_obj.misc_data_dict['shot']
    timebase = tmp[3]
    sig = tmp[2]
    dt = np.mean(np.diff(timebase))
    #tmp_sig = np.sqrt(np.sum(sig**2,axis=0))
    tmp_sig = sig[0,:]
    im = cur_ax.specgram(tmp_sig, NFFT=1024,Fs=1./dt, noverlap=128,xextent=[timebase[0], timebase[-1]])
    im = cur_ax2.specgram(tmp_sig, NFFT=1024,Fs=1./dt, noverlap=128,xextent=[timebase[0], timebase[-1]])
    for i in np.unique(assign):
        mask = (assign==i) * (shot_details==shot)
        if np.sum(mask)>1 and np.mean(details[i,:])>5:
            if i not in plot_colors:
                markersize = 5
                pl = cur_ax.plot(z.feature_obj.misc_data_dict['time'][mask], z.feature_obj.misc_data_dict['freq'][mask],'o', markersize=markersize)
                #pl = cur_ax.scatter(z.feature_obj.misc_data_dict['time'][mask], z.feature_obj.misc_data_dict['freq'][mask], alpha=0.3)
                plot_colors[i] = pl[0].get_color()
                #plot_colors[i] = (pl.get_facecolor(), pl.get_edgecolor())
            else:
                pl = cur_ax.plot(z.feature_obj.misc_data_dict['time'][mask], z.feature_obj.misc_data_dict['freq'][mask],'o', markersize=markersize, color=plot_colors[i])
                #pl = cur_ax.scatter(z.feature_obj.misc_data_dict['time'][mask], z.feature_obj.misc_data_dict['freq'][mask], facecolor=plot_colors[i][0],edgecolor=plot_colors[i][1],alpha=0.3)
    #cur_ax.plot(misc_data_dict['time'][shot_details==shot], misc_data_dict['freq'][shot_details==shot], '.',color='white',markersize=5)
#axf[0].set_xlim(time_window)
#axf2[0].set_xlim(time_window)

tmp = len(time_windows)
for _ in range(tmp-1):
    axf[_].set_xlim(time_windows[_])
    axf2[_].set_xlim(time_windows[_])
    axf[_].set_ylim([0,100])
    axf2[_].set_ylim([0,100])
#axf[0].set_xlim([2800,3000])
#axf2[0].set_xlim([2800,3000])

#fig.subplots_adjust(bottom=0.02, left=0.02, right=0.95, top=0.95,wspace=0.01,hspace=0.01)
#fig2.subplots_adjust(bottom=0.02, left=0.02, right=0.95, top=0.95,wspace=0.01,hspace=0.01)
fig.canvas.draw();fig.show()
fig2.canvas.draw();fig2.show()


#copy.deepcopy(tmp.instance_array_list), copy.deepcopy(tmp.misc_data_dict)
#ecei = dev.acq.getdata(164950,'ECE1')
#print mag.timebase

1/0


def get_interesting(self, n_pts = 20, lower_freq = 1500, cutoff_by = 'sigma_eq', filter_cutoff = 20, datamining_settings = None, upper_freq = 500000, filter_item = 'EM_VMM_kappas'):

    if datamining_settings == None: datamining_settings = {'n_clusters':16, 'n_iterations':20, 'start': 'k_means','verbose':0, 'method':'EM_VMM'}
    print datamining_settings
    good_indices = ext.find_peaks(self.data_fft, n_pts=n_pts, lower_freq = lower_freq, upper_freq = upper_freq)
    self.good_indices = good_indices
    #Use the best peaks to the get the mirnov data
    rel_data = ext.return_values(self.data_fft.signal,good_indices)
    self.misc_data_dict['mirnov_data'] = +rel_data
    rel_data_angles = np.angle(rel_data)
    self.instance_array_amps = +rel_data
    #Use the best peaks to get the other interesting info
    # for i,tmp_label in zip(self.other_arrays_fft, self.other_array_labels):
    #     if tmp_label[0]!=None: 
    #         self.misc_data_dict[tmp_label[0]] = return_values(i.signal, good_indices, force_index = 0)
    #     if tmp_label[1]!=None: 
    #         self.misc_data_dict[tmp_label[1]] = return_values(i.signal, good_indices)

    self.misc_data_dict['time'] = ext.return_time_values(self.data_fft.timebase, good_indices)
    self.misc_data_dict['freq'] = ext.return_non_freq_dependent(self.data_fft.frequency_base,good_indices)
    #misc_data_dict['shot'] = misc_data_dict['time'] * 0 + self.shot
    #misc_data_dict['kh'] = misc_data_dict['time'] * 0 + data.meta['kh']
    # for i in self.meta_data:
    #     try:
    #         if self.data.meta[i]!=None:
    #             self.misc_data_dict[i] = self.misc_data_dict['time'] * 0 + copy.deepcopy(self.data.meta[i])
    #         else:
    #             self.misc_data_dict[i] = np.zeros(self.misc_data_dict['time'].shape, dtype = bool)
    #     except KeyError:
    #         self.misc_data_dict[i] = np.zeros(self.misc_data_dict['time'].shape, dtype = bool)

    diff_angles = (np.diff(rel_data_angles))%(2.*np.pi)
    diff_angles[diff_angles>np.pi] -= (2.*np.pi)

    self.z = ext.perform_data_datamining(diff_angles, self.misc_data_dict, datamining_settings)#n_clusters = 16, n_iterations = 20)

    #filter_item = 'EM_VMM_kappas' if datamining_settings['method'] == 'EM_VMM' else 'EM_GMM_variances'
    instance_array_cur, misc_data_dict_cur = ext.filter_by_kappa_cutoff(self.z, ave_kappa_cutoff = filter_cutoff, ax = None, cutoff_by = cutoff_by, filter_item = filter_item)
    self.instance_array_list = instance_array_cur
    self.misc_data_dict = misc_data_dict_cur
    #return instance_array_cur, misc_data_dict_cur, z.cluster_details['EM_VMM_kappas']

