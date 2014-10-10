#!/usr/bin/python

# To get the Hard Disk Drive, Temp, CPU and FAN information

import re
import os
import sys
import json
import glob

def get_disk_list():
    disk_list = []
    #cmd1 = os.popen("sudo smartctl --scan")
    cmd1 = os.popen("/usr/sbin/smartctl --scan")
    str1 = cmd1.read()

    lines = re.split("\r?\n", str1)
    reobj1 = re.compile("(/dev/[a-z]+)")
    for l in lines[:]:   
        if reobj1.search(l):
            ent1 = re.search(r'/dev/sd[a-z]', l)
	    match = ent1.group()
	    disk_list.append(match)
    return disk_list

def get_disk_status(d = None):

    if not d:
      disk_list = get_disk_list() 
    else:
      disk_list = d

    mini_s = {}
    for dname in disk_list:
        d = {}
	#var1 = "sudo smartctl -H -i "
        var1 = "/usr/sbin/smartctl -H -i "
        #print var1
        var2 = var1 + dname
        cmd2 = os.popen(var2).read()
	lines1 = re.split("\r?\n", cmd2)
	reobj1 = re.compile(".*self-assessment.*")

        for l in lines1[:]:
	    if reobj1.search(l): 
                ent1 = re.search(r'\s[A-Z]+', l)
                d["status"] = (ent1.group()).strip()
        mini_s[dname] = d
    #print mini_s
    return mini_s

def get_disk_info(disk_list):
    dinfo_list = []	
    for dname in disk_list:
	var1 = "/usr/sbin/smartctl -H -i "	
        var2 = var1 + dname
        cmd = os.popen(var2).read()
	lines1 = re.split("\r?\n", cmd)
	reobj1 = re.compile("(.*Number:.*)")
	
	# To get the storage capacity of each disk
	st1 = os.popen("/sbin/fdisk -l | grep Disk")
        str2 = st1.read()
	disk_capacity = re.search(r'\s[0-9]+\.[0-9]\s[a-zA-Z]+',str2)
	
	mini_d = {}
	for l in lines1[:]:
	    if reobj1.search(l):
	        ent2 = re.search(r'\d+\w+', l)
                mini_d["name"] = dname
                mini_d["serial_number"] = ent2.group()
                mini_d["capacity"] = (disk_capacity.group()).strip()
	dinfo_list.append(mini_d)
    return dinfo_list				

def all_disk_list():

    op = (os.popen("zpool list -H | awk {'print $1'} ").read()).strip("\n \n")
    pool_list = op.split()
    list_disk_info = []

    list_associated_disk = []
    pool_names = {}
    for pool_name in pool_list:
        command = "zpool list -v" + " " + pool_name
        zpool_op = os.popen(command).read()
        zpool_list = zpool_op.split("\n")

        for i in zpool_list:
            result = re.search('^\s+[a-zA-Z0-9_-]+',i)
            if result is not None:
                list_associated_disk.append( result.group().lstrip(" "))
                pool_names[pool_name] = result.group().lstrip(" ")

    #print "list_associated_disk :", list_associated_disk
    #print "pool_names : ", pool_names

    for l in list_associated_disk:
        dict_disk_info = {}
        dict_disk_info["id"] = l

        # To get the pool name
        for k, v in pool_names.items():
            if l == pool_names[k]:
                dict_disk_info["pool_name"] = k

        # To get the storage capacity of each disk
        st1 = os.popen("/sbin/fdisk -l | grep Disk")
        str2 = st1.read()
        disk_capacity = re.search(r'\s[0-9]+\.[0-9]\s[a-zA-Z]+',str2)
        dict_disk_info["capacity"] = (disk_capacity.group()).strip()
        list_disk_info.append(dict_disk_info)
        
        # To get the serial number
        disk_list = get_disk_list()
        #print "disk_list :", disk_list
        for dname in disk_list:
            var1 = "/usr/sbin/smartctl -H -i "
            var2 = var1 + dname
            cmd = os.popen(var2).read()
            lines1 = re.split("\r?\n", cmd)
            reobj1 = re.compile("(.*Number:\s+.*)")
            for item in lines1:
                if reobj1.search(item):
                    #ent2 = re.search(r'\w+\d+',item)
                    ent2 = re.search(r'Serial Number:\s+[A-Z0-9a-z]+',item)
                    serial_number = ent2.group().strip("Serial Number:")
                    #print "serial_number: ", serial_number
                    dict_disk_info["serial_number"] = serial_number.strip(" ")
                    
            #print "l.split: ", l.split("_")

            # The below code is extracting Serial Numbers from the /dev/disk/by-id - entry
            # For the case in which the pool may be a part of hard disk!
            """for l in l.split("_"):
                pattern = re.search("[A-Z0-9a-z]+-[a-z0-9]+", l)
                if pattern is not None:
                    #print "pattern: ", pattern.group()
                    if serial_number in (pattern.group()).split("-"):
                        dict_disk_info["serial_number"] = serial_number.strip(" ")

            # For the case the pool may be a entire hard disk!
            if serial_number in l.split("_"):
                dict_disk_info["serial_number"] = serial_number.strip(" ")
            """
    #print list_disk_info
    return list_disk_info
    

