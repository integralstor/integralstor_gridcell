import shutil
import fractalio
from fractalio import common

def add_to_nodes_file(ip_list):
  try :
    if not ip_list:
      raise "No IPs to add to the CTDB nodes file!"
    with open('/etc/ctdb/nodes', 'a') as f:
      for ip in ip_list:
        f.write("%s\n"%ip)
  except Exception, e:
    errors = "Error adding IPs to the CTDB Nodes file : %s"%e
    return -1, errors
  else:
    return 0, None

def remove_from_nodes_file(ip_list):
  #COMPLETE THIS!!!
  try:
    with open('/tmp/ctdb_nodes_file', 'w') as f1:
      with open('%s/lock/nodes'%common.get_admin_vol_mountpoint(), 'r') as f:
        for line in f:
          if line.strip() in ip_list:
            continue
          else:
            f1.write('%s\n'%line.strip())
    shutil.move('/tmp/ctdb_nodes_file', '%s/lock/nodes'%common.get_admin_vol_mountpoint())
  except Exception, e:
    errors = "Error removing IPs from the CTDB Nodes file : %s"%e
    return -1, errors
  else:
    return 0, None

def create_config_file():

  try :
    with open("/etc/sysconfig/ctdb", "w") as f:
      f.write("CTDB_RECOVERY_LOCK=%s/lock/lockfile\n"%common.get_admin_vol_mountpoint())
      f.write("CTDB_MANAGES_SAMBA=yes\n")
      f.write("CTDB_NODES=/etc/ctdb/nodes")
      f.close()
  except Exception, e:
    return -1, "Error creating ctdb config file : %s"%e
  else:
    return 0, None
