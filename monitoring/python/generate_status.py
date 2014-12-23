#!/usr/bin/python

import salt.client
import json, os, shutil, datetime, sys, re
import fractalio
import pprint
from fractalio import lock

def _gen_status_info(path):

  # First load the status from all nodes
  local = salt.client.LocalClient()
  sd = local.cmd('*', 'fractalio_status.status')
  if not sd:
    print 'Did not get a response from salt'
    return -1, None
  #print "Salt returned status"
  #pp = pprint.PrettyPrinter(indent=4)
  #pp.pprint(sd)
  #print "SD Type"
  #print type(sd)


  # Load the manifest to check for discrepencies
  try :
    with open(path, 'r') as f:
      md = json.load(f)
  except Exception, e:
    print "Could not open the manifest file"
    return -1, None

  #print "Manifest file:"
  #print md

  status_dict = {}
  #for key in sd.keys():
  #  print key, len(key)

  # Match the status against the manifest entries for discrepencies
  for hostname, d in md.items():
    #print hostname, len(hostname)
    temp_d = {}
    temp_d["errors"] = []
    node_status = 0

    if hostname not in sd.keys():
      node_status = -1
      #print "Not found in sd"
    else:

      # Process disk information
      disks = {}
      for disk_sn, disk in d["disks"].items():
        dd = {} 
        #disk_sn = disk["serial_number"]
        #dd["serial_number"] = disk_sn
        #dd["capacity"] = disk["capacity"]
        if disk_sn in sd[hostname]["disks"]:
          dd["status"] = sd[hostname]["disks"][disk_sn]["status"] 
          if dd["status"] != 'PASSED':
            node_status = 1
            temp_d["errors"].append("Disk with serial number %s on node %s is reporting SMART errors."%(disk_sn, hostname))
          dd["name"] = sd[hostname]["disks"][disk_sn]["name"] 
        else:
          dd["status"] = "Disk Missing"
          node_status = 1
          temp_d["errors"].append("Disk with serial number %s on node %s seems to be missing."%(disk_sn, hostname))
        disks[disk_sn] = dd
      for td in sd[hostname]["disks"].keys():
        new_disk = True
        if td in d["disks"]:
          new_disk = False
          break
        if new_disk:
          temp_d["errors"].append("New disk detected. Disk with serial number %s on node %s seems to be new."%(td, hostname))
          node_status = 2
      temp_d["disks"] = disks


      # Process interface information
      interfaces = {}
      for ifname, ifdict in d["interfaces"].items():
        id = {}
        if ifname in sd[hostname]["interfaces"]:
          if sd[hostname]["interfaces"][ifname]["up"]:
            id["status"] = "up"
          else:
            id["status"] = "down"
          if not sd[hostname]["interfaces"][ifname]["up"] :
            node_status = 1
            temp_d["errors"].append("Interface %s on node %s is not up."%(ifname, hostname))
          #id["if_name"] = ifname
          if "inet" in sd[hostname]["interfaces"][ifname]:
            id["inet"] = sd[hostname]["interfaces"][ifname]["inet"]
          #id["hwaddr"] = sd[hostname]["interfaces"][ifname]["hwaddr"]
          
        else:
          id["status"] = "Interface Missing"
          node_status = 1
          temp_d["errors"].append("Interface with number %s on node %s seems to be missing."%(ifname, hostname))
        interfaces[ifname] = id
        #interfaces.append(id)
      temp_d["interfaces"] = interfaces

      if "mem_info" in sd[hostname]:
        if sd[hostname]["mem_info"]["mem_total"]["unit"] == "kB":
          sd[hostname]["mem_info"]["mem_total"]["value"] = str(int(sd[hostname]["mem_info"]["mem_total"]["value"])/1024)
          sd[hostname]["mem_info"]["mem_total"]["unit"] = "MB"
        if sd[hostname]["mem_info"]["mem_free"]["unit"] == "kB":
          sd[hostname]["mem_info"]["mem_free"]["value"] = str(int(sd[hostname]["mem_info"]["mem_free"]["value"])/1024)
          sd[hostname]["mem_info"]["mem_free"]["unit"] = "MB"
        temp_d["memory"] = sd[hostname]["mem_info"]
      if "disk_usage" in sd[hostname]:
        temp_d["disk_usage"] = sd[hostname]["disk_usage"]
      if "pools" in sd[hostname]:
        temp_d["pools"] = sd[hostname]["pools"]
      if "load_avg" in sd[hostname]:
        # To get around a django quirk of not recognising hyphens in dicts
        sd[hostname]["load_avg"]["15_min"] = sd[hostname]["load_avg"]["15-min"]
        sd[hostname]["load_avg"]["5_min"] = sd[hostname]["load_avg"]["5-min"]
        sd[hostname]["load_avg"]["1_min"] = sd[hostname]["load_avg"]["1-min"]
        sd[hostname]["load_avg"].pop("15-min", None)
        sd[hostname]["load_avg"].pop("5-min", None)
        sd[hostname]["load_avg"].pop("1-min", None)
        temp_d["load_avg"] = sd[hostname]["load_avg"]
        if temp_d["load_avg"]['15_min'] >= temp_d["load_avg"]['cpu_cores']:
          temp_d["errors"].append("The load average (%d) on node %s has been high over the past 15 minutes."%(temp_d["load_avg"]['15-min'], hostname))
          node_status = "Degraded"
        if temp_d["load_avg"]['5_min'] >= temp_d["load_avg"]['cpu_cores']:
          temp_d["errors"].append("The load average (%d) on node %s has been high over the past 5 minutes."%(temp_d["load_avg"]['5-min'], hostname))
  
      if "cpu_model" in d:
        temp_d["cpu_model"] = d["cpu_model"]
  
      if "fqdn" in d:
        temp_d["fqdn"] = d["fqdn"]
  
      fil = os.popen("ipmitool sdr")
      str4 = fil.read()
      lines = re.split("\r?\n", str4)
      ipmi_status = []
      for line in lines:
        l = line.rstrip()
        if not l:
          continue
        #print l
        comp_list = l.split('|')
        comp = comp_list[0].strip()
        status = comp_list[2].strip()
        if comp in["CPU Temp", "System Temp", "DIMMA1 Temp", "DIMMA2 Temp", "DIMMA3 Temp", "FAN1", "FAN2", "FAN3"] and status != "ns":
          td = {}
          td["reading"] = comp_list[1].strip()
          td["status"] = comp_list[2].strip()
          if comp == "CPU Temp":
            td["parameter_name"] = "CPU Temperature"
            td["component_name"] = "CPU"
          elif comp == "System Temp":
            td["parameter_name"] = "System Temperature"
            td["component_name"] = "System"
          elif comp == "DIMMA1 Temp":
            td["parameter_name"] = "Memory card 1 temperature"
            td["component_name"] = "Memory card 1"
          elif comp == "DIMMA2 Temp":
            td["parameter_name"] = "Memory card 2 temperature"
            td["component_name"] = "Memory card 2"
          elif comp == "DIMMA3 Temp":
            td["parameter_name"] = "Memory card 3 temperature"
            td["component_name"] = "Memory card 3"
          elif comp == "FAN1":
            td["parameter_name"] = "Fan 1 speed"
            td["component_name"] = "Fan 1"
          elif comp == "FAN2":
            td["parameter_name"] = "Fan 2 speed"
            td["component_name"] = "Fan 2"
          elif comp == "FAN3":
            td["parameter_name"] = "Fan 3 speed"
            td["component_name"] = "Fan 3"
          ipmi_status.append(td)

      temp_d["ipmi_status"] = ipmi_status

    temp_d["node_status"] = node_status
    if node_status == 0:
      temp_d["node_status_str"] = "Healthy"
    elif node_status == 1:
      temp_d["node_status_str"] = "Degraded"
    elif node_status == 2:
      temp_d["node_status_str"] = "New on-node hardware detected"
    elif node_status == -1:
      temp_d["node_status_str"] = "No response. Down?"
  
    status_dict[hostname]  = temp_d
  
    #print status_dict
  return 0, status_dict
  
