#!/usr/bin/python

import salt.client
import json, os, shutil, datetime
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
    node_status = "Healthy"

    if hostname not in sd:
      node_status = "No response. Down?"
    else:

      # Process disk information
      disks = []
      for disk in d["disk_info"]:
        dd = {} 
        disk_sn = disk["serial_number"]
        if disk_sn in sd[hostname]["disk_status"]:
          dd["status"] = sd[hostname]["disk_status"][disk_sn]["status"] 
          if dd["status"] != 'PASSED':
            node_status = "Degraded"
            temp_d["errors"].append("Disk with serial number %s on node %s is reporting SMART errors."%(disk_sn, hostname))
          dd["disk_name"] = sd[hostname]["disk_status"][disk_sn]["disk_name"] 
          dd["serial_number"] = disk_sn
        else:
          dd["status"] = "Disk Missing"
          node_status = "Degraded"
          temp_d["errors"].append("Disk with serial number %s on node %s seems to be missing."%(disk_sn, hostname))
        disks.append(dd)
      temp_d["disks"] = disks


      # Process interface information
      # TODO Capture changes in IP info and mac addr as potential errors
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

    temp_d["status"] = node_status
    if "mem_info" in sd[hostname]:
      temp_d["memory"] = sd[hostname]["mem_info"]
    if "disk_usage" in sd[hostname]:
      temp_d["disk_usage"] = sd[hostname]["disk_usage"]
    if "load_avg" in sd[hostname]:
      temp_d["load_avg"] = sd[hostname]["load_avg"]
      if temp_d["load_avg"]['15-min'] >= temp_d["load_avg"]['cpu_cores']:
        temp_d["errors"].append("The load average (%d) on node %s has been high over the past 15 minutes."%(temp_d["load_avg"]['15-min'], hostname))
        node_status = "Degraded"
      if temp_d["load_avg"]['5-min'] >= temp_d["load_avg"]['cpu_cores']:
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

  rc = gen_status('/tmp')
  print rc

if __name__ == "__main__":
  main()
