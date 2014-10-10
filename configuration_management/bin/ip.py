#!/usr/bin/python

import os
import re
import subprocess

from command import execute, get_output_list
def getip():
  if_list = []
  dict = {}
 #print "Executing ifconfig"
  r = execute("/sbin/ifconfig -a")
 #print "After ifconfig"
  #r = execute('python /home/bkrram/Documents/software/Django-1.4.3/code/gluster_admin/gluster_admin/utils/test/test_printip.py')
  if r:
    ol = get_output_list(r)
    for i in ol:
      hw_index  = i.find("HWaddr ")
      if hw_index != -1:
        if dict:
          if_list.append(dict)
          dict = {}
        dict["mac_addr"] =  i[hw_index+7:].strip()
        #print "fractal_%s"%dict["mac_addr"][9:].replace(':', '')
        match = re.search('^([a-zA-Z_0-9]+)', i)
        if match:
          dict["if_name"] = match.group()
      ip_index  = i.find("inet addr:")
      if ip_index != -1:
        match = re.search('([0-9]+)\.([0-9]+)\.([0-9]+)\.([0-9]+)', i[ip_index:])
        ip = match.group()
        dict["ip"] = ip
      bcast_index  = i.find("Bcast:")
      if bcast_index != -1:
        match = re.search('([0-9]+)\.([0-9]+)\.([0-9]+)\.([0-9]+)', i[bcast_index:])
        bcast = match.group()
        dict["bcast"] = bcast
      mask_index  = i.find("Mask:")
      if mask_index != -1:
        match = re.search('([0-9]+)\.([0-9]+)\.([0-9]+)\.([0-9]+)', i[mask_index:])
        mask = match.group()
        dict["mask"] = mask
  if dict and dict not in if_list:
    if_list.append(dict)
  return if_list      

if __name__ == '__main__':
  print getip()
