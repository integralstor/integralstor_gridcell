#!/usr/bin/python

import os
import re
import system_status 

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
   
    print "list_associated_disk :", list_associated_disk   
    print "pool_names : ", pool_names
 
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
        disk_list = system_status.get_disk_list()       
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

            #print "l.split: ", l.split("_") 
            
            # The below code is extract Serial Numbers from the /dev/disk/by-id - entry 
            # For the case in which the pool may be a part of hard disk!
            for l in l.split("_"):
                pattern = re.search("[A-Z0-9a-z]+-[a-z0-9]+", l)
                if pattern is not None:
                    print "pattern: ", pattern.group()
                    if serial_number in (pattern.group()).split("-"):
                        dict_disk_info["serial_number"] = serial_number.strip(" ")

            # For the case the pool may be a entire hard disk!  
            if serial_number in l.split("_"):
                dict_disk_info["serial_number"] = serial_number.strip(" ")
            
            
        
    #print list_disk_info
    return list_disk_info 

if __name__ == '__main__':
    print all_disk_list()
