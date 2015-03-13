

import re, random, sys, os

import fractalio
from fractalio import filesize, command, networking, xml_parse, common

import gluster_commands

production = common.is_production()

def get_components(brick):
  if not brick:
    return None
  l = brick.split(':')
  if len(l) == 1:
    return None
  d = {}
  d["host"] = l[0]
  d["path"] = l[1]
  l1 = l[1].split('/')
  if len(l1) == 1:
    return None
  d["pool"] = l1[1]
  d["ondisk_storage"] = l1[2]
  return d

def get_volume_info_all():

  vl = _get_volume_list(production)
  for v in vl:
    if "options" in v :
      for o in v["options"]:
        if "features.quota" == o["name"]:
          if o["value"]  == "on":
            v["quotas"] = gluster_commands.get_volume_quotas(v["name"]) 
  return vl

def _get_volume_list(production):

  d = gluster_commands.run_gluster_command("/usr/sbin/gluster volume info all --xml", "%s/b.xml"%common.get_devel_files_path(), "Getting volume info")
  if not d or  "op_status" not in d or ("op_status" in d and d["op_status"]["op_ret"] != 0):
    err = "Error getting the volume infomation : "
    if d:
      if "error_list" in d:
        err += " ".join(d["error_list"])
      if "op_status" in d and "op_errstr" in d["op_status"]:
        if d["op_status"]["op_errstr"]:
          err += d["op_status"]["op_errstr"]
    raise Exception(err)
  via_tree = d["tree"]
  admin_vol_name = common.get_admin_vol_name()
  vl = xml_parse.get_volume_list(via_tree, admin_vol_name)

  for vol in vl:
    if vol["status"] != 1:
      continue      
    d = gluster_commands.run_gluster_command("/usr/sbin/gluster volume status %s detail --xml"%vol["name"], "%s/volume_status_detail.xml"%common.get_devel_files_path(), "Getting volume status details")
    if not d or  "op_status" not in d or ("op_status" in d and d["op_status"]["op_ret"] != 0):
      err = "Error getting the volume status details: "
      if d:
        if "error_list" in d:
          err += " ".join(d["error_list"])
        if "op_status" in d and "op_errstr" in d["op_status"]:
          if d["op_status"]["op_errstr"]:
            err += d["op_status"]["op_errstr"]
      raise Exception(err)
    vsd_tree = d["tree"]
    bd, num_up, num_down = xml_parse.get_brick_status(vsd_tree)
    vol["brick_status"] = bd

    size_total = 0
    size_free = 0
    if vol["replica_count"] > 1:
      replica_set_status = []
      for br in vol["bricks"] :
        counted = False
        num_down = 0
        num_up = 0
        for  b in br:
          if b not in bd:
            #Could happen if a brick is down
            #return None
            continue
          if bd[b]["status"] == 1:
            num_up += 1
            if not counted:
              #Found one up replica so only consider size info for this. If all down then it does not count
              size_free += bd[b]["size_free"]
              size_total += bd[b]["size_total"]
              counter = True
          else:
            num_down += 1
          replica_set_status.append(num_down)
      #print replica_set_status
      if num_up == 0:
        vol["data_access_status"] = "Volume down. No data accessible!"
        vol["data_access_status_code"] = -1
      else:
        if max(replica_set_status) == vol["replica_count"]:
          vol["data_access_status"] = "Some data inaccessible"
          vol["data_access_status_code"] = -1
        elif max(replica_set_status) > 0:
          num_more = vol["replica_count"] - max(replica_set_status)
          vol["data_access_status"] = "Data accessible but vulnerable. Loss of %d more data locations will cause data loss"%num_more
          vol["data_access_status_code"] = 1
        else:
          vol["data_access_status"] = "Healthy"
          vol["data_access_status_code"] = 0
    else:
      #Distributed so count em all
      num_down = 0
      for b in bd.keys():
        if bd[b]["status"] == 1:
          num_up += 1
          size_free += bd[b]["size_free"]
          size_total += bd[b]["size_total"]
        else:
          num_down += 1
      if num_down > 0:
        vol["data_access_status"] = "Some data inaccessible"
        vol["data_access_status_code"] = 1
      else:
        vol["data_access_status"] = "Healthy"
        vol["data_access_status_code"] = 0
    vol["size_total"] = filesize.naturalsize(size_total)
    vol["size_used"] = filesize.naturalsize(size_total-size_free)
    vol["size_free"] = filesize.naturalsize(size_free)
    #print size_total-size_free
    #print (size_total-size_free)/float(size_total)
    if size_total > 0:
      vol["size_used_percent"] = int(((size_total-size_free)/float(size_total)) * 100)
    else:
      vol["size_used_percent"] = -1
    #print vol["size_used_percent"]


    # Now get the status of the self heal and NFS servers for each node
    d = gluster_commands.run_gluster_command("/usr/sbin/gluster volume status %s --xml"%vol["name"], "%s/volume_status.xml"%common.get_devel_files_path(), "Getting volume status")
    if not d or  "op_status" not in d or ("op_status" in d and d["op_status"]["op_ret"] != 0):
      err = "Error getting the volume status : "
      if d:
        if "error_list" in d:
          err += " ".join(d["error_list"])
        if "op_status" in d and "op_errstr" in d["op_status"]:
          if d["op_status"]["op_errstr"]:
            err += d["op_status"]["op_errstr"]
      raise Exception(err)
    vs_tree = d["tree"]
    vol = xml_parse.get_volume_process_status(vs_tree, vol)

  return vl



