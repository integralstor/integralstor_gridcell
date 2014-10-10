#!/usr/bin/python

import os
import re
import json

#import command
#import subprocess
import system_status
import host_info

def gen_self():

  host_name = host_info.get_host_name()
  if not host_name:
    return None

  node_dict = {}

  #create a status_dict
  status_dict = {}

  #Populate disk status
  disk_status_dict = system_status.get_disk_status()
  if disk_status_dict:
    status_dict["disk_status"] = disk_status_dict

  #Populate interface status
  int_status_dict = system_status.get_interface_status()
  if int_status_dict:
    status_dict ['interface_status'] = int_status_dict

  #Populate cpu status
  cpu_status_dict = system_status.get_cpu_status()
  if cpu_status_dict:
    status_dict ['cpu_status'] = cpu_status_dict

  node_dict[host_name] = status_dict

  # Create the self.status json file
  with open('/config/self.status', 'w') as of:
      json.dump(node_dict, of, sort_keys = True, indent = 2)

if __name__ == '__main__':
   gen_self()
