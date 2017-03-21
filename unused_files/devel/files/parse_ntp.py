import re
servers = []
with open("ntp.conf", "r") as f:

    lines = f.readlines()
    for line in lines:
        r1 = re.match("[\s]*server[\s]*([\S]+)[\s]*([\"preferred\"]*)", line)
        if r1:
            s = r1.groups()[0]
            print r1.groups()

    print lines

# vim: tabstop=8 softtabstop=0 expandtab ai shiftwidth=4 smarttab
