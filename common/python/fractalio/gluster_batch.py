import time, os, json, os.path, re, sys
import volume_info
import fractalio
from fractalio import common

batch_dir = common.get_batch_files_path()

def create_replace_command_file(si, vil, src_node, dest_node):

  data = {}
  data["title"] = "Replacing GRIDCell %s with GRIDCell %s"%(src_node, dest_node)
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
      d["desc"] = "Adding volume storage in GRIDCell %s for volume %s"%(dest_node, tv)
      d["command"] = c
      d["status_code"] = 0
      data["command_list"].append(d)
      d = {}
      c = "gluster --mode=script volume remove-brick %s %s:/data/%s start --xml"%(tv, src_node, tv)
      d["type"] = "remove_brick_start"
      d["desc"] = "Migrating volume storage from GRIDCell %s for volume %s start"%(src_node, tv)
      d["command"] = c
      d["status_code"] = 0
      data["command_list"].append(d)
      d = {}
      c = "gluster volume remove-brick %s %s:/data/%s status --xml"%(tv, src_node, tv)
      d["type"] = "remove_brick_status"
      d["desc"] = "Migrating volume storage from GRIDCell %s for volume %s status"%(src_node, tv)
      d["command"] = c
      d["status_code"] = 0
      data["command_list"].append(d)
      d = {}
      c = "gluster --mode=script volume remove-brick %s %s:/data/%s commit --xml"%(tv, src_node, tv)
      d["type"] = "remove_brick_commit"
      d["desc"] = "Migrating volume storage from GRIDCell %s for volume %s commit"%(src_node, tv)
      d["command"] = c
      d["status_code"] = 0
      data["command_list"].append(d)
    else:
      #Replicated vol so for now do a replace-brick
      d = {}
      c = "gluster volume replace-brick %s %s:/data/%s %s:/data/%s commit force --xml"%(tv, src_node, tv, dest_node, tv)
      d["type"] = "replace_brick_commit"
      d["desc"] = "Replacing storage location for volume %s from GRIDCell %s to GRIDCell %s"%(tv, src_node, dest_node)
      d["command"] = c
      d["status_code"] = 0
      data["command_list"].append(d)
      d = {}
      c = "gluster volume heal %s full --xml"%tv
      d["type"] = "volume_heal_full"
      d["desc"] = "Migrating volume data from GRIDCell %s for volume %s start"%(src_node, tv)
      d["command"] = c
      d["status_code"] = 0
      data["command_list"].append(d)
      d = {}
      c = "gluster volume heal %s info --xml"%tv
      d["type"] = "volume_heal_info"
      d["desc"] = "Migrating volume data from GRIDCell %s for volume %s info"%(src_node, tv)
      d["command"] = c
      d["status_code"] = 0
      data["command_list"].append(d)

    if not tv in data["volume_list"]:
      data["volume_list"].append(tv)

  if not os.path.exists(batch_dir):
    try:
      os.mkdir(batch_dir)
    except OSError:
      return None

  t = time.localtime()
  data["status"] = "Not yet started"
  data["initiate_time"] = time.strftime("%a %b %d %H:%M:%S %Y", t)
  file_name = "%s_%d"%(time.strftime("bp_replace_node_%b_%d_%Y_%H_%M_%S", t) , int(time.time()))
  full_file_name = "%s/%s"%(batch_dir, file_name)
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

def create_rebalance_command_file(vol_name):

  if not os.path.exists(batch_dir):
    try:
      os.mkdir(batch_dir)
    except OSError:
      return None

  t = time.localtime()
  data = {}
  data["initiate_time"] = time.strftime("%a %b %d %H:%M:%S %Y", t)
  file_name = "%s_%d"%(time.strftime("bp_volume_rebalance_%b_%d_%Y_%H_%M_%S", t) , int(time.time()))
  full_file_name = "%s/%s"%(batch_dir, file_name)
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

def create_factory_defaults_reset_file(scl, vil):

  t = time.localtime()
  data = {}
  data["initiate_time"] = time.strftime("%a %b %d %H:%M:%S %Y", t)
  file_name = "%s_%d"%(time.strftime("bp_factory_defaults_reset_%b_%d_%Y_%H_%M_%S", t) , int(time.time()))
  full_file_name = "%s/%s"%(batch_dir, file_name)
  data["status_url"] = "/show/batch_status_details/%s"%file_name
  data["title"] = "Reset system to factory defaults"
  data["process"] = "factory_deafults_reset"
  data["status"] = "Not yet started"
  data["command_list"] = []

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

  if not os.path.exists(batch_dir):
    try:
      os.mkdir(batch_dir)
    except OSError:
      return None

  try :
    with open(full_file_name, "w+") as f:
      json.dump(data, f, indent=2)
  except Exception, e:
    d["error"] = str(e)
  else:
    d["file_name"] = file_name
  return d
