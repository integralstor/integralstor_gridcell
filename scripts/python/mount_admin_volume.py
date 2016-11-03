
import os, socket, sys, subprocess
from integralstor_common import common, networking, command

def is_part_of_grid():
  part = False
  try:
    platform_root, err = common.get_platform_root()
    if err:
      raise Exception(err)
    if os.path.isfile('%s/part_of_grid'%platform_root):
      part = True
  except Exception, e:
    return False, 'Error checking for grid membership : %s'%str(e)
  else:
    return part, None

def is_admin_gridcell():
  admin = False
  try:
    me = socket.getfqdn()
    platform_root, err = common.get_platform_root()
    if err:
      raise Exception(err)
    if os.path.isfile('%s/admin_gridcells'%platform_root):
      lines = []
      with open('%s/admin_gridcells'%platform_root, 'r') as f:
        lines = f.readlines()
      for line in lines:
        if line.strip() == me:
          admin = True
          break
  except Exception, e:
    return False, 'Error checking for admin grid membership : %s'%str(e)
  else:
    return admin, None
    
def get_admin_gridcells():
  admin_gridcells = []
  try:
    platform_root, err = common.get_platform_root()
    if err:
      raise Exception(err)
    if os.path.isfile('%s/admin_gridcells'%platform_root):
      lines = []
      with open('%s/admin_gridcells'%platform_root, 'r') as f:
        lines = f.readlines()
      admin_gridcells = [line.strip() for line in lines]
  except Exception, e:
    return None, 'Error getting admin GRIDCells: %s'%str(e)
  else:
    return admin_gridcells, None

def is_admin_vol_mounted():
  mounted = False
  try:
    admin_vol_name, err = common.get_admin_vol_name()
    if err:
      raise Exception(err)
    config_dir, err = common.get_config_dir()
    if err:
      raise Exception(err)
    with open('/proc/self/mounts', 'r') as f:
      for line in f:
        if admin_vol_name in line and config_dir in line:
          mounted = True
          break
  except Exception, e:
    return False, 'Error checking if admin volume is mounted : %s'%str(e)
  else:
    return mounted, None


def mount_and_configure():
  try:
    pog, err = is_part_of_grid()
    if err:
      raise Exception(err)
    if pog:
      admin_vol_name, err = common.get_admin_vol_name()
      if err:
        raise Exception(err)

      #Get the config dir - the mount point.
      config_dir, err = common.get_config_dir()
      if err:
        raise Exception(err)

      ag, err = is_admin_gridcell()
      if err:
        raise Exception(err)

      admin_gridcells, err = get_admin_gridcells()
      if err:
        raise Exception(err)

      mounted, err = is_admin_vol_mounted()
      if not mounted:
        for admin_gridcell in admin_gridcells:
          reachable, err = networking.can_ping(admin_gridcell)
          if reachable:
            (ret, rc), err = command.execute_with_rc('mount -t glusterfs %s:/%s %s'%(admin_gridcell, admin_vol_name, config_dir))
            if (not err) and (rc == 0):
              mounted = True
              subprocess.call(['service', 'ctdb', 'restart'], shell=False)
              subprocess.call(['service', 'winbind', 'restart'], shell=False)
              subprocess.call(['service', 'nginx', 'restart'], shell=False)
              subprocess.call(['service', 'uwsgi', 'restart'], shell=False)
              if ag:
                subprocess.call(['service', 'salt-master', 'restart'], shell=False)
                subprocess.call(['service', 'salt-minion', 'restart'], shell=False)
              break
            else:
              print 'Mount from %s failed.'%admin_gridcell
      else:
        print 'Admin volume is already mounted'

      '''
      if mounted:
        path_dict = {'/etc/krb5.conf':'%s/lock/krb5.conf'%config_dir, '/etc/samba/smb.conf':'%s/lock/smb.conf'%config_dir, '/etc/ctdb/nodes':'%s/lock/smb.conf'%config_dir, '/etc/sysconfig/ctdb':'%s/lock/ctdb'%config_dir}
        for link, file in path_dict.items():
          if os.path.islink(link) or os.path.isfile(link):
            print link, 'exists so removing'
            os.remove(link)
          os.symlink(file, link)
      else:
        raise Exception('Could not mount the admin volume')
      '''
  except Exception, e:
    return False, str(e)
  else:
    return True, None

def main():
  ret, err = mount_and_configure()
  if err:
    print err
    sys.exit(-1)
    

if __name__ == '__main__':
  main()
      