def volume_exists(vil, vol_name):

  if not vil:
    vil = get_volume_info_all()
  for v in vil:
    if v["name"] == vol_name:
      return True
    else:
      return False

def get_volume_info(vil, vol_name):

  if not vil:
    vil = get_volume_info_all()
  vol = None
  if vil:
    for v in vil:
      if v["name"] == vol_name:
        vol = v
        break
  return vol

def get_volumes_on_node(hostname, vil):
  #Returns a list of volume names on a node for display

  if not hostname:
    return None

  if not vil:
    vil = get_volume_info_all()

  if not vil:
    return []

  vol_list = []
  for vol in vil:
    bl = get_brick_hostname_list(vol)
    if hostname in bl:
      vol_list.append(vol["name"])
  return vol_list

def get_snapshots(vol_name):

  prod_command = 'gluster snapshot info volume %s  --xml'%vol_name
  dummy_command = "%s/view_snapshots.xml"%common.get_devel_files_path()
  d = gluster_commands.run_gluster_command(prod_command, dummy_command, "Starting volume %s"%vol_name)
  l = None
  if d:
    if d["op_status"]["op_ret"] == 0:
      l = xml_parse.get_snapshots(d["root"])
  return l


def get_brick_hostname_list(vol_dict):

  l = []
  for brick in vol_dict["bricks"]:
    for ib in brick:
      h, b = ib.split(':')
      if h not in l:
        l.append(h)

  return l

def set_volume_options(cd):

  vol_name = cd["vol_name"]
  auth_allow = cd["auth_allow"]
  auth_reject = cd["auth_reject"]
  if "nfs_disable" in cd:
    nfs_disable = cd["nfs_disable"]
  else:
    nfs_disable = False
  if "enable_worm" in cd:
    enable_worm = cd["enable_worm"]
  else:
    enable_worm = False
  readonly = cd["readonly"]
  nfs_volume_access = cd["nfs_volume_access"]

  vol_dict = get_volume_info(None, vol_name)

  #set defaults first
  _auth_allow = "*"
  _auth_reject = "NONE"
  _readonly = "off"
  _nfs_disable = False
  _enable_worm = False
  _nfs_volume_access = "read-write"

  if "options" in vol_dict:
    for option in vol_dict["options"]:
      if option["name"] == "auth.allow": 
        _auth_allow = option["value"]
      if option["name"] == "auth.reject": 
        _auth_reject = option["value"]
      if option["name"] == "nfs.disable": 
        if option["value"].lower() == "off":
          _nfs_disable = False
        else:
          _nfs_disable = True
      if option["name"] == "nfs.volume-access": 
        _nfs_volume_access = option["value"]
      if option["name"] == "features.read-only": 
        _readonly = option["value"]
      if option["name"] == "features.worm": 
        if option["value"].lower() == "enable":
          _enable_worm = True
        else:
          _enable_worm = False
    
  # Now, for each option that has changed, set the parameter
  ret_list = []

  if _auth_allow != auth_allow:
    d = _set_volume_option(vol_name, "auth.allow", auth_allow, "Setting option for permitted access IP addresses for %s to \'%s\'"%(vol_name, auth_allow))
    ret_list.append(d)
  if _auth_reject != auth_reject:
    d = _set_volume_option(vol_name, "auth.reject", auth_reject, "Setting option for denied access IP addresses for %s to \'%s\'"%(vol_name, auth_reject))
    ret_list.append(d)
  if _readonly != readonly:
    d = _set_volume_option(vol_name, "features.read-only", readonly, "Setting readonly mount access(for all access methods) for %s to \'%s\'"%(vol_name, readonly))
    ret_list.append(d)
  if readonly == "off":
    #All the rest applies only if volume access is read-write
    if _nfs_disable != nfs_disable:
      if nfs_disable:
        p = "on"
      else:
        p = "off"
      d = _set_volume_option(vol_name, "nfs.disable", p, "Setting NFS disable for %s to \'%s\'"%(vol_name, p))
      ret_list.append(d)
    if not nfs_disable:
      print "in"
      if nfs_volume_access and _nfs_volume_access != nfs_volume_access:
        d = _set_volume_option(vol_name, "nfs.volume-access", nfs_volume_access, "Setting NFS access type for %s to \'%s\'"%(vol_name, nfs_volume_access))
        ret_list.append(d)
    if _enable_worm != enable_worm:
      if enable_worm:
        p = "enable"
      else:
        p = "disable"
      d = _set_volume_option(vol_name, "features.worm", p, "Setting feature WORM for %s to \'%s\'"%(vol_name, p))
      ret_list.append(d)
  return ret_list

