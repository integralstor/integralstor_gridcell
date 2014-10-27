
from command import get_command_output 
import xml_parse, gluster_commands

import re, random, sys, os

from django.conf import settings
from django.conf import settings

'''
sys.path.insert(0, '/opt/fractal/gluster_admin')
sys.path.insert(0, '/home/bkrram/Documents/software/Django-1.4.3/code/gluster_admin')
'''
path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '%s/../..'%path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'integral_view.settings'



def get_volume_info_all():

  vl = xml_parse.get_volume_list()
  for v in vl:
    if "options" in v :
      for o in v["options"]:
        if "features.quota" == o["name"]:
          if o["value"]  == "on":
            v["quotas"] = gluster_commands.get_volume_quotas(v["name"]) 
  return vl
#  return [{'name': 'testvol1', 'bricks': [{'path': '/data/test', 'host': '192.168.0.11'}, {'path': '/data/test', 'host': '192.168.0.12'}], 'distCount': '1', 'replicaCount': '2', 'brickCount': '2', 'stripeCount': '1', 'type': 'Replicate', 'statusStr': 'Started'}, {'name': 'testvol2', 'bricks': [{'path': '/data/test2', 'host': '192.168.0.2'}, {'path': '/data/test2', 'host': '192.168.0.1'}], 'distCount': '2', 'replicaCount': '1', 'brickCount': '2', 'stripeCount': '1', 'type': 'Distribute', 'statusStr': 'Started'}]

def get_vol_dict(vil, vol_name):
  if not vil:
    vil = get_volume_info_all()
  for v in vil:
    if v["name"] == vol_name:
      return v
  return None

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

def get_brick_hostname_list(vol_dict):

  l = []
  for brick in vol_dict["bricks"]:
    for ib in brick:
      h, b = ib.split(':')
      if h not in l:
        l.append(h)

  return l

'''
def get_human_readable_data_locations(vol_dict, scl):
  hrl = []
  bhl = get_brick_hostname_list(vol_dict)
  return bhl
  for i, node in enumerate(scl):
    if "hostname" in node and node["hostname"] in bhl:
      if i%2 == 0:
        hrl.append("Sled %d Node 1"%node["sled"])
      else:
        hrl.append("Sled %d Node 2"%node["sled"])
  return hrl
'''

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
  
'''
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

def get_replacement_node_info(si, vil):

  #Fill src_node_list and dest_node_list
  i = 0
  src_node_list = []
  dest_node_list = []
  sil = si.items()
  for hostname in si.keys():
    if si[hostname]["node_status"] != 0 :
      continue
    if not si[hostname]["in_cluster"] :
      continue
    if si[hostname]["volume_list"]:
      src_node_list.append(hostname)
    else:
      dest_node_list.append(hostname)
  d = {}
  d["src_node_list"] = src_node_list
  d["dest_node_list"] = dest_node_list
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
