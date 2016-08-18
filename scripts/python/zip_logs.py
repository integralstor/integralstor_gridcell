import salt.client
import os, zipfile,shutil
from integralstor_gridcell import grid_ops
from integralstor_common import common

# Files go in the format of , path where the file exists, and the regex to match for the files
files = [["/var/log/","*message*"],["/var/log/","*boot.log"],"/var/log/nginx/error.log","/var/log/smblog.vfs","/var/log/log.ctdb",["/var/log/samba/","*log.smbd*"],["/var/log/","*dmesg*"]]

folders = ["/var/log/glusterfs","/var/log/samba",common.get_alerts_dir(),"/var/log/integralstor","/var/spool/mail/root","/var/log/salt"]

primary_logs = ["/opt/integralstor/integralstor_gridcell/config/logs/"]

local = salt.client.LocalClient()

def get_logs(minion):
  try: 
    for logs in files:
      if isinstance(logs,list):
        local.cmd(minion,"cp.push_dir",[logs[0],logs[1]])
      else:
        local.cmd(minion,"cp.push",[logs])
    for folder in folders:
      local.cmd(minion,"cp.push_dir",[folder])
    if minion == "gridcell-pri.integralstor.lan":
      for folder in primary_logs:
        local.cmd(minion,"cp.push_dir",[folder])
    
  except Exception,e:
    return False,e
  return True, None

def zip_minion_logs():
  try:
    minions,err = grid_ops.get_accepted_minions()    
    if err:
      raise Exception(err)
    for minion in minions:
      # check if the minion is up or not.
      status = local.cmd(minion,"test.ping")
      if minion in status:
        log_path = "/var/cache/salt/master/minions/%s/files/"%minion
        status,err = get_logs(minion)
        if os.path.isdir(log_path): 
          zipdir(log_path,"/tmp/logs/%s.zip"%minion)
        else:
          with open("/tmp/logs/%s.log"%minion,"w") as f:
            f.write("Unable to get log file in path : %s"%log_path)
      else:
        with open("/tmp/logs/%s.log"%minion,"a+") as f:
          f.write("Minion %s did not respond. Minion possibly down."%minion)
  except Exception,e:
    return False,e
  return True, None

def zipdir(path, name):
  ziph = zipfile.ZipFile(name, "w", zipfile.ZIP_DEFLATED)
  for root, dirs, files in os.walk(path):
    for file in files:
      ziph.write(os.path.join(root, file))
  ziph.close()

if __name__ == "__main__":
  try:
    if os.path.isfile("/tmp/integralstor_logs.zip"):
      os.remove("/tmp/integralstor_logs.zip") 
    path = "/tmp/logs/"
    if not os.path.isdir(path):
      os.mkdir(path)    
    if not os.listdir(path) == []:
      shutil.rmtree(path)
      os.mkdir(path)    
    status ,err = zip_minion_logs() 
    if err:
      raise Exception(e)
    zipdir(path, "/tmp/integralstor_logs.zip")
  except Exception,e :
    print e 
