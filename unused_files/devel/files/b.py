import re

with open("heal_full.txt", "r") as f:

    lines = f.readlines()
    # print lines
    for line in lines:
        m = re.search(
            "Heal operation on volume [a-zA-Z_\-]* has been successful", line)
        # print m
        if m:
            print m.group()

# vim: tabstop=8 softtabstop=0 expandtab ai shiftwidth=4 smarttab
