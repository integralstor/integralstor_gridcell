
from xml.etree import ElementTree
import tempfile, socket, time, random, json, sys, os

#sys.path.append('/usr/lib/python2.6/site-packages/gfapi-0.0.1-py2.6.egg')
#import gluster
#from gluster import gfapi

from django.conf import settings

import volume_info, system_info
import xml_parse, command

import fractalio

def deactivate_snapshot(snapshot_name):

  prod_command = 'gluster --mode=script snapshot deactivate  %s --xml'%snapshot_name
  dummy_command = "%s/deactivate_snapshot.xml"%settings.BASE_FILE_PATH
  #assert False
  d = run_gluster_command(prod_command, dummy_command, "Deactivating snapshot %s"%snapshot_name)
  return d

def activate_snapshot(snapshot_name):

  prod_command = 'gluster --mode=script snapshot activate  %s --xml'%snapshot_name
  dummy_command = "%s/activate_snapshot.xml"%settings.BASE_FILE_PATH
  #assert False
  d = run_gluster_command(prod_command, dummy_command, "Activating snapshot %s"%snapshot_name)
  return d

def create_snapshot(d):

  vol_name = d["vol_name"]
  snapshot_name = d["snapshot_name"]

  prod_command = 'gluster snapshot create %s  %s --xml'%(snapshot_name, vol_name)
  dummy_command = "%s/create_snapshot.xml"%settings.BASE_FILE_PATH
  #assert False
  d = run_gluster_command(prod_command, dummy_command, "Created a snapshot named %s for volume %s"%(snapshot_name, vol_name))
  return d



def remove_node(si, node):
  ol = []
  
  localhost = socket.gethostname().strip()
  if si[node]["in_cluster"] and node != localhost: 
    d = {}
    command = 'gluster peer detach %s --xml'%node
    d["actual_command"] = command
    d["command"] = "Removing node %s from the storage pool"%node
    #rd = xml_parse.run_command_get_xml_output_tree(command, "/home/bkrram/Documents/software/Django-1.4.3/code/gluster_admin/gluster_admin/utils/test/peer_detach.xml")
    rd = xml_parse.run_command_get_xml_output_tree(command, "%s/peer_detach.xml"%settings.BASE_FILE_PATH)
    if "error_list" in rd:
      d["error_list"] = rd["error_list"]
    status_dict = None
    if "tree" in rd:
      root = rd["tree"].getroot()
      status_dict = xml_parse.get_op_status(root)
      d["op_status"] = status_dict
    if status_dict and status_dict["op_ret"] == 0:
      #Success so add audit info
      d["audit_str"] = "removed node %s"%node
    ol.append(d)
  return ol


def add_servers(anl):

  sled_dict = {}
  ol = []
  sled_list = []
  localhost = socket.gethostname().strip()

  # Create a dict with the keys being sleds and values being list of nodes in the sled in order to process by sled
  #Convoluted logic in order to try and make sure that whole sleds are added and we can back out a node addition if the other node failed

  for node in anl:
    host = node["hostname"]
    status_dict = None
    if host != localhost:
      d = {}
      d["command"] = "Adding node %s to the pool"%host
      cmd = "gluster peer probe %s --xml"%host
      d["actual_command"] = cmd
      #rd = xml_parse.run_command_get_xml_output_tree(cmd, "/home/bkrram/Documents/software/Django-1.4.3/code/gluster_admin/gluster_admin/utils/test/peer_probe.xml")
      rd = xml_parse.run_command_get_xml_output_tree(cmd, "%s/peer_probe.xml"%settings.BASE_FILE_PATH)
      if "error_list" in rd:
        d["error_list"] = rd["error_list"]
      if "tree" in rd:
        root = rd["tree"].getroot()
        status_dict = xml_parse.get_op_status(root)
        d["op_status"] = status_dict

      if status_dict and status_dict["op_ret"] == 0:
        #Success so add audit info
        d["audit_str"] = "added node %s to the storage pool"%host
      ol.append(d)

  return ol


