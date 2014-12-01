#!/usr/bin/python

import os
import subprocess
import re
import fractalio
from fractalio import zfs, command, hardware_utils


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
  fractalio.hardware_utils.rescan_drives()

  pool_list = zfs.get_pool_list()
  #print pool_list


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
    d = {}
    if reg_exp_dl.search(line):
      result_dl = re.search(r'/dev/sd[a-z]', line)
      result_dl1 = re.search(r'/dev/(sd[a-z])', line)
      if result_dl:
        d["full_path"] = result_dl.group()
        dname = result_dl1.groups()[0]
        r = re.match('^sd[a-z]', dname)
        d["name"] = r.group()
        dl.append(d)
      else:
        print "No disk list pattern match found"
 
  #print "disk list info: ", dl
  id_dict = {}
  for (dirpath, dirnames, filenames) in os.walk('/dev/disk/by-id'):
    #print dirpath
    #print dirnames
    #print filenames
    for file in filenames:
      if "scsi-SATA" not in file:
        continue
      #print file
      #print "%s/%s"%(dirpath, file)
      #print os.readlink("%s/%s"%(dirpath, file))
      if os.path.islink("%s/%s"%(dirpath,file)):
        realpath = os.path.normpath(os.path.join(os.path.dirname("%s/%s"%(dirpath, file)), os.readlink("%s/%s"%(dirpath,file)) ) )
        id_dict[realpath] = file
        #realpath = os.path.realpath(os.readlink("%s/%s"%(dirpath,file)))
        #print realpath
  #print id_dict

  return_dict = {}
  #print dl
  for disk_name_dict in dl:
      
    disk_info_dict = {}
    disk_info_dict["rotational"] = False
    if os.path.isfile('/sys/block/%s/queue/rotational'%disk_name_dict["name"]):
      with open ('/sys/block/%s/queue/rotational'%disk_name_dict["name"]) as f:
        str = f.read()
        if str.strip() == "1":
          disk_info_dict["rotational"] = True
    cmd_disk = "/usr/sbin/smartctl -H -i" + " " + disk_name_dict["full_path"] 
    dl_output = os.popen(cmd_disk).read()
    lines = re.split("\r?\n", dl_output)

    reobj1 = re.compile("(.*Number:.*)")
 
    # To get the storage capacity of each disk
    st1 = os.popen("/sbin/fdisk -l %s | grep Disk"%disk_name_dict["full_path"])
    str2 = st1.read()
    disk_capacity = re.search(r'\s[0-9]+\.[0-9]\s[a-zA-Z]+',str2)
 
    for line in lines:
      #print line
      if reobj1.search(line):
        serial_number = re.search(r':\s+\S+', line)
        disk_info_dict['orig_name'] = disk_name_dict["full_path"]
        #disk_info_dict['serial_number'] = serial_number.group().strip(": ")
        serial_number = serial_number.group().strip(": ")
        disk_info_dict['capacity'] = (disk_capacity.group()).strip()

    '''
    if disk_name_dict["name"] in pool_names:
      disk_info_dict["pool"] = pool_names[disk_name_dict["name"]]
    else:
      disk_info_dict["pool"] = None
    '''

    #print disk_info_dict["name"]
    if disk_info_dict["orig_name"] in id_dict:
      disk_info_dict["id"] = id_dict[disk_info_dict["orig_name"]]

    found_pool = False
    for pool in pool_list:
      for component in pool["config"]["components"]:
        if component["name"] == disk_info_dict["id"]:
          disk_info_dict["pool"] = pool["config"]["pool_status"]["name"]
          found_pool = True
          break
      if found_pool:
        break

    return_dict[serial_number] = disk_info_dict
    #disk_info_list.append(disk_info_dict) 

  #print disk_info_list

  if return_dict:
    grains['disks'] = return_dict
  else:
    grains['disks'] = {}
    #grains['disk_info'] = "Can't populate disk list Information"

  return grains
  
if __name__ == '__main__':
  print diskinfo() 