def _set_volume_option(vol_name, option, value, display_command):
  prod_command = 'gluster volume set %s %s %s --xml'%(vol_name, option, value)
  #dummy_command = "/home/bkrram/Documents/software/Django-1.4.3/code/gluster_admin/gluster_admin/utils/test/set_vol_options.xml"
  dummy_command = "%s/set_vol_options.xml"%common.get_devel_files_path()
  d = gluster_commands.run_gluster_command(prod_command, dummy_command, display_command)
  return d



def main():

  #vl = get_volume_list()
  #print "Volume list :"
  #print vl
  #get_volume_status("test")
  #get_volume_info()
  print get_volume_info_all()


if __name__ == "__main__":
  main()


'''
def get_removable_sled_list(scl, vil):
  #Return a list of sleds that can be chosen to be removed - a sled can be removed if both its nodes are in the cluster and no volumes have bricks on either node
  i = 0
  sl = []
  while i < len(scl):
    free_sled = True
    if len(get_volumes_on_node(scl[i], vil))>0 or len(get_volumes_on_node(scl[i+1], vil))>0:
      free_sled = False
    if free_sled and ((scl[i]["in_cluster"]) or (scl[i+1]["in_cluster"])):
      sl.append((i/2) +1)
    i = i+2
  return sl
def get_expandable_node_list(si, vol, replicated, replica_count):

  # If distributed then return all nodes where volume is not present
  # If replicated, then return sets of nodes where the volume is not present

  d = {}
  nl = []
  dl = []
  if replicated:
    pass
  else:
    for hostname in si.keys():
      if si[hostname]["node_status"] != 0:
        continue
      if vol["name"] in si[hostname][volume_list]:
        continue
      nl.append(hostname)
  d["node_list"]
  return nl
  
def get_expandable_lists(scl, vol, count):
  #Returns a list of nodes and sleds that qualify for expansion of a volume

  if not scl:
    scl = system_info.load_system_config()

  node_list = []
  sled_list = []
  for i in xrange(0, len(scl), 2):
    if not scl[i]["in_cluster"]:
      continue
    part_of_vol = False
    for j in xrange(2):
      for brick in vol["bricks"]:
        if "hostname" in scl[i+j] and brick["host"] == scl[i+j]["hostname"]:
          part_of_vol = True
          break
      if part_of_vol:
        break
    if not part_of_vol:
      sled_list.append(i)

  # Randomly try and use the sleds from either direction to increase uniformity. This is because the spare sled may leave one sled out
  toss = random.randint(0,1)
  if toss == 0:
    sled_list = sled_list[::-1]

  # Can only expand if there are a multiple of count sleds. Otherwise do not allow
  expandable = True
  if len(sled_list) == 0:
    expandable = False

  if vol["type"] == "Replicate":
    if len(sled_list) == 0 or len(sled_list)/count == 0:
      expandable = False


  if not expandable:
    return None

  if vol["type"] == "Distribute":
    for i in xrange(len(sled_list)):
      if "hostname" in scl[sled_list[i]] and  "hostname" in scl[sled_list[i]+1] :
        node_list.append(scl[sled_list[i]]["hostname"])
        node_list.append(scl[sled_list[i]+1]["hostname"])
  else:
    base = 1
    end = base + count -1
    while end <= len(sled_list) :
      node = random.randint(0,1)
      for i in xrange(count):
        if "hostname" in scl[sled_list[base-1+i]+node]:
          b = scl[sled_list[base-1+i]+node]["hostname"]
          node_list.append(b)
      base = base + count
      end = end + count

  d = {}
  d["node_list"] = node_list
  d["sled_list"] = sled_list
  return d

def get_replacement_sled_info(scl, vil):

  #Fill src_sled_list and dest_sled_list
  i = 0
  src_sled_list = []
  dest_sled_list = []
  while i < len(scl):
    vols_in_sled = False
    if (not scl[i]["active"]) or (not scl[i+1]["active"]) or (not scl[i]["in_cluster"]) or (not scl[i+1]["in_cluster"]):
      i = i+2
      continue
    for vol in vil:
      for brick in vol["bricks"]:
        if "hostname" in scl[i] and  "hostname" in scl[i+1] :
          if brick["host"] in [scl[i]["hostname"], scl[i+1]["hostname"]]:
            vols_in_sled = True
            break
      if vols_in_sled:
        break
    if not vols_in_sled:
      dest_sled_list.append((i/2) + 1)
    else:
      src_sled_list.append((i/2) + 1)
    i = i+2
  d = {}
  d["src_sled_list"] = src_sled_list
  d["dest_sled_list"] = dest_sled_list
  return d
'''