def build_create_or_expand_volume_command(command, si, anl, vol_type, ondisk_storage, repl_count, vol_name):
  
  d = {}
  node_list = []
  num_nodes = len(anl)
  #num_disks = len(si[anl[0]]["disks"])
  num_pools = len(si[anl[0]]["pools"])
  cmd = command

  count = 0
  if vol_type == "distributed":
    for hostname in anl:
      for i, pool in enumerate(si[hostname]["pools"]):
        node_list.append(["%s %s"%(hostname, pool["name"])])
        brick = "%s:/%s/%s/%s"%(hostname, pool["name"], ondisk_storage, vol_name)
        count += 1
        cmd = cmd + brick + " "
  else:
    #Replicated 
    if num_nodes < repl_count:
      d["error"] = "Insufficient number of nodes to make the replica pairs"
      return d
    pool_num = 1
    first_node = 1
    second_node = first_node + 1
    init_node = 1

    if num_nodes %2 == 0:
      #Even number of nodes
      while True:
        pool_num = 1
        nl = []
        while pool_num <= num_pools:
          node_name = anl[first_node-1]
          node = si[anl[first_node-1]]
          nl = []
          a = "node %s %s"%(node_name, node["pools"][pool_num-1]["name"])
          print a
          nl.append(a)
          brick = "%s:/%s/%s/%s"%(node_name, node["pools"][pool_num-1]["name"], ondisk_storage, vol_name)
          cmd = cmd + brick + " "
          count += 1

          node_name = anl[second_node-1]
          node = si[anl[second_node-1]]
          brick = "%s:/%s/%s/%s"%(node_name, node["pools"][pool_num-1]["name"], ondisk_storage, vol_name)
          cmd = cmd + brick + " "
          a = "node %s disk %s"%(node_name, node["pools"][pool_num-1]["name"])
          print a
          nl.append(a)
          count += 1
          pool_num += 1

          print "------------"

        node_list.append(nl)

        first_node = 1 if first_node == num_nodes else first_node + 2
        second_node = 1 if second_node == num_nodes else second_node + 2

        if second_node == 1:
          break
    else:
      #Odd number of nodes
      tl = []
      while True:
        nl = []
        node_name = anl[first_node-1]
        node = si[anl[first_node-1]]
        brick = "%s:/%s/%s/%s"%(node_name, node["pools"][pool_num-1]["name"], ondisk_storage, vol_name)
        a = "node %s disk %s"%(node_name, node["pools"][pool_num-1]["name"])
        if a in tl:
          break
        cmd = cmd + brick + " "
        count += 1
        tl.append(a)
        print a

        nl.append(a)
    
        disk_num = 1 if disk_num == num_disks else disk_num + 1
        node_name = anl[second_node-1]
        node = si[anl[second_node-1]]
        brick = "%s:/%s/%s/%s"%(node_name, node["pools"][pool_num-1]["name"], ondisk_storage, vol_name)
        cmd = cmd + brick + " "
        a = "node %s disk %s"%(node_name, node["pools"][pool_num-1]["name"])
        print a
        count += 1
        tl.append(a)
        nl.append(a)
        node_list.append(nl)
        pool_num = 1 if pool_num == num_pools else pool_num + 1
        print "------------"

        if second_node + 1 > num_nodes:
          first_node = second_node
          second_node = init_node
        else:
          first_node = second_node
          second_node = second_node + 1











  '''
  if vol_type == "distributed":
    if raid:
      #One pool per NODE so apportion accordingly
      for hostname in anl:
        node_list.append(["%s %s"%(hostname, si[hostname]["raid_pool_name"])])
        brick = "%s:/%s/%s/%s"%(hostname, si[hostname]["raid_pool_name"], ondisk_storage, vol_name)
        count += 1
        cmd = cmd + brick + " "
    else:
      #One pool per DISK so apportion accordingly
      for hostname in anl:
        for i, disk in enumerate(si[hostname]["disks"]):
          node_list.append(["%s %s"%(hostname, disk["pool"])])
          brick = "%s:/%s/%s/%s"%(hostname, disk["pool"], ondisk_storage, vol_name)
          count += 1
          cmd = cmd + brick + " "
  else:
    #Replicated volume

    if num_nodes < repl_count:
      d["error"] = "Insufficient number of nodes to make the replica pairs"
      return d

    if raid:
      #One pool per NODE so apportion accordingly
      if num_nodes % 2 != 0:
        d["error"] = "Insufficient number of nodes to make the replica pairs. Nodes can only be added in pairs."
        return d
      disk_num = 1
      first_node = 1
      second_node = first_node + 1
      init_node = 1

      while True:
        nl = []
        node_name = anl[first_node-1]
        node = si[anl[first_node-1]]
        nl = []
        a = "node %s %s"%(node_name, node["raid_pool_name"])
        print a
        nl.append(a)
        brick = "%s:/%s/%s/%s"%(node_name, node["raid_pool_name"], ondisk_storage, vol_name)
        cmd = cmd + brick + " "
        count += 1

        node_name = anl[second_node-1]
        node = si[anl[second_node-1]]
        brick = "%s:/%s/%s/%s"%(node_name, node["rai_pool_name"], ondisk_storage, vol_name)
        cmd = cmd + brick + " "
        brick = "%s:/%s/%s/%s"%(node_name, node["raid_pool_name"], ondisk_storage, vol_name)
        print a
        nl.append(a)
        count += 1
  
        node_list.append(nl)
  
        first_node = 1 if first_node == num_nodes else first_node + 2
        second_node = 1 if second_node == num_nodes else second_node + 2

        if second_node == 1:
          break
    else:
      #One pool per DISK so apportion accordingly

      disk_num = 1
      first_node = 1
      second_node = first_node + 1
      init_node = 1
  
      if num_nodes %2 == 0:
        while True:
          disk_num = 1
          nl = []
          while disk_num <= num_disks:
            node_name = anl[first_node-1]
            node = si[anl[first_node-1]]
            nl = []
            a = "node %s %s"%(node_name, node["disk"][disk_num-1]["pool"])
            print a
            nl.append(a)
            brick = "%s:/%s/%s/%s"%(node_name, node["disks"][disk_num-1]["pool"], ondisk_storage, vol_name)
            cmd = cmd + brick + " "
            count += 1
  
            node_name = anl[second_node-1]
            node = si[anl[second_node-1]]
            brick = "%s:/%s/%s/%s"%(node_name, node["disks"][disk_num-1]["pool"], ondisk_storage, vol_name)
            cmd = cmd + brick + " "
            a = "node %s disk %s"%(node_name, node["disks"][disk_num-1]["pool"])
            print a
            nl.append(a)
            count += 1
            disk_num += 1
  
            print "------------"
  
          node_list.append(nl)
  
          first_node = 1 if first_node == num_nodes else first_node + 2
          second_node = 1 if second_node == num_nodes else second_node + 2
  
          if second_node == 1:
            break
      else:
        tl = []
        while True:
          nl = []
          node_name = anl[first_node-1]
          node = si[anl[first_node-1]]
          brick = "%s:/%s/%s/%s"%(node_name, node["disks"][disk_num-1]["pool"], ondisk_storage, vol_name)
          a = "node %s disk %s"%(node_name, node["disks"][disk_num-1]["pool"])
          if a in tl:
            break
          cmd = cmd + brick + " "
          count += 1
          tl.append(a)
          print a
  
          nl.append(a)
      
          disk_num = 1 if disk_num == num_disks else disk_num + 1
          node_name = anl[second_node-1]
          node = si[anl[second_node-1]]
          brick = "%s:/%s/%s/%s"%(node_name, node["disks"][disk_num-1]["pool"], ondisk_storage, vol_name)
          cmd = cmd + brick + " "
          a = "node %s disk %s"%(node_name, node["disks"][disk_num-1]["pool"])
          print a
          count += 1
          tl.append(a)
          nl.append(a)
          node_list.append(nl)
          disk_num = 1 if disk_num == num_disks else disk_num + 1
          print "------------"
  
          if second_node + 1 > num_nodes:
            first_node = second_node
            second_node = init_node
          else:
            first_node = second_node
            second_node = second_node + 1
  '''




  d["cmd"] = cmd
  d["count"] = count
  d["node_list"] = node_list
  return d

