from multiprocessing import Pool
import pyfusion as pf
import numpy as np
import copy, os, time, itertools
import matplotlib.pyplot as plt



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
            #ind1 = np.argmin(np.abs(data_fft.timebase - time_seg_average_time))
            #ind2 = np.argmin(np.abs(data_fft.frequency_base - misc_data_dict['freq'][-1]))
            #misc_data_dict['mirnov_data'].append(data_fft.signal[ind1,:,ind2])

            # for i,tmp_label in zip(other_arrays_data_fft, self.other_array_labels):
            #     if tmp_label[0]!=None: self.misc_data_dict[tmp_label[0]].append((i[:,0]))
            #     if tmp_label[1]!=None: self.misc_data_dict[tmp_label[1]].append((i[:,tmp_loc]))
            phases = np.array([tmp_phase.delta for tmp_phase in fs.dphase])
            phases[np.abs(phases)<0.001]=0
            instance_array_list.append(phases)
    for i in misc_data_dict.keys():
        misc_data_dict[i]=np.array(misc_data_dict[i])
    instance_array = np.array(instance_array_list)
    return instance_array, misc_data_dict, mag.signal, mag.timebase



def get_stft(shot, time_window = None):
    if time_window == None: time_window=[1000,5000]
    dev = pf.getDevice('DIIID')
    print("I connected!")
    mag = dev.acq.getdata(shot,'DIIID_toroidal_mag')
    mag_red = mag.reduce_time(time_window)
    samples = 1024
    overlap = 4
    data_fft = mag_red.generate_frequency_series(samples,samples/overlap)
    import pyfusion.clustering.extract_features_scans as ext
    n_pts = 20; lower_freq = 1; cutoff_by = 'sigma_eq'; filter_cutoff = 55; datamining_settings = None; upper_freq = 500000; filter_item = 'EM_VMM_kappas'

    timebase = mag.timebase
    good_indices = ext.find_peaks(data_fft, n_pts=n_pts, lower_freq=lower_freq, upper_freq=upper_freq)
    rel_data = ext.return_values(data_fft.signal,good_indices)
    misc_data_dict = {}
    misc_data_dict['mirnov_data'] = +rel_data
    rel_data_angles = np.angle(rel_data)
    instance_array_amps = +rel_data
    misc_data_dict['time'] = ext.return_time_values(data_fft.timebase, good_indices)
    misc_data_dict['freq'] = ext.return_non_freq_dependent(data_fft.frequency_base,good_indices)
    misc_data_dict['shot'] = np.ones(len(misc_data_dict['freq']),dtype=int)*shot
    diff_angles = (np.diff(rel_data_angles))%(2.*np.pi)
    diff_angles[diff_angles>np.pi] -= (2.*np.pi)
    datamining_settings = {'n_clusters':16, 'n_iterations':20, 'start': 'k_means','verbose':0, 'method':'EM_VMM'}
    z = ext.perform_data_datamining(diff_angles, misc_data_dict, datamining_settings)

    #fig10, ax10 = plt.subplots()
    dt = np.mean(np.diff(timebase))
    #im = ax10.specgram(mag.signal[0,:], NFFT=1024,Fs=1./dt, noverlap=128,xextent=[timebase[0], timebase[-1]])
    instance_array_cur, misc_data_dict_cur = ext.filter_by_kappa_cutoff(z, ave_kappa_cutoff = filter_cutoff, ax = None, cutoff_by = cutoff_by, filter_item = filter_item)
    #fig10.canvas.draw();fig10.show()
    instance_array = np.array(instance_array_cur)
    misc_data_dict = misc_data_dict_cur
    return instance_array, misc_data_dict, mag.signal, mag.timebase

def get_single_wrapper(input_data):
    print 'in wrapper'
    return copy.deepcopy(get_single(input_data[0], time_window=input_data[1]))

def get_stft_wrapper(input_data):
    print 'in wrapper stft'
    return copy.deepcopy(get_stft(input_data[0], time_window=input_data[1]))
    

shot_list = [163518,164950,164436,165402]

#shot_list = np.arange(159243,159257+1)#159257+1)
#shot_list = np.arange(159243,159257+1)#159257+1)

shot_list = np.arange(159243, 159257+1)
#shot_list = np.arange(159243, 159243+3)
results = []
time_window = [1000,2000]
time_window = [300,1400]
#time_window = [1000,5000]
nrows = int(np.sqrt(len(shot_list)))
ncols = int(np.ceil(len(shot_list)/nrows))
fig, ax = plt.subplots(nrows = nrows, ncols=ncols, sharex=True, sharey=True)
axf = ax.flatten()

rep = itertools.repeat
input_data_iter = itertools.izip(shot_list, rep(time_window))

n_cpus = 1

#generate the shot list for each worker
#wrapper = get_single_wrapper
wrapper = get_stft_wrapper
if n_cpus>1:
    pool_size = n_cpus
    pool = Pool(processes=pool_size, maxtasksperchild=3)
    print 'creating pool map'
    results = pool.map(wrapper, input_data_iter)
    print 'waiting for pool to close '
    pool.close()
    print 'joining pool'
    pool.join()
    print 'pool finished'
else:
    results = map(wrapper, input_data_iter)

#for cur_ax, shot in zip(axf,shot_list):
#    results.append(get_single(shot, time_window))
#fig.canvas.draw();fig.show()
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
#return clust.feature_object(instance_array = instance_array, instance_array_amps = +misc_data_dict['mirnov_data'], misc_data_dict = misc_data_dict)
import pyfusion.clustering as clust
feat_obj = clust.feature_object(instance_array = instance_array, instance_array_amps = +misc_data_dict['mirnov_data'], misc_data_dict = misc_data_dict)
datamining_settings = {'n_clusters':16, 'n_iterations':20, 
                       'start': 'k_means','verbose':0, 'method':'EM_VMM'}
z = feat_obj.cluster(**datamining_settings)
z.plot_VM_distributions()
z.plot_dimension_histograms()
#z.plot_phase_vs_phase(compare_dimensions=[[1,2],[2,3]])
dims = [[i,i+1] for i in range(13)]
z.plot_phase_vs_phase(compare_dimensions=dims)
z.plot_cumulative_phases()


fig, ax = plt.subplots(nrows = nrows, ncols=ncols, sharex=True, sharey=True)
axf = ax.flatten()
fig2, ax2 = plt.subplots(nrows = nrows, ncols=ncols, sharex=True, sharey=True)
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
axf[0].set_xlim(time_window)
axf2[0].set_xlim(time_window)
fig.subplots_adjust(bottom=0.02, left=0.02, right=0.95, top=0.95,wspace=0.01,hspace=0.01)
fig2.subplots_adjust(bottom=0.02, left=0.02, right=0.95, top=0.95,wspace=0.01,hspace=0.01)
fig.canvas.draw()#;fig.show()
fig2.canvas.draw()#;fig2.show()
plt.show()

#copy.deepcopy(tmp.instance_array_list), copy.deepcopy(tmp.misc_data_dict)
#ecei = dev.acq.getdata(164950,'ECE1')
#print mag.timebase

#1/0

'''
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

'''