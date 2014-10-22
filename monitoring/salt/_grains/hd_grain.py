#!/usr/bin/python

import os
import subprocess
import re


def command_execution(command = None):
  """ This function executes a command and returns the output in the form of a tuple.
      Exits in the case of an exception.
  """

  if command is None:
    return None

  err = ''
  args = command.split()
  try:
    output = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)

  except Exception as e:
    err = str(e)
    return err

  ret_val = output.communicate()

  if ret_val:
    return ret_val
  else:
    return err


def validate_cmd_output(output_tuple = None):
  if output_tuple is None:
    return None

  if output_tuple[0]  :
    cmd_executed = output_tuple[0]
  else:
    print "Error : %s" % output_tuple[1]
    exit (-1)

  return cmd_executed


def diskinfo():

  # Initialize a grain dictionary
  grains = {}

  # Some code for logic that sets grains like..
 
  # To get information about Hard Disk and ..
  # the list containing the info is abbreviated as "dl"
  cmd_dl = "/usr/sbin/smartctl --scan"

  output_tuple_dl = command_execution(cmd_dl)
  cmd_executed_dl = validate_cmd_output(output_tuple_dl)

  # Regex to capture "/dev/sdX"
  reg_exp_dl = re.compile("(/dev/[a-z]+)")

  dl = []
  for line in cmd_executed_dl.split('\n'):
    if reg_exp_dl.search(line):
      result_dl = re.search(r'/dev/sd[a-z]', line)
      if result_dl:
        dl.append(result_dl.group() )
      else:
        print "No disk list pattern match found"
 
  print "disk list info: ", dl

  disk_info_list = []
  for disk_name in dl:
    cmd_disk = "/usr/sbin/smartctl -H -i" + " " + disk_name 
    dl_output = os.popen(cmd_disk).read()
    lines = re.split("\r?\n", dl_output)

    reobj1 = re.compile("(.*Number:.*)")
 
    # To get the storage capacity of each disk
    st1 = os.popen("/sbin/fdisk -l | grep Disk")
    str2 = st1.read()
    disk_capacity = re.search(r'\s[0-9]+\.[0-9]\s[a-zA-Z]+',str2)
 
    disk_info_dict = {}
    for line in lines:
      if reobj1.search(line):
        serial_number = re.search(r':\s+\S+', line)
        disk_info_dict['name'] = disk_name
        disk_info_dict['serial_number'] = serial_number.group().strip(": ")
        disk_info_dict['capacity'] = (disk_capacity.group()).strip()

    disk_info_list.append(disk_info_dict) 

  #print disk_info_list

  if disk_info_list:
    grains['disk_info'] = disk_info_list
  else:
    grains['disk_info'] = []
    #grains['disk_info'] = "Can't populate disk list Information"

  return grains
  
if __name__ == '__main__':
  print diskinfo() 
