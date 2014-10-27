#!/usr/bin/python

import salt.client
import json, os, datetime, shutil, sys
import lock

def _gen_manifest_info():
  local = salt.client.LocalClient()
  data = local.cmd('*', 'grains.item', ['disk_info', 'hwaddr_interfaces', 'mem_total', 'fqdn', 'cpu_model'])
  #print data
  if not data:
    return -1, None
  ret = {}
  for k, v in data.items():
    v['interface_info'] = {}
    #Tweak the key names
    if v and 'hwaddr_interfaces' in v and v['hwaddr_interfaces'] :
      for int_name, mac_addr in v['hwaddr_interfaces'].items():
        d = {}
        d['mac_addr'] = mac_addr
        '''
        if 'ip_interfaces' in v and int_name in v['ip_interfaces']:
          d['ip_addr'] = v['ip_interfaces'][int_name]
        else:
          d['ip_addr'] = []
        '''
        v['interface_info'][int_name] = d 

      v.pop('hwaddr_interfaces', None)
      #v.pop('ip_interfaces', None)
    ret[k] = v
    return 0, ret

def gen_manifest(path):
  if not lock.get_lock('generate_manifest'):
    print 'Generate Status : Could not acquire lock. Exiting.'
    return -1
  ret_code = 0
  rc, ret = _gen_manifest_info()
  if rc != 0 :
    ret_code = rc
  else:
    fullpath = os.path.normpath("%s/master.manifest"%path)
    fulltmppath = os.path.normpath("%s/master.manifest.tmp"%path)
    fullcopypath = os.path.normpath("%s/master.manifest.%s"%(path, datetime.datetime.now().strftime("%B_%d_%Y_%H_%M_%S")))
    try:
      #Generate into a tmp file
      with open(fulltmppath, 'w') as fd:
        json.dump(ret, fd, indent=2)
      #Copy original to a backup
      if os.path.isfile(fullpath):
        shutil.copyfile(fullpath, fullcopypath)
      #Now move the tmp to the actual manifest file name
      shutil.move(fulltmppath, fullpath)
    except Exception, e:
      print "Error generating the manifest file : %s"%str(e)
      ret_code = -1
  lock.release_lock('generate_manifest')
  return ret_code

import atexit
atexit.register(lock.release_lock, 'generate_manifest')

def main():

  num_args = len(sys.argv)
  if num_args > 1:
    rc = gen_manifest(os.path.normpath(sys.argv[1]))
  else:
    rc = gen_manifest('/home/bkrram/fractal/integral_view/integral_view/devel/config')
  #print rc
  print rc

if __name__ == "__main__":
  main()
