# jtools.py
# John Gresl 10/6/2016
import os.path
from copy import deepcopy

# Contains useful auxiliary functions for aesthetics. . .

def numlist_to_strlist(it):
    out = []
    for i in it:
        out.append(str(i))
    return out


def print_dict(d,mod):
    # Prints a dictionary with 'mod' before each line
    f_str = "{}{{:{}}}:  {{}}".format(mod, max(map(len, d.keys()))+2)
    for k,v in d.items():
        print(f_str.format(k,v))

def ensure_valid_path(p):
    # Ensures that p is a valid path to a file. If the path already exists,
    # ask the user if they would like to overwrite it.
    if os.path.isfile(p):
        valid_ans = ["y","yes","n","no"]
        ans = raw_input("File already exists at:\n\t{}\nWould you like to overwrite this file? (y/n)\n".format(p)).lower().strip()
        while ans not in valid_ans:
            ans = raw_input("\"{}\" is not a valid input. Please select a choice from {}. . .\n".format(ans, valid_ans)).lower().strip()
        return 0 if ans in ["no","n"] else 1
    return 1

def write_master_database(location,header, ord_dict):
    do_write = ensure_valid_path(location)
    if not do_write:
        print("Invalid file path... Please start over.")
        return None
    categories = ord_dict.keys()
    values = ord_dict.values()
    n = len(categories)
    #m = n-2 # The number of categories that are NOT shot or time
    #categories.remove("shot") # We don't need these two in categories anymore.
    #categories.remove("time")
    values_as_str = []
    for array in values:
        values_as_str.append(numlist_to_strlist(array))
    values = values_as_str


    # The first array in values is a shot array, the second array is a time array.
    # This should ALWAYS be true.. Maybe I should check with code to be 100% sure.
    #shots = numlist_to_strlist(ord_dict["shot"])
    #times = numlist_to_strlist(ord_dict["time"])


    # Write the header and the categories, with 14 spaces allocated per column
    #cat_str = "#" + "{:14s}"*m
    cat_str = "#" + "{:14s}" * n
    cat_str = cat_str.format(*categories)
    with open(location,"w") as db:
        db.write(header+"\n")
        db.write(cat_str)
        for v in zip(*values):
            line_str = "{:14s}" * n
            line_str = line_str.format(*v)
            db.write("\n" + line_str)
    return

def write_event_database(location, header, ord_dict):
    do_write = ensure_valid_path(location)
    if not do_write:
        print("Invalid file path... Please start over.")
        return None

    # Get categories, which are the names of the values in ord_dict.
    categories = ord_dict.keys()
    values = ord_dict.values()
    n = len(categories)

    # All we care about are the shot numbers, times, and frequencies.
    shots = numlist_to_strlist(ord_dict["shot"])
    times = numlist_to_strlist(ord_dict["time"])
    freqs = numlist_to_strlist(ord_dict["freq"])

    event_str = "#SHOT: {:6s} TIME: {:6s}"
    freq_str  = "{}"
    to_write = "\0 " # Trust me, we need this here.
    with open(location,"w") as event_db:
        event_db.write(header)
        cur_s = -9999.
        cur_t = -9999.
        for s,t,f in zip(shots,times,freqs):
            # if its a new shot or a new time, we need to write the sub-header
            if (s != cur_s or t != cur_t):
                event_db.write(to_write[:-2])
                to_write = ""
                event_db.write("\n"+event_str.format(s,t)+"\n")
                cur_s = s
                cur_t = t
            to_write += freq_str.format(f) + ", "
        event_db.write(to_write[:-2])
    return


def write_columns(location, header, ord_dict):
    # I would like to use **kwargs here but python 2 treats it as an unordered dict, which will make the database
    # lose designated structure. Instead, will have to pass an ordered dict as an argument and manually unpack it.
    # WARNING: In order to write to a file, all values within ord_dict will be converted to strings. If a value is an
    # abstract class, make sure it has an appropriate __repr__(self).
    do_write = ensure_valid_path(location)
    if not do_write:
        print("Invalid file path... Please start over.")
        return None

    # Get categories, which are the names of the values in ord_dict.
    categories = ord_dict.keys()
    values = ord_dict.values()
    n = len(categories)

    # Every list in values must have the same length. Otherwise raise an assertion error.
    m = len(values[0])
    for i in range(1,n):
        assert len(values[i]) == m

    # Convert everything in values to a str.
    values_as_str = []
    for array in values:
        values_as_str.append(numlist_to_strlist(array))

    #Allocate 14 spaces per column
    col_width = 14
    cat_string = "{{:{}s}}".format(col_width)
    cat_string = cat_string*n

    with open(location,"w") as db:
        db.write(header)
        db.write("\n#"+cat_string.format(*categories))
        for i in range(m):
            cur_line = []
            for j in range(n):
                cur_line.append(values_as_str[j][i])
            db.write("\n " + cat_string.format(*cur_line))

    return
