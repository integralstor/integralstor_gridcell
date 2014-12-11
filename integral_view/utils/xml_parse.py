
from xml.etree import ElementTree
import tempfile, sys, os

import fractalio
from fractalio import filesize
from fractalio import networking
from django.conf import settings
import command



def get_text(node, subnode):
  n = node.findall(subnode)
  if n:
    return n[0].text
  else:
    return None

def get_op_status(root):
  # Get the status of a gluster command from the xml output
  d = {}
  for e in root.getiterator():
    if e.tag == "opRet":
      try :
        d["op_ret"] = int(e.text)
      except Exception, e:
        d["op_ret"] = None
      #print "opRet = %s"%e.text
    elif e.tag == "opErrno":
      try :
        d["op_errno"] = int(e.text)
      except Exception, e:
        d["op_errno"] = None
      #print "opErrno = %s"%e.text
    elif e.tag == "opErrstr":
      d["op_errstr"] = e.text
      #print "opErrstr = %s"%e.text
    elif e.tag == "output":
      d["output"] = e.text
      #print "output = %s"%e.text
  return d

def _get_bricks(volume, type_str, replica_count):
  '''
  bricks = []
  n = volume.findall(".//bricks/brick")
  for node in n:
    d = {}
    ind = node.text.find(":")
    ind1 = node.text.find("/")
    rest = node.text[ind1+1:]
    ind2 = rest.find("/")
    d["host"] = node.text[:ind]
    d["path"] = node.text[ind:]
    d["pool_name"] = rest[:ind2]
    bricks.append(d) 
  return bricks
  '''

  bricks = volume.findall(".//bricks/brick")
  bl = []
  tl = []
  count = 0
  for brick in bricks:
    if "replicate" in type_str:
      #print count
      tl.append(brick.text)
      count += 1
      #Create lists of replica sets
      if count == replica_count:
        #print "appending"
        bl.append(tl)
        tl = []
        count = 0
    else:
      #Create lists of individual nodes
      tl = []
      tl.append(brick.text)
      bl.append(tl)
  return bl

def _get_options(volume):
  options = []
  n = volume.findall(".//options/option")
  for node in n:
    d = {}
    x = node.find("./name")
    if x != None:
      d["name"] = x.text
    x = node.find(".//value")
    if x != None:
      d["value"] = x.text
    options.append(d) 
  return options

def run_command_get_xml_output_tree(cmd, file_name):
  #If production, run the command else read from file_name, return the xml tree
  d = {}
  el = []
  tree = None
  if not settings.PRODUCTION:
    try :
      with open(file_name, 'rt') as f:
        tree = ElementTree.parse(f)
    except Exception, e:
      el.append(str(e))
  else:
    temp = tempfile.TemporaryFile()
    try:
      r = command.execute(cmd)
      if r:
        l = command.get_output_list(r)
        el = command.get_error_list(r)
        if l:
          for line in l:
            temp.write(line)
      temp.seek(0)
      tree = ElementTree.parse(temp)
    except Exception, e:
      el.append(str(e))
    finally:
      temp.close()
  if tree:
    d["tree"] = tree
  if el:
    d["error_list"] = el
  return d

