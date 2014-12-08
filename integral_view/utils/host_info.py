
import subprocess
import time
import re
import os

#Local command module
import command


def get_host_name():
  """ Returns the Hostname of the local box"""
  return os.uname()[1]

  

def main():

  print "Hostname = " + get_host_name()
  print get_processor_type()
  print get_total_memory()
  print get_uptime_result()
  print get_system_time()
  #print get_ip_info()


if __name__ == "__main__":
  main()

'''
def get_ip_info():
  """ Returns the IP addr, bcast and mask of the local box. Not currently used"""

  if_list = []
  dict = {}
  r = command.execute("ifconfig ")
  #r = command.execute('python /home/bkrram/Documents/software/Django-1.4.3/code/gluster_admin/gluster_admin/utils/test/test_printip.py')
  if r:
    ol = command.get_output_list(r)
    for i in ol:
      hw_index  = i.find("HWaddr ")
      if hw_index != -1:
        if dict:
          if_list.append(dict)
          dict = {}
        dict["mac_addr"] =  i[hw_index+7:].strip()
        match = re.search('^([a-zA-Z_0-9]+)', i)
        if match:
          dict["if_name"] = match.group()
      ip_index  = i.find("inet addr:")
      if ip_index != -1:
        match = re.search('([0-9]+)\.([0-9]+)\.([0-9]+)\.([0-9]+)', i[ip_index:])
        ip = match.group()
        dict["ip"] = ip
      bcast_index  = i.find("Bcast:")
      if bcast_index != -1:
        match = re.search('([0-9]+)\.([0-9]+)\.([0-9]+)\.([0-9]+)', i[bcast_index:])
        bcast = match.group()
        dict["bcast"] = bcast
      mask_index  = i.find("Mask:")
      if mask_index != -1:
        match = re.search('([0-9]+)\.([0-9]+)\.([0-9]+)\.([0-9]+)', i[mask_index:])
        mask = match.group()
        dict["mask"] = mask
  if dict and dict not in if_list:
    if_list.append(dict)
  return if_list    


def get_service_status(service_name):
  """ Returns the service status of the service_name param on the local box"""

  cmd = "service %s status"%service_name
  r = command.execute(cmd)
  if r:
    return command.get_output_list(r)
  else:
    l = ["Could not retrieve status"]
    return l

def get_processor_type():
  cmd = "cat /proc/cpuinfo"
  r = command.execute(cmd)
  if r:
    ol = command.get_output_list(r)
  for line in ol:
    line.strip('\n')
    if "model name" in line:
      return re.sub( ".*model name.*:", "", line,1)

def get_total_memory():
  cmd = "cat /proc/meminfo"
  r = command.execute(cmd)
  if r:
    ol = command.get_output_list(r)
  for line in ol:
    line.strip('\n')
    if "MemTotal" in line:
      print line
      ms = re.sub( ".*MemTotal.*:", "", line,1)
      ml = re.search(r"(\d+)(\D*)", ms).groups()
      num_str = "Could not retrieve"
      if ml:
        unit = "KB"
        if ml[1]:
          unit = ml[1].strip().upper()
        num = 0
        if unit == 'KB':
          try:
            num = int(ml[0].strip())
          except Exception as e:
            num_str = "Could not retrieve"
      return str(num/1024)+'MB'

def get_uptime_result():
  cmd = "uptime"
  uptime = 'Could not retrieve uptime'
  load_average = 'Could not retrieve load average'

  r = command.execute(cmd)
  ol = None
  if r:
    ol = command.get_output_list(r)
  if ol:
    uts = ol[0]
    print uts
    r = re.search(r' up (\d+:\d+)',uts)
    if r:
      ul = r.groups()
      if ul:
        uptime = ul[0]+' hours'
    r = re.search(r'load average: ([\d.]+,[ \d.]+,[ \d.]+)',uts)
    if r:
      lal = r.groups()
      if lal:
        load_average = lal[0]
  return {'uptime':uptime, 'load_average':load_average}
    
def get_system_time():
  date = time.strftime('%a %b %d %H:%M %Z %Y')
  return date
'''
