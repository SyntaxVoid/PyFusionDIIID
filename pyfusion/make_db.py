# John Gresl 1/9/2017

import os.path


def make_db(shot, location):
    # Verify that there is not a database at the location already. If there is,
    # ask the user if they would like to overwrite the file.
    if os.path.isfile(location):
        valid_ans = ["y","yes","n","no"]
        ans = raw_input("File already exists at:\n\t{}.\nWould you like to overwrite this file? (y/n)\n".format(location)).lower().strip()
        while ans not in valid_ans:
            ans = raw_input("\"{}\" is not a valid input. Please select a choice from {}. . .\n".format(ans, valid_ans)).lower().strip()
        print(ans)
    header = '''# Shot {}\n# START DATA'''.format(shot)
    with open(location,"w") as database:
        database.write(header)
        database.write("\ntest...")
    return

if __name__ == '__main__':
    make_db(1,"C:\\Users\\John Gresl\\OneDrive\\Documents\\PyFusion\\pyfusion\\test_database.txt")

