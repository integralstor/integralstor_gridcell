import os, re, subprocess, glob
import salt.modules.network, salt.modules.ps, salt.modules.status


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

def disk_status():

  # Initialize a grain dictionary
  grains = {}

  # Some code for logic that sets grains like..

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

  disk_status = {}
  for disk_name in dl:
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
    d["disk_name"] = disk_name
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


def status():
  d = {}
  d["disk_status"] = disk_status()
  d["interface_status"] = interface_status()
  d["load_avg"] = load_avg()
  d["disk_usage"] = disk_usage()
  d["mem_info"] = mem_info()
  return d
      
if __name__ == '__main__':
  print status()
  #print disk_status()
  #print interface_status()
  #print status()
  #print load_avg()
  #print disk_usage()
  #print mem_info()
