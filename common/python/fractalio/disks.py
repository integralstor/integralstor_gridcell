import fractalio
from fractalio import zfs, command
import re, os, pprint

def rescan_drives():
  try :
    for dirname, dirs, files in os.walk('/sys/class/scsi_host/'):
      #print dirs
      for dir in dirs:
        #print '/sys/class/scsi_host/%s/scan'%dir
        with open('/sys/class/scsi_host/%s/scan'%dir, 'w') as f:
          #print '/sys/class/scsi_host/%s/scan'%dir
          f.write('- - -')
          f.close()
  except Exception, e:
    return False, "Error rescanning drives : %s"%str(e)
  else:
    return True, None

def get_all_disks_by_name():

  #Returns a list of all disks by name (sda/sbd, etc) in the sytem
  dl = []
  try:
    cmd_dl = "/usr/sbin/smartctl --scan"
    ret, rc = command.execute_with_rc(cmd_dl)
    cmd_executed_dl = command.get_output_list(ret)
    
    # Regex to capture "/dev/sdX"
    reg_exp_dl = re.compile("(/dev/[a-z]+)")

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
  except Exception, e:
    return None, "Error retrieving disks by name : %s"%str(e)
  else:
    return dl, None


def _get_disk_info_list():
  #Returns a list of all disks with ID information
  dl = []
  try:
    for (dirpath, dirnames, filenames) in os.walk('/dev/disk/by-id'):
      #print dirpath
      #print dirnames
      #print filenames
      for file in filenames:
        d = {}
        if not file.startswith('ata'):
          continue
        #print file
        #print "%s/%s"%(dirpath, file)
        #print os.readlink("%s/%s"%(dirpath, file))
        if os.path.islink("%s/%s"%(dirpath,file)):
          realpath = os.path.normpath(os.path.join(os.path.dirname("%s/%s"%(dirpath, file)), os.readlink("%s/%s"%(dirpath,file)) ) )
          d['path'] = realpath
          d["name"] = os.path.split(os.path.normpath(os.readlink("%s/%s"%(dirpath,file))))[1]
          d['id'] = file
          if "part" in file.lower():
            partition = True
          else:
            partition = False
          d["partition"] = partition
          dl.append(d)
          #realpath = os.path.realpath(os.readlink("%s/%s"%(dirpath,file)))
          #print realpath
      #Now reorganize into a dict to return
  except Exception, e:
    return None, "Error retrieving disks by ID : %s"%str(e)
  else:
    return dl, None

def is_rotational(disk_name):
  #Given a disk name like sda, returns true if its a rotational device
  rotational = True
  if not disk_name:
    return None, "Disk name not specified. Could not determine rotational status"
  try:
    if os.path.isfile('/sys/block/%s/queue/rotational'%disk_name):
      with open ('/sys/block/%s/queue/rotational'%disk_name) as f:
        str = f.read()
        if str.strip() == "1":
          rotational = True
        else:
          rotational = False
    else:
      return None, "Configuration error. Rotational parameter not set for disk %s"%disk_name
  except Exception, e:
    return None, "Error checking disk rotational status : %s"%str(e)
  else:
    return rotational, None

def get_capacity(name):
  #Given the name of a disk (like sda) OR a partition (like sda2), returns the capacity
  capacity = None
  try:
    # Get the storage capacity 
    st1 = os.popen("/sbin/fdisk -l /dev/%s | grep Disk"%name)
    str2 = st1.read()
    disk_capacity = re.search(r'\s[0-9]+[\.0-9]*\s[a-zA-Z]+',str2)
    capacity = (disk_capacity.group()).strip()
  except Exception, e:
    return None, "Error getting disk capacity : %s"%str(e)
  else:
    return capacity, None

def get_serial_number(disk_name):
  #Given the name of a disk (like sda) returns the serial number
  serial_number = None
  try:
    cmd_disk = "/usr/sbin/smartctl -H -i /dev/%s"%disk_name
    dl_output = os.popen(cmd_disk).read()
    lines = re.split("\r?\n", dl_output)
    reobj1 = re.compile("(.*Number:.*)")

    for line in lines:
      #print line
      if reobj1.search(line):
        sn = re.search(r':\s+\S+', line)
        if sn:
          serial_number = sn.group().strip(": ")
  except Exception, e:
    return None, "Error getting disk serial number : %s"%str(e)
  else:
    return serial_number, None

def get_partitions_on_a_disk(disk_name, dl = None):
  #Given a disk name like sda, returns all the partitions info like sda1, sda2, etc
  l = []
  try:
    if not disk_name:
      return None, "No disk name specified so cannot retrieve partitions"
    if not dl:
      dl, err =  _get_disk_info_list()
    if not dl:
      if err:
        raise "Error retrieving partitions, could not read disk info : %s"%err
      else:
        raise "Error retrieving partitions, could not read disk info "
    for d in dl:
      if disk_name in d["name"] and "part" in d["id"]:
        capacity, err = get_capacity(d["name"])
        if capacity:
          d["capacity"] = capacity
        l.append(d)
  except Exception, e:
    return None, "Error retrieving partitions : %s"%str(e)
  else:
    return l, None