def get_interface_status():
    in_face ={}
    for dir in glob.glob('/sys/class/net/eth*'):
        cmd1 = "cat "+ dir + "/operstate"
        res = os.popen(cmd1).read()
        #print dir
        dir_name = dir[len('/sys/class/net/'):]
        #print dir_name
        in_face [dir_name] = {}
        in_face [dir_name]['status'] = res.strip('\n')
    return in_face

def get_interface_info():

    op = os.popen('/sbin/ifconfig -a | cut -c 1-8 | sort | uniq -u').read()
    ilist = op.split()

    dict1 = {}
    for i in ilist:
        if i == 'lo':
            #ilist.remove()
            continue
        cmd = "ifconfig"+ " " + i
        res = os.popen(cmd).read()
        lines = re.split("\r?\n", res)
        
        dict1[i] = {}
        reobj1 = re.compile("inet addr:")         
        reobj2 = re.compile(".*Bcast:.*")
        reobj3 = re.compile(".*Mask:.*")
        
        for l in lines:
            if reobj1.search(l):
                try:
                    ent1 = re.search('([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', l) 
                    dict1[i]['ip'] = ent1.group()

                    """if input_ip is not None:
                        if ent1.group() == input_ip:
                            dict1[i]['active_ip'] = True
                        else: 
                            dict1[i]['active_ip'] = False
                    else:
                        print "Active_ip is not specified, explicitly." 
                    """

                except TypeError:
                    print "Pattern not Found" 

            if reobj2.search(l):
                try:
                    ent2 = re.search(r'\sBcast:([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', l)   
                    new_ent2 = ent2.group().lstrip(' Bcast:')
                    dict1[i]['bcast'] = new_ent2 
                except TypeError:
                    print "Pattern Match no found"

            if reobj3.search(l):
                try:
                    ent3 = re.search(r'\sMask:([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', l) 
                    new_ent3 = ent3.group().lstrip(' Mask: ')
                    dict1[i]['mask'] = new_ent3
                except TypeError:
                    print "Pattern Not Found "
    return dict1
   
   
def get_cpu_status():
    str_t = os.popen("/usr/bin/ipmitool sdr | grep \"Temp\" ").read()
    lines = re.split("\r?\n", str_t)
    temp_dict = {}

    reobjt = re.compile("(CPU Temp\s)")
    for line in lines[:]:
        if reobjt.search(line):
            ent1 = re.search(r'\d+\s[a-zA-Z]+\s[C]', line)
            ent2 = re.search(r'\|\s[a-zA-Z]+', line)
            ent2_1= (ent2.group()).lstrip('|')
            #print ent1.group()
            #print ent2_1.strip()
            temp_dict["status"] = ent2_1.strip()
            temp_dict["temp"] = ent1.group()
    return temp_dict


