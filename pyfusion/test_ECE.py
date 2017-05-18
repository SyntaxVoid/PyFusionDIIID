from multiprocessing import Pool
import pyfusion as pf
import numpy as np
import copy, os, time, itertools
import matplotlib.pyplot as plt
import cPickle as pickle
import pyfusion.clustering as clust
import pyfusion.clustering.extract_features_scans as ext

use_ECE = True

shot_list = [159243]
shot = shot_list[0]
time_window = [300,1400]

if time_window == None: time_window=[1000,5000]

# Get the raw data for this shot
dev = pf.getDevice('DIIID')
if use_ECE:
    mag = dev.acq.getdata(shot,'ECEF_array')
    print 'use ECEF, {}'.format(shot)
else:
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
n_pts = 20; lower_freq = 1; cutoff_by = 'sigma_eq'; filter_cutoff = 70; #filter_cutoff = 55; 
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
datamining_settings = {'n_clusters':16, 'n_iterations':20, 'start': 'k_means','verbose':0, 'method':'EM_VMM'}
z = ext.perform_data_datamining(diff_angles, misc_data_dict, datamining_settings)

dt = np.mean(np.diff(mag.timebase))

# Only keep instances that belong to well defined clusters - i.e useful information instead of noise
instance_array_cur, misc_data_dict_cur = ext.filter_by_kappa_cutoff(z, ave_kappa_cutoff = filter_cutoff, ax = None, cutoff_by = cutoff_by, filter_item = filter_item)

# Return this data from a single shot to be used in the big clustering step that involves all the shots
instance_array = np.array(instance_array_cur)
misc_data_dict = misc_data_dict_cur

divisor = np.sum(np.abs(misc_data_dict['mirnov_data']),axis=1)
misc_data_dict['mirnov_data_backup'] = copy.deepcopy(misc_data_dict['mirnov_data'])
misc_data_dict['mirnov_data'] = copy.deepcopy(misc_data_dict['mirnov_data_backup'])
misc_data_dict['mirnov_data'] = np.abs(misc_data_dict['mirnov_data']/divisor[:,np.newaxis])

# Now for the actual datamining
feat_obj = clust.feature_object(instance_array = instance_array, instance_array_amps = +misc_data_dict['mirnov_data'], misc_data_dict = misc_data_dict)
datamining_settings = {'n_clusters':16, 'n_iterations':20, 
                       'start': 'k_means','verbose':0, 'method':'EM_VMM'}
datamining_settings = {'n_clusters':12, 'sin_cos':0,
                       'verbose':0, 'method':'k_means'}
z = feat_obj.cluster(amplitude=True,**datamining_settings)

z.plot_VM_distributions()

z.plot_clusters_amp_lines()

assign = z.cluster_assignments

fig, ax = z.plot_time_freq_all_clusters()
fig2, ax2 = plt.subplots(ncols=2,sharex=True,sharey=True)
sig = mag_red.signal
timebase = mag_red.timebase
dt = np.mean(np.diff(timebase))
tmp_sig = sig[3,:]
for i in ax.flatten():
    im = i.specgram(tmp_sig, NFFT=1024,Fs=1./dt, noverlap=128,xextent=[timebase[0], timebase[-1]],cmap='viridis',zorder=-1)
    im[-1].set_clim([-80,-40])
for i in np.atleast_1d(ax2).flatten():
    im = i.specgram(tmp_sig, NFFT=1024,Fs=1./dt, noverlap=128,xextent=[timebase[0], timebase[-1]],cmap='viridis',zorder=-1)
    im[-1].set_clim([-80,-40])

plot_colors = {}
for i in np.unique(assign):
    mask = (assign==i)
    if np.sum(mask)>1:
        if i not in plot_colors:
            markersize = 5
            pl = ax2[0].plot(z.feature_obj.misc_data_dict['time'][mask], z.feature_obj.misc_data_dict['freq'][mask],'o', markersize=markersize)
fig2.canvas.draw(); fig2.show()
fig.canvas.draw(); fig.show()