def _diskmap():
  disk_positions = []
  try:
    disknames = {}
    for file in os.listdir('/sys/bus/scsi/devices'):
      m = re.match("^\d", file)
      if m:
        str = '/sys/bus/scsi/devices/' + file + '/block'
        for disk in os.listdir(str):
            disknames[file.split(':')[0]] = disk

    #print disknames
    #print sorted(disknames)
    for key in sorted(disknames):
      #print key, disknames[key]
      td = {}
      str = '/sys/block/' + disknames[key] + '/queue/rotational'
      fh = open(str, "r")
      value = fh.read().strip()
      if value != '0':
        #print sno
        #print "Port:%s,Disk:%s,SerialNo:%s" % (key,disknames[key],sno)
        #td["serial_number"] = sno
        td["scsi_port_number"] = int(key)
        td['name'] = disknames[key]
        disk_positions.append(td)
      fh.close()
  except Exception, e:
    return None, "Error retrieving disk positions : %s"%str(e)
  else:
    return disk_positions, None


def get_disk_info(disk_name, idl = None, diskmap = None):

  #Given a disk name like sda, get the disk info
  return_dict = {}
  try:
    if not diskmap:
      diskmap, err = _diskmap()
    if diskmap:
      #print 'in'
      for d in diskmap:
        #print d
        if d['name'] == disk_name:
          return_dict['scsi_port'] = d['scsi_port_number']
    else:
      emsg = "Error getting disk positions "
      if err:
        emsg += err
      raise Exception(emsg)
    if not idl:
      idl, err =  _get_disk_info_list()
    found = False
    for d in idl:
      if disk_name == d["name"]:
        found = True
        break
    if found:
      return_dict["id"] = d["id"]
      return_dict["name"] = d["name"]
      return_dict["path"] = d["path"]
    capacity, err = get_capacity(disk_name)
    if capacity:
      return_dict['capacity'] = capacity
    serial_number, err = get_serial_number(disk_name)
    if serial_number:
      return_dict['serial_number'] = serial_number
    rotational, err = is_rotational(disk_name)
    if rotational is not None:
      return_dict['rotational'] = rotational
    partitions, err = get_partitions_on_a_disk(disk_name, idl)
    if partitions:
      return_dict['partitions'] = partitions
  except Exception, e:
    return None, "Error getting disk information : %s"%str(e)
  else:
    return return_dict, None

def get_rootfs_device():
  device = None
  try:
    cmd = r"df -P /"
    ret, rc = command.execute_with_rc(cmd)
    if rc != 0:
      err_list = command.get_error_list(ret)
      if err_list:
        err_str = ','.join(err_list)
        raise Exception(err_str)
      else:
        raise Exception("Unknown error")
    
    device_list = command.get_output_list(ret)
    if len(device_list) < 2:
      device = None
    else:
      device_list_str = device_list[len(device_list)-1]
      parts = device_list_str.split()
      if parts:
        device = parts[0]

  except Exception, e:
    return None, "Error getting root FS device: %s"%str(e)
  else:
    return device, None
  
def get_disk_info_all():
  #Returns a structured dict for every disk that is alive
  return_dict = {}
  try:
    diskmap, err = _diskmap()
    if not diskmap:
      errstr = "Could not retrieve disk positions "
      if err:
        errstr = "%s : %s"%(errstr, err)
      raise Exception(errstr)
    dl, err =  _get_disk_info_list()
    if not dl:
      errstr = "Could not retrieve Disk information "
      if err:
        errstr = "%s : %s"%(errstr, err)
      raise Exception(errstr)
    for d in dl:
      if "part" in d["id"]:
        continue
      di_dict, err = get_disk_info(d["name"], dl, diskmap)
      if di_dict:
        return_dict[di_dict["serial_number"]] = di_dict
    root_device, err = get_rootfs_device()
    if root_device:
      found_boot = False
      for sn, disk in return_dict.items():
        if 'partitions' not in disk:
          continue
        for partition in disk['partitions']:
          if partition['path'] == root_device:
            partition['root_partition'] = True
            disk['boot_device'] = True
            found_boot = True
            break
        if found_boot:
          break

  except Exception, e:
    return None, "Error getting complete disk information : %s"%str(e)
  else:
    return return_dict, None




def main():
  pp = pprint.PrettyPrinter(indent=4)
  #print 'Disks by name : '
  #print get_disks_by_name()
  #print 'Disks by id : '
  #print  _get_disk_info_list()
  #print 'is rotational: '
  #print is_rotational('sda')
  #print is_rotational('sdc')

  #print 'Disk info: '
  #d, err = get_disk_info('sdc')
  #pp.pprint(d)
  d, err = get_disk_info_all()
  pp.pprint(d)
  #print 'Disk partitions: '
  #print get_partitions('sda')
  #_diskmap()
  #print get_rootfs_device()

if __name__ == '__main__':
  main()
