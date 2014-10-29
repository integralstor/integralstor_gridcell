#!/usr/bin/python

import salt.client
import json, os, shutil, datetime, sys
import lock

def _gen_status_info(path):

  # First load the status from all nodes
  local = salt.client.LocalClient()
  sd = local.cmd('*', 'fractalio.status')
  if not sd:
    return -1, None
  #print "Salt returned status"
  #print sd

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

  # Match the status against the manifest entries for discrepencies
  for hostname, d in md.items():
    temp_d = {}
    temp_d["errors"] = []
    node_status = 0

    if hostname not in sd:
      node_status = -1
    else:

      # Process disk information
      disks = []
      for disk in d["disk_info"]:
        dd = {} 
        disk_sn = disk["serial_number"]
        dd["serial_number"] = disk_sn
        dd["capacity"] = disk["capacity"]
        if disk_sn in sd[hostname]["disk_status"]:
          dd["status"] = sd[hostname]["disk_status"][disk_sn]["status"] 
          if dd["status"] != 'PASSED':
            node_status = "Degraded"
            temp_d["errors"].append("Disk with serial number %s on node %s is reporting SMART errors."%(disk_sn, hostname))
          dd["disk_name"] = sd[hostname]["disk_status"][disk_sn]["disk_name"] 
        else:
          dd["status"] = "Disk Missing"
          node_status = "Degraded"
          temp_d["errors"].append("Disk with serial number %s on node %s seems to be missing."%(disk_sn, hostname))
        disks.append(dd)
      for td in sd[hostname]["disk_status"].keys():
        new_disk = True
        for ad in d["disk_info"]:
          if ad["serial_number"] == td:
            new_disk = False
            break
        if new_disk:
          temp_d["errors"].append("New disk detected. Disk with serial number %s on node %s seems to be new."%(td, hostname))
          node_status = 2
      temp_d["disks"] = disks


      # Process interface information
      interfaces = []
      for ifname, ifdict in d["interface_info"].items():
        id = {}
        if ifname in sd[hostname]["interface_status"]:
          if sd[hostname]["interface_status"][ifname]["up"]:
            id["status"] = "up"
          else:
            id["status"] = "down"
          if not sd[hostname]["interface_status"][ifname]["up"] :
            node_status = "Degraded"
            temp_d["errors"].append("Interface %s on node %s is not up."%(ifname, hostname))
          id["if_name"] = ifname
          if "inet" in sd[hostname]["interface_status"][ifname]:
            id["inet"] = sd[hostname]["interface_status"][ifname]["inet"]
          id["hwaddr"] = sd[hostname]["interface_status"][ifname]["hwaddr"]
          
        else:
          id["status"] = "Interface Missing"
          node_status = "Degraded"
          temp_d["errors"].append("Interface with number %s on node %s seems to be missing."%(ifname, hostname))
        interfaces.append(id)
      temp_d["interfaces"] = interfaces

    temp_d["node_status"] = node_status
    if node_status == 0:
      temp_d["node_status_str"] = "Healthy"
    elif node_status == 1:
      temp_d["node_status_str"] = "Degraded"
    elif node_status == 2:
      temp_d["node_status_str"] = "New on-node hardware detected"
    elif node_status == -1:
      node_status = "No response. Down?"
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
    status_dict[hostname]  = temp_d

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
    rc = gen_status('/home/bkrram/fractal/integral_view/integral_view/devel/config')
    print rc

if __name__ == "__main__":
  main()
