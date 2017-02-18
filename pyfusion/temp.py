d = '''channel_1  = MPI66M322D
channel_2  = MPI6NA322D
channel_3  = MPI6FA322D
channel_4  = MPI67A322D
channel_5  = MPI7NA322D
channel_6  = MPI7FA322D
channel_7  = MPI79N322D
channel_8  = MPI79F322D
channel_9  = MPI9A322D
channel_10 = MPI89A322D
channel_11 = MPI8A322D
channel_12 = MPI5A322D
channel_13 = MPI4A322D
channel_14 = MPI3A322D
channel_15 = MPI2A322D
channel_16 = MPI1A322D
channel_17 = MPI11M322D
channel_18 = MPI1B322D
channel_19 = MPI2B322D
channel_20 = MPI3B322D
channel_21 = MPI4B322D
channel_22 = MPI5B322D
channel_23 = MPI8B322D
channel_24 = MPI89B322D
channel_25 = MPI9B322D
channel_26 = MPI79B322D
channel_27 = MPI7FB322D
channel_28 = MPI7NB322D
channel_29 = MPI67B322D
channel_30 = MPI6FB322D
channel_31 = MPI6NB322D'''

f_str = '''[Diagnostic:{}]
data_fetcher = pyfusion.acquisition.DIIID.fetch.DIIIDDataFetcherPTdata
mds_tree = ptdata
pointname = {}'''

out = ""

x = d.split("\n")
channels = []
for i in x:
    channel = i.split()[2]
    out += f_str.format(channel,channel) + "\n\n"

f = open("temp.txt","w")
f.write(out)
f.close()