def build_expand_volume_command(vol, si):

  d = {}

  # First get all the node/disk combinations where the volume is not present
  anl = []
  num_nodes = 0

  ondisk_storage = "normal"
  if "compressed" in vol['bricks'][0]:
    ondisk_storage = "compressed"
  elif "deduplicated" in vol['bricks'][0]:
    ondisk_storage = "deduplicated"

  for hostname in si.keys():
    if si[hostname]["node_status"] != 0 or si[hostname]["in_cluster"] == False:
      continue
    if vol["name"] in si[hostname]["volume_list"]:
      continue
    num_nodes += 1
    anl.append(hostname)

  if len(anl) < 2:
    d["error"] = "Could not find sufficient storage to expand this volume. You need atleast 2 unused nodes in order to expand a volume"
    return d

  command = 'gluster volume add-brick %s  '%vol["name"]

  repl_count = 0

  if vol["type"] in ['Replicate', 'Distributed_Replicate', 'distributed_striped_replicated', 'striped_replicated']:
    vol_type = "replicated"
    repl_count  = int(vol["replicaCount"])
  else:
    vol_type = "distributed"

  d = build_create_or_expand_volume_command(command, si, anl, vol_type, ondisk_storage, repl_count, vol["name"])

  if "cmd" in d:
    d["cmd"] = d["cmd"] + " --xml"

  return d
    
def build_create_volume_command(vol_name, vol_type, ondisk_storage, repl_count, transport, si):

  # Now build the command based on parameters provided
  command = 'gluster volume create %s '%vol_name
  if vol_type in ['replicated', 'distributed_replicated', 'distributed_striped_replicated', 'striped_replicated']:
    command = command + ' replica %d '%repl_count
    vol_type = "replicated"
  command = command + ' transport %s '%transport
  num_nodes = 0

  # Get the number of active nodes and their names
  anl = []
  for hostname in si.keys():
    if si[hostname]["node_status"] != 0 or si[hostname]["in_cluster"] == False:
      continue
    num_nodes += 1
    anl.append(hostname)

  d = {}
  if not anl:
    d["error"] = "No appropriate storage available to create the volume"
    return d

  d = build_create_or_expand_volume_command(command, si, anl, vol_type, ondisk_storage, repl_count, vol_name)
  if "cmd" in d:
    d["cmd"] = d["cmd"] + " --xml"
  return d


def create_rebalance_command_file(vol_name):
  try:
    dir = settings.BATCH_COMMANDS_DIR
  except:
    dir = "."
  if not os.path.exists(dir):
    try:
      os.mkdir(dir)
    except OSError:
      return None

  t = time.localtime()
  data = {}
  data["initiate_time"] = time.strftime("%a %b %d %H:%M:%S %Y", t)
  file_name = "%s_%d"%(time.strftime("bp_volume_rebalance_%b_%d_%Y_%H_%M_%S", t) , int(time.time()))
  full_file_name = "%s/in_process/%s"%(dir, file_name)
  data["status_url"] = "/show/batch_status_details/%s"%file_name
  data["title"] = "Volume rebalance for volume \'%s\'"%vol_name
  data["process"] = "volume_rebalance"
  data["status"] = "Not yet started"
  data["command_list"] = []
  d = {}
  d["type"] = "rebalance_start"
  d["desc"] = "Volume rebalance for volume %s - start"%vol_name
  d["command"] = "gluster volume rebalance %s start --xml"%vol_name
  d["status_code"] = 0
  data["command_list"].append(d)
  d = {}
  d["type"] = "rebalance_status"
  d["desc"] = "Volume rebalance for volume %s - status"%vol_name
  d["command"] = "gluster volume rebalance %s status --xml"%vol_name
  d["status_code"] = 0
  data["command_list"].append(d)
  try :
    with open(full_file_name, "w+") as f:
      json.dump(data, f, indent=2)
  except Exception, e:
    d["error"] = str(e)
  else:
    d["file_name"] = file_name
  return d

