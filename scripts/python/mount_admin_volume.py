
import os, socket, sys, subprocess, logging
from integralstor_common import common, networking, command, logger
from integralstor_gridcell import grid_ops

def mount_and_configure():
  lg = None
  try:
    lg, err = logger.get_script_logger('Admin volume mounter', '/var/log/integralstor/scripts.log', level = logging.DEBUG)

    logger.log_or_print('Admin volume mounter initiated.', lg, level='info')

    pog, err = grid_ops.is_part_of_grid()
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

      ag, err = grid_ops.is_admin_gridcell()
      if err:
        raise Exception(err)

      admin_gridcells, err = grid_ops.get_admin_gridcells()
      if err:
        raise Exception(err)

      mounted, err = grid_ops.is_admin_vol_mounted_local()
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
              str =  'Mount from %s failed.'%admin_gridcell
              logger.log_or_print(str, lg, level='warning')
        if not mounted:
          str =  'Failed to mounted admin volume!'
          logger.log_or_print(str, lg, level='critical')
      else:
        str =  'Admin volume is already mounted'
        logger.log_or_print(str, lg, level='info')

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
    str = 'Error mounting admin volume : %s'%str(e)
    logger.log_or_print(str, lg, level='critical')
    return False, str(e)
  else:
    str = 'Admin volume mounter completed.'
    logger.log_or_print(str, lg, level='info')
    return True, None

def main():
  ret, err = mount_and_configure()
  if err:
    print err
    sys.exit(-1)
    

if __name__ == '__main__':
  main()
      
