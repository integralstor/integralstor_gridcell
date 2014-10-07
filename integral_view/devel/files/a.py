from xml.etree import ElementTree
import filesize

def get_op_status(root):
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
  return d

def get_text(node, subnode):
  n = node.findall(subnode)
  if n:
    return n[0].text
  else:
    return None

vol_list = []
with open('volume_info.xml', 'rt') as f:
  tree = ElementTree.parse(f)

  root = tree.getroot()
  #op_status = get_op_status(root)
  #print op_status
  vols = root.findall('.//volume')
  
  for vol in vols:
    d = {}
    d["name"] = vol.find('./name').text
    d["status"] = vol.find('./status').text
    d["status_str"] = vol.find('./statusStr').text
    d["type_str"] = vol.find('./typeStr').text.lower()
    d["replica_count"] = int(vol.find('./replicaCount').text)
    bricks = vol.findall('.//brick')
    bl = []
    tl = []
    count = 0
    for brick in bricks:
      if "replicate" in d["type_str"]:
        #print count
        tl.append(brick.text)
        count += 1
        #Create lists of replica sets
        if count == d["replica_count"]:
          #print "appending"
          bl.append(tl)
          tl = []
          count = 0
      else:
        #Create lists of individual nodes
        tl = []
        tl.append(brick.text)
        bl.append(tl)
    d["bricks"] = bl
    ol = []
    options = vol.findall('.//option')
    protocols = {}
    # Set enabled unless turned off with options
    protocols["cifs"] = True
    protocols["nfs"] = True
    for option in options:
      od = {}
      for o in option.getchildren():
        if o.tag == 'name':
          n = o.text
        elif o.tag == 'value':
          od[n] = o.text
          if n == "user.cifs":
            if o.text in ['disable','off','false']:
              protocols["cifs"] = False 
          if n == "nfs.disable":
            if o.text in ['on','true']:
              protocols["nfs"] = False 
          ol.append(od)
    d["options"] = ol
    d["protocols"] = protocols
    vol_list.append(d)



for vol in vol_list:
  #Issue actual commen here
  with open('volume_status_detail.xml', 'rt') as f:
    tree = ElementTree.parse(f)

    root = tree.getroot()
    #op_status = get_op_status(root)
    #print op_status
    nodes = root.findall('.//node')
    size_total = 0
    size_free = 0
    bd = {}
    num_up = 0
    num_down = 0
    for node in nodes:
      d = {}
      d["status"] = int(node.find('./status').text)
      d["size_total"] = int(node.find('./sizeTotal').text)
      d["size_free"] = int(node.find('./sizeFree').text)
      d["hostname"] = node.find('./hostname').text
      d["path"] = node.find('./path').text
      brick_name = "%s:%s"%(d["hostname"], d["path"])
      bd[brick_name] = d
      if d["status"] == 1:
        num_up +=1
      else:
        num_down += 1 

    if vol["replica_count"] > 1:
      replica_set_status = []
      for br in vol["bricks"] :
        counted = False
        num_down = 0
        num_up = 0
        for  b in br:
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
        elif max(replica_set_status) > 0:
          num_more = vol["replica_count"] - max(replica_set_status)
          vol["data_access_status"] = "Data accessible but vulnerable. Loss of %d more data locations will cause data loss"%num_more
        else:
          vol["data_access_status"] = "Healthy"
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
      else:
        vol["data_access_status"] = "Healthy"
        

  vol["size_total"] = filesize.naturalsize(size_total)
  vol["size_free"] = filesize.naturalsize(size_free)
  
with open('volume_status.xml', 'rt') as f:
  tree = ElementTree.parse(f)

  root = tree.getroot()
  #op_status = get_op_status(root)
  #print op_status
  nodes = root.findall('.//node')
  d = {}
  for node in nodes:
    hostname = node.find('./hostname').text
    path = node.find('./path').text
    status = int(node.find('./status').text)
    if path not in d:
      d[path] = {}
    print "hostname %s path %s status %s"%(hostname, path, status)
    if hostname in ["NFS Server", "Self-heal Daemon"]:
      if hostname == "Self-heal Daemon":
        d[path]["self_heal_deamon_status"] = status
      elif hostname == "NFS Server":
        d[path]["nfs_status"] = status
  print d
#print vol_list