def create_factory_defaults_reset_file():
  try:
    dir = settings.BATCH_COMMANDS_DIR
  except:
    dir = "."
  if not os.path.exists(dir):
    try:
      os.mkdir(dir)
    except OSError:
      return None

  t = time.localtime()
  data = {}
  data["initiate_time"] = time.strftime("%a %b %d %H:%M:%S %Y", t)
  file_name = "%s_%d"%(time.strftime("bp_factory_defaults_reset_%b_%d_%Y_%H_%M_%S", t) , int(time.time()))
  full_file_name = "%s/in_process/%s"%(dir, file_name)
  data["status_url"] = "/show/batch_status_details/%s"%file_name
  data["title"] = "Reset system to factory defaults"
  data["process"] = "factory_deafults_reset"
  data["status"] = "Not yet started"
  data["command_list"] = []

  vil = volume_info.get_volume_info_all()
  scl = system_info.load_system_config()
  for v in vil:
    if v["status"] == 1:
      #Stop this volume
      d = {}
      d["type"] = "vol_stop"
      d["desc"] = "Stopping volume %s "%v["name"]
      d["command"] = 'gluster volume stop %s force --xml'%v["name"]
      d["status_code"] = 0
      data["command_list"].append(d)
  for v in vil:
    d = {}
    d["type"] = "vol_delete"
    d["desc"] = "Deleting volume %s "%v["name"]
    d["command"] = 'gluster volume delete %s force --xml'%v["name"]
    d["status_code"] = 0
    data["command_list"].append(d)
    for brick in v["bricks"]:
      for ib in brick:
        h, b = ib.split(':')
        d = {}
        d["type"] = "brick_delete"
        d["desc"] = "Deleting brick %s on %s for volume %s "%(b, h, v["name"])
        d["command"] = '/opt/fractal/bin/client rcmd rm -rf %s'%b
        d["status_code"] = 0
        data["command_list"].append(d)

  # Remove all the volume directories..

  localhost = socket.gethostname().strip()
  for hostname, n in scl.items():
    if (hostname.strip() == localhost) or (not n["in_cluster"]):
      continue
    d = {}
    d["type"] = "peer_detach"
    d["desc"] = "Removing %s from the storage pool"%hostname
    d["command"] = 'gluster peer detach %s --xml'%hostname
    d["status_code"] = 0
    data["command_list"].append(d)

  try :
    with open(full_file_name, "w+") as f:
      json.dump(data, f, indent=2)
  except Exception, e:
    d["error"] = str(e)
  else:
    d["file_name"] = file_name
  return d