def get_quanta_cpu_status():
    str_t = os.popen("/usr/bin/ipmitool sdr | grep Temp ").read()
    lines = re.split("\r?\n", str_t)
    temp_dict = {}

    reobjt = re.compile("(CPU Temp\s)")
    for line in lines[:]:
        if reobjt.search(line):
            ent1 = re.search(r'\d+\s[a-zA-Z]+\s[C]', line)
            ent2 = re.search(r'\|\s[a-zA-Z]+', line)
            ent2_1= (ent2.group()).lstrip('|')
            #print ent1.group()
            #print ent2_1.strip()
            temp_dict["status"] = ent2_1.strip()
            temp_dict["temp"] = ent1.group()
    return temp_dict





def get_temp_status():
    st4 = os.popen("/usr/bin/ipmitool sdr | grep \"Temp\" ")
    str4 = st4.read()
    #print str4
    lines = re.split("\r?\n", str4)
    list_T = []
    temp_dict = {}

    reobjT = re.compile("(Temp_CPU0\s)")
    for line in lines[:]:
        if reobjT.search(line):
            ent1 = re.search(r'\d+\s[a-zA-Z]+\s[C]', line)
            ent2 = re.search(r'\|\s[a-zA-Z]+', line)
            ent2_1= (ent2.group()).lstrip('|')
            temp_dict["status"] = ent2_1.strip()
            temp_dict["temp"] = ent1.group()
            list_T.append(temp_dict)
    return temp_dict

def get_fan_status():
    st4 = os.popen("/usr/bin/ipmitool sdr | grep Fan ")
    str1 = st4.read()

    lines = re.split("\r?\n", str1)
    fan_dict = {}
    reobj = re.compile("Fan_*")
    for l in lines[:]:
        if reobj.search(l):
            ent1 = re.search(r'[a-zA-Z]+_[A-Z0-9]+_[0-9]', l)
            #print ent1.group()

            ent2 = re.search(r'\|\s[0-9]+\s[A-Z]+', l)
            #print (ent2.group()).lstrip('| ')
            ent3 = re.search(r'\s\|\s[a-z]+', l)
            #print ent3.group().lstrip('| ')

            fan_dict [ent1.group()] = {}
            fan_dict [ent1.group()]['rpm'] = ent2.group().lstrip('| ')
            fan_dict [ent1.group()]['status'] = ent3.group().lstrip('| ')
    return fan_dict

def get_psu_status():
    st1 = os.popen("/usr/bin/ipmitool sdr | grep PSU ")
    str1 = st1.read()

    lines = re.split("\r?\n", str1)
    psu_dict = {}
    reobj = re.compile("PSU[0-9]_*")
    for l in lines[:]:
        if reobj.search(l):
            ent1 = re.search(r'[a-zA-Z0-9]+_[A-Za-z]+', l)
            #print ent1.group()

            ent2 = re.search(r'\|\s[0-9a-z]+', l)
            #print ent2.group().lstrip('| ')
            ent3 = re.search(r'\s\|\s[a-z]+', l)
            #print ent3.group().lstrip('| ')

            psu_dict [ent1.group()] = {}
            psu_dict [ent1.group()]['code'] = ent2.group().lstrip('| ')
            psu_dict [ent1.group()]['status'] = ent3.group().lstrip('| ')
    return psu_dict

if __name__ == "__main__":
    disk_list = []
    disk_list = get_disk_list()
    print get_disk_list()
    print get_disk_status(disk_list)
    print "all_disk_list: ", all_disk_list()
    print get_interface_status()
    print "get_cpu_status() : ", get_cpu_status()
    print get_quanta_cpu_status()
    #print get_temp_status()
    #print get_fan_status()
    #print get_psu_status()
    #print get_disk_info(disk_list)
    print get_interface_info()
    sys.exit()