def get_volume_list():

  production = True
  try:
    production =  settings.PRODUCTION
  except Exception, e:
    production = False

  if not production:
    #fn = "/home/bkrram/Documents/software/Django-1.4.3/code/gluster_admin/gluster_admin/utils/b.xml"
    fn = "%s/b.xml"%settings.BASE_FILE_PATH
    with open(fn, 'rt') as f:
      tree = ElementTree.parse(f)
  else:
    temp = tempfile.TemporaryFile()
    try:
      cmd = "/usr/local/sbin/gluster volume info all --xml"
      r = command.execute(cmd)
      if r:
        #print "cmd out is "
        l = command.get_output_list(r)
        #print l
        #print "cmd err is "
        #l = command.get_error_list(r)
        #print l
        for line in l:
          temp.write(line)
        temp.seek(0)
        tree = ElementTree.parse(temp)
    finally:
      temp.close()


  vl = []
  for volume in tree.findall('.//volumes/volume'):
    _vol_name = get_text(volume, "name")
    if settings and settings.ADMIN_VOL_NAME and _vol_name == settings.ADMIN_VOL_NAME:
      continue
    v = {}
    v["name"] = _vol_name
    v["type"] = get_text(volume, "typeStr")
    v["status"] = int(get_text(volume, "status"))
    v["status_str"] = get_text(volume, "statusStr")
    v["brick_count"] = int(get_text(volume, "brickCount"))
    v["dist_count"] = int(get_text(volume, "distCount"))
    v["stripe_count"] = int(get_text(volume, "stripeCount"))
    v["replica_count"] = int(get_text(volume, "replicaCount"))
    v["opt_count"] = get_text(volume, "optCount")
    v["bricks"] = _get_bricks(volume, v["type"], v["replica_count"])
    v["options"] = _get_options(volume)

    protocols = {}
    # Set enabled unless turned off with options
    protocols["cifs"] = True
    protocols["nfs"] = True
    for option in v["options"]:
      if option["name"] == "user.cifs":
        if option["value"] in ['disable','off','false']:
          protocols["cifs"] = False 
        if option["name"] == "nfs.disable":
          if option["value"] in ['on','true']:
            protocols["nfs"] = False 
    v["protocols"] = protocols
    vl.append(v)

  for vol in vl:
    if vol["status"] != 1:
      continue      
    if not production:
      fn = "%s/volume_status_detail.xml"%settings.BASE_FILE_PATH
      with open(fn, 'rt') as f:
        tree = ElementTree.parse(f)
    else:
      temp = tempfile.TemporaryFile()
      try:
        cmd = "/usr/local/sbin/gluster volume status %s detail --xml"%vol["name"]
        print cmd
        r = command.execute(cmd)
        if r:
          #print "cmd out is "
          l = command.get_output_list(r)
          #print l
          #print "cmd err is "
          #l = command.get_error_list(r)
          #print l
          for line in l:
            temp.write(line)
          temp.seek(0)
          tree = ElementTree.parse(temp)
      finally:
        temp.close()

    root = tree.getroot()
    nodes = root.findall('.//node')
    size_total = 0
    size_free = 0
    bd = {}
    num_up = 0
    num_down = 0
    for node in nodes:
      #print "----"
      #for a in iter(node):
      #  print a.tag, a.text
      #a = node.find('./node')
      if node.find('./node'):
        print "continuing"
        continue
      #a = node.find('./status')
      if node.find('./status') == None:
        print "continuing"
        continue
      #print "ok"
      d = {}
      d["status"] = int(node.find('./status').text)
      d["size_total"] = int(node.find('./sizeTotal').text)
      d["size_free"] = int(node.find('./sizeFree').text)
      d["hostname"] = node.find('./hostname').text
      d["path"] = node.find('./path').text
      d["pid"] = node.find('./pid').text
      brick_name = "%s:%s"%(d["hostname"], d["path"])
      bd[brick_name] = d
      if d["status"] == 1:
        num_up +=1
      else:
        num_down += 1 
    #assert False
    vol["brick_status"] = bd

    if vol["replica_count"] > 1:
      replica_set_status = []
      for br in vol["bricks"] :
        counted = False
        num_down = 0
        num_up = 0
        for  b in br:
          if b not in bd:
            #Could happen if a brick is down
            return None
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
    vol["size_used_percent"] = int(((size_total-size_free)/float(size_total)) * 100)
    #print vol["size_used_percent"]


    # Now get the status of the self heal and NFS servers for each node
    if not production:
      fn = "%s/volume_status.xml"%settings.BASE_FILE_PATH
      with open(fn, 'rt') as f:
        tree = ElementTree.parse(f)
    else:
      temp = tempfile.TemporaryFile()
      try:
        cmd = "/usr/local/sbin/gluster volume status %s --xml"%vol["name"]
        r = command.execute(cmd)
        if r:
          #print "cmd out is "
          l = command.get_output_list(r)
          #print l
          #print "cmd err is "
          #l = command.get_error_list(r)
          #print l
          for line in l:
            temp.write(line)
          temp.seek(0)
          tree = ElementTree.parse(temp)
      finally:
        temp.close()

    root = tree.getroot()
    nodes = root.findall('.//node')

    vol["processes_ok"] = True
    for node in nodes:
      if node.find('./node'):
        print "continuing"
        continue
      hostname = node.find('./hostname').text
      if hostname not in ["NFS Server", "Self-heal Daemon"]:
        continue
      path = node.find('./path').text
      if path == "localhost":
        path = os.uname()[1]
      status = int(node.find('./status').text)
      found = False
      for br in vol["brick_status"].keys():
        #print "splitting %s"%br
        h, p = br.split(':')
        #print h, hostname
        if h == path:
          #print "Found!"
          found = True
          break
      if found:
        #br now holds the brick for which we will update the nfs and self heal status
        if hostname == "Self-heal Daemon":
          vol["brick_status"][br]["self_heal_deamon_status"] = status
          if "replicate" in vol["type"].lower() and status != 1:
            vol["processes_ok"] = False
        elif hostname == "NFS Server":
          vol["brick_status"][br]["nfs_status"] = status
          if vol["protocols"]["nfs"] and status != 1:
            vol["processes_ok"] = False
      
      
  #print vl
  #assert False
  return vl