def create_replace_command_file(si, vil, src_node, dest_node):

  data = {}
  data["title"] = "Replacing node %s with node %s"%(src_node, dest_node)
  data["process"] = "replace_node"
  data["volume_list"] = []
  data["command_list"] = []

  vol_list = ""
  command_list = []


  tvl = si[src_node]["volume_list"]
  for tv in tvl:
    vd = volume_info.get_volume_info(vil, tv)
    if vd["type"] == "Distribute":
      d = {}
      #c = "gluster volume replace-brick %s %s:/data/%s %s:/data/%s"%(tv, scl[n]["hostname"], tv, scl[dest_node]["hostname"], tv)
      c = "gluster volume add-brick %s %s:/data/%s --xml"%(tv, dest_node, tv)
      d["type"] = "add_brick"
      d["desc"] = "Adding volume storage in node %s for volume %s"%(dest_node, tv)
      d["command"] = c
      d["status_code"] = 0
      data["command_list"].append(d)
      d = {}
      c = "gluster --mode=script volume remove-brick %s %s:/data/%s start --xml"%(tv, src_node, tv)
      d["type"] = "remove_brick_start"
      d["desc"] = "Migrating volume storage from node %s for volume %s start"%(src_node, tv)
      d["command"] = c
      d["status_code"] = 0
      data["command_list"].append(d)
      d = {}
      c = "gluster volume remove-brick %s %s:/data/%s status --xml"%(tv, src_node, tv)
      d["type"] = "remove_brick_status"
      d["desc"] = "Migrating volume storage from node %s for volume %s status"%(src_node, tv)
      d["command"] = c
      d["status_code"] = 0
      data["command_list"].append(d)
      d = {}
      c = "gluster --mode=script volume remove-brick %s %s:/data/%s commit --xml"%(tv, src_node, tv)
      d["type"] = "remove_brick_commit"
      d["desc"] = "Migrating volume storage from node %s for volume %s commit"%(src_node, tv)
      d["command"] = c
      d["status_code"] = 0
      data["command_list"].append(d)
    else:
      #Replicated vol so for now do a replace-brick
      d = {}
      c = "gluster volume replace-brick %s %s:/data/%s %s:/data/%s commit force --xml"%(tv, src_node, tv, dest_node, tv)
      d["type"] = "replace_brick_commit"
      d["desc"] = "Replacing storage location for volume %s from node %s to node %s"%(tv, src_node, dest_node)
      d["command"] = c
      d["status_code"] = 0
      data["command_list"].append(d)
      d = {}
      c = "gluster volume heal %s full --xml"%tv
      d["type"] = "volume_heal_full"
      d["desc"] = "Migrating volume data from node %s for volume %s start"%(src_node, tv)
      d["command"] = c
      d["status_code"] = 0
      data["command_list"].append(d)
      d = {}
      c = "gluster volume heal %s info --xml"%tv
      d["type"] = "volume_heal_info"
      d["desc"] = "Migrating volume data from node %s for volume %s info"%(src_node, tv)
      d["command"] = c
      d["status_code"] = 0
      data["command_list"].append(d)

    if not tv in data["volume_list"]:
      data["volume_list"].append(tv)
  try:
    dir = settings.BATCH_COMMANDS_DIR
  except:
    dir = "."

  if not os.path.exists(dir):
    try:
      os.mkdir(dir)
    except OSError:
      return None

  t = time.localtime()
  data["status"] = "Not yet started"
  data["initiate_time"] = time.strftime("%a %b %d %H:%M:%S %Y", t)
  file_name = "%s_%d"%(time.strftime("bp_replace_node_%b_%d_%Y_%H_%M_%S", t) , int(time.time()))
  full_file_name = "%s/in_process/%s"%(dir, file_name)
  data["status_url"] = "/show/batch_status_details/%s"%file_name
  d = {}
  try:
    with open(full_file_name, "w+") as f:
      json.dump(data, f, indent=2)
  except Exception, e:
    d["error"] = str(e)
  else:
    d["file_name"] = file_name
  return d

def expand_volume(vol_name, hosts):

  d = {}
  brick_name = None
  for host in hosts:
    if brick_name:
      brick_name = brick_name+ " " + "%s:/data/%s"%(host, vol_name)
    else:
      brick_name = "%s:/data/%s"%(host, vol_name)
  command = 'gluster volume add-brick %s %s --xml'%(vol_name, brick_name)
  d['actual_command'] = command
  #rd = xml_parse.run_command_get_xml_output_tree(command, "/home/bkrram/Documents/software/Django-1.4.3/code/gluster_admin/gluster_admin/utils/test/add_brick.xml")
  rd = xml_parse.run_command_get_xml_output_tree(command, "%s/add_brick.xml"%settings.BASE_FILE_PATH)
  if "error_list" in rd:
    d["error_list"] = rd["error_list"]
  status_dict = None
  if "tree" in rd:
    root = rd["tree"].getroot()
    status_dict = xml_parse.get_op_status(root)
    d["op_status"] = status_dict
  return d


def volume_stop_or_start(vol_name, op):

  prod_command = 'gluster --mode=script volume %s %s --xml'%(op, vol_name)
  #dummy_command = "/home/bkrram/Documents/software/Django-1.4.3/code/gluster_admin/gluster_admin/utils/test/vol_stop.xml"
  dummy_command = "%s/vol_stop.xml"%settings.BASE_FILE_PATH
  d = run_gluster_command(prod_command, dummy_command, "Starting volume %s"%vol_name)
  return d

def run_gluster_command(prod_command, dummy_command, display_command):
  #Run the command and return a dict with the xml results
  #prod_command is the actual command, dummy_command is the file to use in its place for non production, display_command is the string to be
  #be used for display to the user to show what the command is doing

  d = {}
  d['actual_command'] = prod_command
  d['display_command'] = display_command

  rd = xml_parse.run_command_get_xml_output_tree(prod_command, dummy_command)
  if "error_list" in rd:
    d["error_list"] = rd["error_list"]
  status_dict = None
  if "tree" in rd:
    root = rd["tree"].getroot()
    status_dict = xml_parse.get_op_status(root)
    d["op_status"] = status_dict
    d["root"] = root
  return d

def set_volume_quota(vol_name, enable_quota, set_quota, limit, unit):

  ret_list = []

  if enable_quota:
    #Need to first enable quota
    prod_command = 'gluster volume quota %s enable --xml'%(vol_name)
    dummy_command = "%s/enable_quota.xml"%settings.BASE_FILE_PATH
    d = run_gluster_command(prod_command, dummy_command, "Enabling quota for volume %s"%vol_name)
    ret_list.append(d)

  if not set_quota:
    #Need to first enable quota
    prod_command = 'gluster volume quota %s remove / --xml'%(vol_name)
    dummy_command = "%s/remove_quota.xml"%settings.BASE_FILE_PATH
    d = run_gluster_command(prod_command, dummy_command, "Removing quota for volume %s"%vol_name)
    ret_list.append(d)
  else:
    #Need to first enable quota
    prod_command = 'gluster volume quota %s limit-usage / %s%s --xml'%(vol_name, limit, unit)
    dummy_command = "%s/set_quota.xml"%settings.BASE_FILE_PATH
    d = run_gluster_command(prod_command, dummy_command, "Setting quota for volume %s to %s %s"%(vol_name, limit, unit))
    ret_list.append(d)

  return ret_list

