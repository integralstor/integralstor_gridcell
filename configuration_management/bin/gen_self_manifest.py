#!/usr/bin/python

import os
import re
import json

import system_status
import host_info

def gen_manifest():
    newdict = {}
    newdict [host_info.get_host_name()] = {}
    temp_list1 = system_status.get_disk_list()
    #newdict [host_info.get_host_name()]['disk_info'] = system_status.get_disk_info(temp_list1)
    newdict [host_info.get_host_name()]['disk_info'] = system_status.all_disk_list()
    newdict [host_info.get_host_name()]['interface_info'] = system_status.get_interface_info()
    
    #print "newdict : ", newdict
    with open('/config/self.manifest', 'w') as of:
        json.dump(newdict, of, sort_keys=True, indent=2) 

if __name__ == '__main__':
    gen_manifest()
