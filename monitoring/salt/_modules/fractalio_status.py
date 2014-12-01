import os, re, subprocess, glob
import salt.modules.network, salt.modules.ps, salt.modules.status
import fractalio
from fractalio import zfs, hardware_utils, command


def _execute_command(command = None):
  """ This function executes a command and returns the output in the form of a tuple.
      Exits in the case of an exception.
  """

  if command is None:
    return None

  err = ''
  args = command.split()
  try:
    proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    if proc:
			ret = proc.communicate()

  except Exception as e:
    err = str(e)
    return err, None

  if ret:
    return ret, proc.returncode
  else:
    return ret, None


def _validate_cmd_output(output_tuple = None):

  if output_tuple is None:
    return None

  if output_tuple[0]  :
    output = output_tuple[0]
  else:
    print "Error : %s" % output_tuple[1]
    return None

  return output

def disk_info():

  return_dict = {}
  fractalio.hardware_utils.rescan_drives()

  pool_list = zfs.get_pool_list()
  #print pool_list


 
  # To get information about Hard Disk and ..
  # the list containing the info is abbreviated as "dl"
  cmd_dl = "/usr/sbin/smartctl --scan"

  #output_tuple_dl = command_execution(cmd_dl)
  #cmd_executed_dl = validate_cmd_output(output_tuple_dl)
  ret, rc = command.execute_with_rc(cmd_dl)
  cmd_executed_dl = command.get_output_list(ret)
    

  # Regex to capture "/dev/sdX"
  reg_exp_dl = re.compile("(/dev/[a-z]+)")

  dl = []
  for line in cmd_executed_dl:
    d = {}
    if reg_exp_dl.search(line):
      result_dl = re.search(r'/dev/sd[a-z]', line)
      result_dl1 = re.search(r'/dev/(sd[a-z])', line)
      if result_dl:
        d["full_path"] = result_dl.group()
        dname = result_dl1.groups()[0]
        r = re.match('^sd[a-z]', dname)
        d["name"] = r.group()
        dl.append(d)
      else:
        print "No disk list pattern match found"
 
  #print "disk list info: ", dl
  id_dict = {}
  for (dirpath, dirnames, filenames) in os.walk('/dev/disk/by-id'):
    #print dirpath
    #print dirnames
    #print filenames
    for file in filenames:
      if "scsi-SATA" not in file:
        continue
      #print file
      #print "%s/%s"%(dirpath, file)
      #print os.readlink("%s/%s"%(dirpath, file))
      if os.path.islink("%s/%s"%(dirpath,file)):
        realpath = os.path.normpath(os.path.join(os.path.dirname("%s/%s"%(dirpath, file)), os.readlink("%s/%s"%(dirpath,file)) ) )
        id_dict[realpath] = file
        #realpath = os.path.realpath(os.readlink("%s/%s"%(dirpath,file)))
        #print realpath
  #print id_dict

  #print dl
  for disk_name_dict in dl:
      
    disk_info_dict = {}
    disk_info_dict["rotational"] = False
    if os.path.isfile('/sys/block/%s/queue/rotational'%disk_name_dict["name"]):
      with open ('/sys/block/%s/queue/rotational'%disk_name_dict["name"]) as f:
        str = f.read()
        if str.strip() == "1":
          disk_info_dict["rotational"] = True
    cmd_disk = "/usr/sbin/smartctl -H -i" + " " + disk_name_dict["full_path"] 
    dl_output = os.popen(cmd_disk).read()
    lines = re.split("\r?\n", dl_output)

    reobj1 = re.compile("(.*Number:.*)")
 
    # To get the storage capacity of each disk
    st1 = os.popen("/sbin/fdisk -l %s | grep Disk"%disk_name_dict["full_path"])
    str2 = st1.read()
    disk_capacity = re.search(r'\s[0-9]+\.[0-9]\s[a-zA-Z]+',str2)
 
    for line in lines:
      #print line
      if reobj1.search(line):
        serial_number = re.search(r':\s+\S+', line)
        disk_info_dict['orig_name'] = disk_name_dict["full_path"]
        #disk_info_dict['serial_number'] = serial_number.group().strip(": ")
        serial_number = serial_number.group().strip(": ")
        disk_info_dict['capacity'] = (disk_capacity.group()).strip()

    '''
    if disk_name_dict["name"] in pool_names:
      disk_info_dict["pool"] = pool_names[disk_name_dict["name"]]
    else:
      disk_info_dict["pool"] = None
    '''

    #print disk_info_dict["name"]
    if disk_info_dict["orig_name"] in id_dict:
      disk_info_dict["id"] = id_dict[disk_info_dict["orig_name"]]

    found_pool = False
    for pool in pool_list:
      for component in pool["config"]["components"]:
        if component["name"] == disk_info_dict["id"]:
          disk_info_dict["pool"] = pool["config"]["pool_status"]["name"]
          found_pool = True
          break
      if found_pool:
        break

    return_dict[serial_number] = disk_info_dict
    #disk_info_list.append(disk_info_dict) 

  #print disk_info_list

  #  if return_dict:
  #  return_dict['disks'] = return_dict
  #else:
  #  return_dict['disks'] = {}
  #return_dict['disk_info'] = "Can't populate disk list Information"

  #print return_dict
  return return_dict