def get_volume_quotas(vol_name):

  quotas = None
  #Need to first enable quota
  prod_command = 'gluster volume quota %s list --xml'%(vol_name)
  dummy_command = "%s/list_quota.xml"%settings.BASE_FILE_PATH
  d = run_gluster_command(prod_command, dummy_command, "Enabling quota for volume %s"%vol_name)
  if d["op_status"]["op_ret"] == 0:
    root = d["root"]
    quotas = xml_parse.get_vol_quotas(root)
    return quotas
  else:
    return None

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

  vol_dict = volume_info.get_volume_info(None, vol_name)

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
    d = set_volume_option(vol_name, "auth.allow", auth_allow, "Setting option for permitted access IP addresses for %s to \'%s\'"%(vol_name, auth_allow))
    ret_list.append(d)
  if _auth_reject != auth_reject:
    d = set_volume_option(vol_name, "auth.reject", auth_reject, "Setting option for denied access IP addresses for %s to \'%s\'"%(vol_name, auth_reject))
    ret_list.append(d)
  if _readonly != readonly:
    d = set_volume_option(vol_name, "features.read-only", readonly, "Setting readonly mount access(for all access methods) for %s to \'%s\'"%(vol_name, readonly))
    ret_list.append(d)
  if readonly == "off":
    #All the rest applies only if volume access is read-write
    if _nfs_disable != nfs_disable:
      if nfs_disable:
        p = "on"
      else:
        p = "off"
      d = set_volume_option(vol_name, "nfs.disable", p, "Setting NFS disable for %s to \'%s\'"%(vol_name, p))
      ret_list.append(d)
    if not nfs_disable:
      print "in"
      if nfs_volume_access and _nfs_volume_access != nfs_volume_access:
        d = set_volume_option(vol_name, "nfs.volume-access", nfs_volume_access, "Setting NFS access type for %s to \'%s\'"%(vol_name, nfs_volume_access))
        ret_list.append(d)
    if _enable_worm != enable_worm:
      if enable_worm:
        p = "enable"
      else:
        p = "disable"
      d = set_volume_option(vol_name, "features.worm", p, "Setting feature WORM for %s to \'%s\'"%(vol_name, p))
      ret_list.append(d)
  return ret_list

def set_volume_option(vol_name, option, value, display_command):
  prod_command = 'gluster volume set %s %s %s --xml'%(vol_name, option, value)
  #dummy_command = "/home/bkrram/Documents/software/Django-1.4.3/code/gluster_admin/gluster_admin/utils/test/set_vol_options.xml"
  dummy_command = "%s/set_vol_options.xml"%settings.BASE_FILE_PATH
  d = run_gluster_command(prod_command, dummy_command, display_command)
  return d

'''
def list_dir (vol_name, path):
  #mypath = path + ".dir"
  print "volname %s. path %s"%(vol_name, path)
  vol = gfapi.Volume("localhost", vol_name)
  print "test"
  vol.mount()
  print "test"
  fd = vol.opendir(path)
  if not isinstance(fd,gfapi.Dir):
    return False, "opendir error %d" % fd
  files = []
  while True:
    #print "next"
    ent = fd.next()
    if not isinstance(ent,gfapi.Dirent):
      break
    name = ent.d_name[:ent.d_reclen]
    print "name=%s"%(name)
    print "full_name=%s/%s"%(path,name)
    #print ent
    if vol.opendir("%s/%s"%(path,name)):
    #if isinstance(ent, gfapi.Dir):
      print "directory"
      if not name in [".", ".."]:
        files.append(name)
    else:
      print "file"
  return files
'''

def main():

  print list_dir("distvol", "/")

if __name__ == "__main__":
  main()

