# jtools.py
# John Gresl 10/6/2016

# Contains useful auxiliary functions for aesthetics. . .

def print_dict(d,mod):
    # Prints a dictionary with 'mod' before each line
    f_str = "{}{{:{}}}:  {{}}".format(mod, max(map(len, d.keys()))+2)
    for k,v in d.items():
        print(f_str.format(k,v))