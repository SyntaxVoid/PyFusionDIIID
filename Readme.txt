Just a general text file with some instructions on how to do things.

In[x]: indicates a python command.
IDL>  indicates an IDL command.

I. Making a database from scratch.
    Given a certain shot and time window, you can calculate the FFT of the signals
    with the 'run_fft()' command found in 'make_db.py'.
        In[1]: import make_db
        In[2]: data_fft = make_db.run_fft(shot=159243,time_window=[350,550])

    You can then write a database full of events from the FFT. An event is defined as
    a peak in the FFT. It is desirable to write a seperate database for events because
    there can be 20 events per time slice as opposed to just one value for a point name
    like the plasma current.
        In[3]: make_db.make_event_database(shot,data_fft,location="example_event_database.txt")

    At this point, we have to switch to IDL since I'm not away of a pythonic procedure for
    fetching pointnames such as plasma current (ip), electron temperature (tste_0), etc...
    If it is not already in your IDL path, navigate to where make_dbv2.pro is located and
    run IDL.
    *** TODO: Have python write out a file consisting of shot & times so that I can read it into IDL.
        IDL> make_dbv2,159243,["ip","betan","cerqrott1","cerqrott6"],"example_db.sav"
    At this point, an IDL structure named "data_dict" that contains the given pointnames
    is stored at "example_db.sav". To analyze this structure within IDL:
        IDL> restore,"example_db.sav"
        IDL> help,data_dict
    To plot plasma current (ip) vs time:
        IDL> plot,data_dict.time,data_dict.ip

    Moving back to Python, now we have to load the idlsav file and format it into an ordered
    dictionary.
        In[4]: import jtools
        In[5]: ord_dict = jt.idlsav_to_ordered_dict("example_db.sav")

    And then we write the master database with the values found within IDL
        In[6]: jt.write_master_database("example_master_db.txt"," # Example Header",ord_dict)

    Some additional notes:
        The event database is formatted as such:

# SAMPLE HEADER OF EVENT DATABASE
#SHOT: <shot> TIME: <time_of_event>
frequency peaks separated by commas
#SHOT: <shot> TIME: <time_of_event>
frequency peaks separated by commas

        The master database is formated as such:

# SAMPLE HEADER OF MASTER DATABASE
#shot          time          q0            q95           ip
<shot>        <time>        <q0>          <q95>         <ip>
<shot>        <time>        <q0>          <q95>         <ip>