def remove_sled(scl, sled):

  ol = []
  
  localhost = socket.gethostname().strip()
  if "hostname" in scl[sled*2] and scl[sled*2]["in_cluster"] and scl[sled*2]["hostname"] != localhost: 
    d = {}
    command = 'gluster peer detach %s --xml'%scl[sled*2]["hostname"]
    d["actual_command"] = command
    node_num = scl[sled*2]["node"]
    if node_num%2:
      node_num = 1
    else:
      node_num = 2
    d["command"] = "Removing sled %d node %d from the storage pool"%(sled+1, node_num) 
    #rd = xml_parse.run_command_get_xml_output_tree(command, "/home/bkrram/Documents/software/Django-1.4.3/code/gluster_admin/gluster_admin/utils/test/peer_detach.xml")
    rd = xml_parse.run_command_get_xml_output_tree(command, "%s/peer_detach.xml"%settings.BASE_FILE_PATH)
    if "error_list" in rd:
      d["error_list"] = rd["error_list"]
    status_dict = None
    if "tree" in rd:
      root = rd["tree"].getroot()
      status_dict = xml_parse.get_op_status(root)
      d["op_status"] = status_dict
    if status_dict and status_dict["op_ret"] == 0:
      #Success so add audit info
      d["audit_str"] = "removed sled %d node %d"%(sled+1, node_num)
    ol.append(d)

    if not status_dict or status_dict["op_ret"] != 0  :
      #Could not get status or something went wrong so bail out
      return ol

  # Previous one succeeded so try next one

  if "hostname" in scl[(sled*2) + 1] and scl[(sled*2) + 1]["in_cluster"] and scl[(sled*2) + 1]["hostname"] != localhost:
    d = {}
    node_num = scl[(sled*2) + 1]["node"]
    if node_num%2:
      node_num = 1
    else:
      node_num = 2
    d["command"] = "Removing sled %d node %d from the storage pool"%(sled+1, node_num) 

    command = 'gluster peer detach %s --xml'%scl[(sled*2) + 1]["hostname"]
    d["actual_command"] = command

    #rd = xml_parse.run_command_get_xml_output_tree(command, "/home/bkrram/Documents/software/Django-1.4.3/code/gluster_admin/gluster_admin/utils/test/peer_detach.xml")
    rd = xml_parse.run_command_get_xml_output_tree(command, "%s/peer_detach.xml"%settings.BASE_FILE_PATH)
    if "error_list" in rd:
      if "error_list" in d:
        d["error_list"].append(rd["error_list"])
      else:
        d["error_list"] = rd["error_list"]

    status_dict = None
    if "tree" in rd:
      root = rd["tree"].getroot()
      status_dict = xml_parse.get_op_status(root)
      d["op_status"] = status_dict
    if status_dict and status_dict["op_ret"] == 0:
      #Success so add audit info
      d["audit_str"] = "removed sled %d node %d"%(sled+1, node_num)
    ol.append(d)

    if (not status_dict or status_dict["op_ret"] != 0)  and scl[sled*2]["hostname"] != localhost:
      #Could not get status or something went wrong so undo the first operation by trying to add node to cluster again
      d = {}
      command = 'gluster peer probe %s --xml'%scl[sled*2]["hostname"]
      d["actual_command"] = command
      node_num = scl[sled*2]["node"]
      if node_num%2:
        node_num = 1
      else:
        node_num = 2
      d["command"] = "Re-adding sled %d node %d to the storage pool as previous node removal failed"%(sled+1, node_num) 
      #rd = xml_parse.run_command_get_xml_output_tree(command, "/home/bkrram/Documents/software/Django-1.4.3/code/gluster_admin/gluster_admin/utils/test/peer_probe.xml")
      rd = xml_parse.run_command_get_xml_output_tree(command, "%s/peer_probe.xml"%settings.BASE_FILE_PATH)
      if "error_list" in rd:
        d["error_list"] = rd["error_list"]
      status_dict = None
      if "tree" in rd:
        root = rd["tree"].getroot()
        status_dict = xml_parse.get_op_status(root)
        d["op_status"] = status_dict
      if status_dict and status_dict["op_ret"] == 0:
        #Succeeded so back out old audit string
        d["audit_str"] = "re-added sled %d node %d to the storage pool as previous node removal failed"%(sled+1, node_num) 
      ol.append(d)

  return ol

