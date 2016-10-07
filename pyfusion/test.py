d = {"NAME": "John", "AGE": 21, "LIKES": ["physics","math","4"]}


def print_dict(d):
    f_str = "\t{{:{}}}:  {{}}".format(max(map(len, d.keys()))+2)
    for k,v in d.items():
        print(f_str.format(k,v))