def get_snapshots(root):
  l = []
  t = root.findall('.//snapshots/snapshot')
  if t:
    for node in t:
      d = {}
      d["name"] = get_text(node, "name")
      d["create_time"] = get_text(node, "createTime")
      x = node.find('./snapVolume')
      if x:
        d["status"] = get_text(x, "status")
      l.append(d)
  return l
    

def get_peer_list():
  production = True
  try:
    production =  settings.PRODUCTION
  except Exception, e:
    production = True

  if not production:
    #with open('/home/bkrram/Documents/software/Django-1.4.3/code/gluster_admin/gluster_admin/utils/peer_status', 'rt') as f:
    with open('%s/peer_status'%settings.BASE_FILE_PATH, 'rt') as f:
      tree = ElementTree.parse(f)
  else:
    #temp = tempfile.TemporaryFile()
    try:
      cmd = "/usr/local/sbin/gluster peer status --xml"
      print "executing %s"%cmd
      r = command.execute(cmd)
      if r:
        peer_list = command.get_output_list(r)
        xml_string = ''.join(peer_list)
        tree = ElementTree.fromstring(xml_string)
        #for line in l:
        #  temp.write(line)
        #temp.seek(0)
        #tree = ElementTree.parse(temp)
    finally:
      pass
    #  temp.close()

  peerlist = []
  #t = tree.findall('.//peerStatus/peer')
  t = tree.findall('.//peer')
  for peer in t:
    d = {}
    d["hostname"] = get_text(peer, "hostname")
    d["status"] = get_text(peer, "connected")
    #peerlist.append(get_text(peer, "hostname"))
    peerlist.append(d)
  tree = None
  if peerlist:
    d = {}
    d["hostname"] = os.uname()[1]
    if networking.can_connect("localhost", 24007):
      d["status"] = '1'
    else:
      d["status"] = '0'
    peerlist.append(d)

  return peerlist

def get_vol_quotas(root):
  # Return a dict of all quotas with keys being the dir
  t = root.findall(".//quota")
  ret_dict = {}
  for q in t:
    d = {}
    d["limit"] = get_text(q, "limit")
    d["size"] = get_text(q, "size")
    ret_dict[get_text(q, "path")] = d
  return ret_dict

def main():
  path = os.path.dirname(os.path.abspath(__file__))
  sys.path.insert(0, '%s/../..'%path)
  os.environ['DJANGO_SETTINGS_MODULE']='integral_view.settings'
  BASEPATH = settings.BATCH_COMMANDS_DIR
  production = settings.PRODUCTION
  get_volume_list()

if __name__ == "__main__":
  main()