'''
def build_create_volume_command(vol_name, vol_type, repl_count, transport, scl):

  d = {}
  # Now build the command based on parameters provided
  command = 'gluster volume create %s '%vol_name
  if vol_type in ['replicated', 'distributed_replicated', 'distributed_striped_replicated', 'striped_replicated']:
    command = command + ' replica %d '%repl_count
  command = command + ' transport %s '%transport

  node_list = []
  if vol_type == "distributed":
    for inode, node in enumerate(scl):
      if node["in_cluster"] == False:
        continue
      node_list.append("Sled %d Node %d "%((inode/2)+1, (inode%2)+1))
      if "hostname" in node:
        brick = "%s:/data/%s"%(node["hostname"], vol_name)
        command = command + brick + " "
  else:
    base = 0
    end = base + (repl_count*2) -1
    while end <= len(scl) :
      num_nodes = 0
      node_in_sled = random.randint(0,1)
      l = []
      incomplete_replica = False
      tmp_command = ""
      while num_nodes < repl_count:
        node_num = base + node_in_sled
        if node_num >= len(scl):
          incomplete_replica = True
          break
        #if scl[node_num]["in_cluster"] == False:
        if scl[node_num]["present"] == False or scl[node_num]["up"]==False or scl[node_num]["in_cluster"] == False:
          base = base + 2
          continue
        if "hostname" in scl[node_num]:
          l.append("Sled %d Node %d "%((node_num/2)+1, node_in_sled+1))
          b = scl[node_num]["hostname"]
          brick = "%s:/data/%s"%(b,vol_name)
          tmp_command = tmp_command + brick + " "
          num_nodes = num_nodes + 1
        base = base + 2
      if not incomplete_replica:
        command = command + tmp_command + " "
        node_list.append(l)
        end = base + (repl_count*2) -1
      else:
        break
  d["cmd"] = command
  d["node_list"] = node_list
  return d
'''
'''
def create_replace_command_file(scl, vil, src_sled, dest_sled):

  data = {}
  data["title"] = "Replacing sled %d with sled %d"%(src_sled, dest_sled)
  data["process"] = "replace_sled"
  data["volume_list"] = []
  data["command_list"] = []

  vol_list = ""
  command_list = []
  src_node_list = []

  src_node_list.append((src_sled - 1)*2 )
  src_node_list.append((src_sled - 1)*2 + 1)

  for n in src_node_list:
    if n%2 == 0:
      dest_node = (int(dest_sled) -1)*2
    else:
      dest_node = (int(dest_sled) -1)*2 + 1


    tvl = volume_info.get_volumes_on_node(scl[n], vil)
    for tv in tvl:
      if (not "hostname" in scl[n]) or (not "hostname" in scl[dest_node]):
        continue
      vd = volume_info.get_volume_info(vil, tv)
      if vd["type"] == "Distribute":
        d = {}
        #c = "gluster volume replace-brick %s %s:/data/%s %s:/data/%s"%(tv, scl[n]["hostname"], tv, scl[dest_node]["hostname"], tv)
        c = "gluster volume add-brick %s %s:/data/%s --xml"%(tv, scl[dest_node]["hostname"], tv)
        d["type"] = "add_brick"
        d["desc"] = "Adding volume storage in sled %d for volume %s"%(dest_sled, tv)
        d["command"] = c
        d["status_code"] = 0
        data["command_list"].append(d)
        d = {}
        c = "gluster --mode=script volume remove-brick %s %s:/data/%s start --xml"%(tv, scl[n]["hostname"], tv)
        d["type"] = "remove_brick_start"
        d["desc"] = "Migrating volume storage from sled %d for volume %s start"%(src_sled, tv)
        d["command"] = c
        d["status_code"] = 0
        data["command_list"].append(d)
        d = {}
        c = "gluster volume remove-brick %s %s:/data/%s status --xml"%(tv, scl[n]["hostname"], tv)
        d["type"] = "remove_brick_status"
        d["desc"] = "Migrating volume storage from sled %d for volume %s status"%(src_sled, tv)
        d["command"] = c
        d["status_code"] = 0
        data["command_list"].append(d)
        d = {}
        c = "gluster --mode=script volume remove-brick %s %s:/data/%s commit --xml"%(tv, scl[n]["hostname"], tv)
        d["type"] = "remove_brick_commit"
        d["desc"] = "Migrating volume storage from sled %d for volume %s commit"%(src_sled, tv)
        d["command"] = c
        d["status_code"] = 0
        data["command_list"].append(d)
      else:
        #Replicated vol so for now do a replace-brick
        d = {}
        c = "gluster volume replace-brick %s %s:/data/%s %s:/data/%s commit force --xml"%(tv, scl[n]["hostname"], tv, scl[dest_node]["hostname"], tv)
        #c = "gluster volume add-brick %s %s:/data/%s"%(tv, scl[dest_node]["hostname"], tv)
        d["type"] = "replace_brick_commit"
        #d["desc"] = "Adding volume storage in sled %d for volume %s"%(dest_sled, tv)
        d["desc"] = "Replacing storage location for volume %s from sled %d to sled %d"%(tv, src_sled, dest_sled)
        d["command"] = c
        d["status_code"] = 0
        data["command_list"].append(d)
        d = {}
        #c = "gluster volume remove-brick %s %s:/data/%s start --xml"%(tv, scl[n]["hostname"], tv)
        c = "gluster volume heal %s full --xml"%tv
        d["type"] = "volume_heal_full"
        d["desc"] = "Migrating volume data from sled %d for volume %s start"%(src_sled, tv)
        d["command"] = c
        d["status_code"] = 0
        data["command_list"].append(d)
        d = {}
        #c = "gluster volume remove-brick %s %s:/data/%s status --xml"%(tv, scl[n]["hostname"], tv)
        c = "gluster volume heal %s info --xml"%tv
        d["type"] = "volume_heal_info"
        d["desc"] = "Migrating volume data from sled %d for volume %s info"%(src_sled, tv)
        d["command"] = c
        d["status_code"] = 0
        data["command_list"].append(d)

      if not tv in data["volume_list"]:
        data["volume_list"].append(tv)
  try:
    dir = settings.BATCH_COMMANDS_DIR
  except:
    dir = "."

  if not os.path.exists(dir):
    try:
      os.mkdir(dir)
    except OSError:
      return None

  t = time.localtime()
  data["status"] = "Not yet started"
  data["initiate_time"] = time.strftime("%a %b %d %H:%M:%S %Y", t)
  file_name = "%s_%d"%(time.strftime("bp_replace_sled_%b_%d_%Y_%H_%M_%S", t) , int(time.time()))
  full_file_name = "%s/in_process/%s"%(dir, file_name)
  data["status_url"] = "/show/batch_status_details/%s"%file_name
  d = {}
  try:
    with open(full_file_name, "w+") as f:
      json.dump(data, f, indent=2)
  except Exception, e:
    d["error"] = str(e)
  else:
    d["file_name"] = file_name
  return d
'''
