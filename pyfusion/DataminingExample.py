import Analysis

## Some settings
shots = range(159243,159246+1)
time_window = [300,1400]
probes = "DIIID_toroidal_mag"
datamining_settings = {'n_clusters': 8, 'n_iterations': 20, 'start': 'k_means',
                       'verbose': 0, 'method': 'EM_VMM', "seeds": [832]}
## First, we create the Analysis object which conveniently stores all our information in one place.
A1 = Analysis.Analysis(shots=shots, time_windows=time_window,
                       probes=probes,datamining_settings=datamining_settings,
                       markersize=7)
## Then we run the analysis, which will perform all the datamining and clustering
A1.run_analysis()
## Then, we can plot the clusters for reference
A1.plot_clusters()
## We can plot some diagnostics for a particular time and frequency
A1.plot_diagnostics(time_window=time_window, t0=801.711, f0=85.9375, idx="tor")