def gen_status(path):
  if not lock.get_lock('generate_status'):
    print 'Generate Status : Could not acquire lock. Exiting.'
    return -1
  ret_code = 0
  fullmanifestpath = os.path.normpath("%s/master.manifest"%path)
  rc, ret = _gen_status_info(fullmanifestpath)
  if rc != 0 :
    ret_code = rc
  else:
    fullpath = os.path.normpath("%s/master.status"%path)
    fulltmppath = os.path.normpath("%s/master.status.tmp"%path)
    try:
      #Generate into a tmp file
      with open(fulltmppath, 'w') as fd:
        json.dump(ret, fd, indent=2)
      #Now move the tmp to the actual manifest file name
      shutil.move(fulltmppath, fullpath)
    except Exception, e:
      print "Error generating the status file : %s"%str(e)
      ret_code = -1
  lock.release_lock('generate_status')
  return ret_code

import atexit
atexit.register(lock.release_lock, 'generate_status')

def main():

  num_args = len(sys.argv)
  if num_args > 1:
    rc = gen_status(os.path.normpath(sys.argv[1]))
    print rc
  else:
    #rc = gen_status('/home/bkrram/fractal/integral_view/integral_view/devel/config')
    rc = gen_status('/tmp')
    print rc

if __name__ == "__main__":
  main()