def disk_status():

  # To get information about Hard Disk and ..
  # the list containing the info is abbreviated as "dl"
  cmd_dl = "/usr/sbin/smartctl --scan"

  output_tuple_dl, rc = _execute_command(cmd_dl)
  output_list = _validate_cmd_output(output_tuple_dl)

  # Regex to capture "/dev/sdX"
  reg_exp_dl = re.compile("(/dev/[a-z]+)")

  dl = []
  for line in output_list.split('\n'):
    if reg_exp_dl.search(line):
      result_dl = re.search(r'/dev/sd[a-z]', line)
      if result_dl:
        dl.append(result_dl.group() )
      else:
        print "No disk list pattern match found"

  #print "disk list info: ", dl    

  #print "disk list info: ", dl
  id_dict = {}
  for (dirpath, dirnames, filenames) in os.walk('/dev/disk/by-id'):
    #print dirpath
    #print dirnames
    #print filenames
    for file in filenames:
      if "scsi-SATA" not in file:
        continue
      #print file
      #print "%s/%s"%(dirpath, file)
      #print os.readlink("%s/%s"%(dirpath, file))
      if os.path.islink("%s/%s"%(dirpath,file)):
        realpath = os.path.normpath(os.path.join(os.path.dirname("%s/%s"%(dirpath, file)), os.readlink("%s/%s"%(dirpath,file)) ) )
        id_dict[realpath] = file
        #realpath = os.path.realpath(os.readlink("%s/%s"%(dirpath,file)))
        #print realpath
  #print id_dict
  disk_status = {}
  pool_list = zfs.get_pool_list()
  for disk_name in dl:
    #print salt.modules.status.diskusage(disk_name)
    print disk_name
    d = {}
    cmd = "/usr/sbin/smartctl -H -i %s"%disk_name
    output_tuple_dl, rc = _execute_command(cmd)
    output_list = _validate_cmd_output(output_tuple_dl)
    lines = re.split("\r?\n", output_list)
    reobj1 = re.compile(".*self-assessment.*") 
    reobj2 = re.compile("^Serial Number:") 
    
    serial_number = None
    for l in lines:
      if reobj1.search(l):
        ent = re.search(r'\s[A-Z]+', l)
        d["status"] = (ent.group()).strip()
      if reobj2.search(l):
        #print "found serial number!"
        ent = re.search(r'(^Serial Number:)\s*(\S+)', l)
        #print ent.groups()
        serial_number = ent.groups()[1]

    if disk_name in id_dict:
      id = id_dict[disk_name]
      d["name"] = disk_name
      found_pool = False
      for pool in pool_list:
        for component in pool["config"]["components"]:
          if component["name"] == id:
            d["pool"] = pool["config"]["pool_status"]["name"]
            found_pool = True
            break
        if found_pool:
          break
    if serial_number:
      disk_status[serial_number] = d
    else:
      print "Count not find the disk serial number!"
  return disk_status

def interface_status():
  return salt.modules.network.interfaces()
   
def load_avg():
  d = salt.modules.status.loadavg()
  d["cpu_cores"] = int(_cpu_cores())
  return d

def disk_usage():
  return salt.modules.status.diskusage()

def _cpu_cores():
  d = salt.modules.status.cpuinfo()
  if d:
    return d["cpu cores"]
  else:
    return -1

def mem_info():
  d = salt.modules.status.meminfo()
  ret = {}
  if d:
    if "MemTotal" in d:
      ret['mem_total'] = d['MemTotal']
    if "MemFree" in d:
      ret['mem_free'] = d['MemFree']
  return ret

def pool_status():

  pool_list = fractalio.zfs.get_pool_list()
  return pool_list


def status():
  d = {}
  d["disks"] = disk_status()
  d["interfaces"] = interface_status()
  d["pools"] = pool_status()
  d["load_avg"] = load_avg()
  d["disk_usage"] = disk_usage()
  d["mem_info"] = mem_info()
  return d
      
if __name__ == '__main__':
  #print status()
  print disk_info()
  #print pool_status()
  #print disk_status()
  #print interface_status()
  #print status()
  #print load_avg()
  #print disk_usage()
  #print mem_info()
