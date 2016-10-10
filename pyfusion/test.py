
# Test taken from Appendix G of Shaun's thesis
import pyfusion.clustering as clust
import pyfusion.clustering.extract_features_scans as ext

dataset = ["test_shots"]
array = ["DIIID_toroidal_mag"]
other_arrays = ["DIIID_toroidal_mag"]
other_array_labels = ["toroidal mag"]
meta_data = ["kh", "heating_freq", "main_current","sec_current","shot"]
ext_settings_svd = {"min_svs": 2, "power_cutoff": 0.006, "lower_freq": 4000, "upper_freq": 200000}

print("Before svd multi extract.")
svd_data = ext.multi_extract_DIIID(dataset,array,other_arrays=other_arrays,other_array_labels=other_array_labels,
                                   meta_data=meta_data, n_cpus=1, NFFT=1024, overlap=4,
                                   extraction_settings=ext_settings_svd,method="svd")
print("After svd multi extract.")
datamining_settings = {"n_clusters": 16, "n_iterations": 20, "start": "k_means", "verbose": 1, "method": "EM_VMM"}

extraction_settings = {"n_pts": 5, "lower_freq": 1500, "filter_cutoff": 0.18, "cutoff_by": "sigma_bar",
                       "datamining_settings": datamining_settings, "upper_freq": 100000}

print("Before STFT")
stft_data = ext.multi_extract_DIIID(dataset, array, other_arrays = other_arrays, other_array_labels=other_array_labels,
                                    meta_data=meta_data,n_cpus=1,NFFT=1024,overlap=4,extraction_settings=extraction_settings,method="stft")
print("After STFT")
comb_data = ext.combine_feature_sets(svd_data,stft_data)
svd_cluster = svd_data.cluster(method="EM_VMM", start="k_means", n_clusters = 16, n_iterations = 50, number_of_starts = 4, n_cpus = 1)
svd_cluster.plot_single_kh()







'''

import random
from matplotlib import pyplot as plt
from matplotlib import ticker as mtick


def make_cluster(xmin,ymin,xmax,ymax,npts):
    xout = []
    yout = []
    for i in range(npts):
        xout.append(random.uniform(xmin,xmax))
        yout.append(random.uniform(ymin,ymax))
    return xout, yout

c1 = make_cluster(1,.2,2,2,35)
c2 = make_cluster(3,0.3,4,2,32)
c3 = make_cluster(1,3,3,5,37)

loc = mtick.MultipleLocator(base=0.5)
fig,ax = plt.subplots()
ax.plot(c1[0],c1[1],"ro",c2[0],c2[1],"go",c3[0],c3[1],"bo")
ax.xaxis.set_major_locator(loc)
ax.yaxis.set_major_locator(loc)
plt.axis([0,5,0,6])
ax.grid()
plt.title("Clustering Example")
plt.legend(["Cluster 1","Cluster 2","Cluster 3"])
plt.show()

'''