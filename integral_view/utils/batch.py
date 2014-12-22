
import time, os, json, os.path, re, sys

path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '%s/../..'%path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'integral_view.settings'
#sys.path.insert(0, '/opt/fractal/gluster_admin')
#sys.path.insert(0, '/home/bkrram/Documents/software/Django-1.4.3/code/gluster_admin')
from django.conf import settings
import volume_info

class BatchException(Exception):

  msg = None

  def __init__(self, msg):
    self.msg = msg

  def __str__(self):
    return repr(self.msg)

def load_all_files(type):
  #Used to load all the info from all the files of type type (either "start" or "process")
  try: 
    batch_dir = settings.BATCH_COMMANDS_DIR
  except:
    batch_dir = "."
  files = os.listdir(os.path.normpath("%s/%s"%(batch_dir,type)))
  list = []
  for file in files:
    with open(os.path.normpath("%s/%s/%s"%(batch_dir, type, file))) as f:
      print "%s/%s/%s"%(batch_dir, type, file)
      d = json.load(f)
      list.append(d)
  return list

def load_specific_file(filename):

  # Return the json contents of the filename as the data structure
  try:
    batch_dir = settings.BATCH_COMMANDS_DIR
  except:
    batch_dir = "."
  f = None
  try:
    f = open(os.path.normpath("%s/in_process/%s"%(batch_dir, filename)))
  except IOError:
    pass
  if f:
    d = json.load(f)

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
