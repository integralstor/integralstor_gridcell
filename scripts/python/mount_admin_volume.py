
import os, socket, sys, subprocess, logging, shutil
from integralstor_common import common, networking, command, logger, services_management
from integralstor_gridcell import grid_ops, gluster_trusted_pools

def sync_ctdb_files ():
  """
  Syncs CTDB files on the localhost with the mounted admin vol.

  Input:
    ['None']
  Output:
    Returns three variables [ret1,ret2,ret3]:
      ret1 -- True if sync was sucessful, else False
      ret2 -- True if there was a difference, False if they were already in sync
      ret3 -- None if there were no errors/exceptions, 'Error string' otherwise
  """

  is_change = False
  try:
    config_dir, err = common.get_config_dir ()
    if err:
      raise Exception (err)
  
    (ret, rc), err = command.execute_with_rc ('diff "/etc/sysconfig/ctdb" "%s/lock/ctdb"' %str(config_dir))
    if (not err) and (rc != 0):
      shutil.copyfile ('%s/lock/ctdb'%str(config_dir), '/etc/sysconfig/ctdb')
      is_change = True
    (ret, rc), err = command.execute_with_rc ('diff "/etc/ctdb/nodes" "%s/lock/nodes"' %str(config_dir))
    if (not err) and (rc != 0):
      shutil.copyfile ('%s/lock/nodes'%str(config_dir), '/etc/ctdb/nodes')
      is_change = True
    (ret, rc), err = command.execute_with_rc ('diff "/etc/ctdb/public_addresses" "%s/lock/public_addresses"' %str(config_dir))
    if (not err) and (rc != 0):
      shutil.copyfile ('%s/lock/public_addresses'%str(config_dir), '/etc/ctdb/public_addresses')
      is_change = True
  except Exception, e:
    return False, is_change, "Couldn't sync ctdb files: %s" %str(e)
  else:
    return True, is_change, None

def mount_and_configure():
  lg = None
  try:
    lg, err = logger.get_script_logger('Admin volume mounter', '/var/log/integralstor/scripts.log', level = logging.DEBUG)

    logger.log_or_print('Admin volume mounter initiated.', lg, level='info')

    pog, err = grid_ops.is_part_of_grid()
    if err:
      raise Exception(err)
    if pog:
      logger.log_or_print('Checking glusterd service', lg, level='debug')
      service = 'glusterd'
      status, err = services_management.get_service_status([service])
      if err:
	raise Exception(err)
      logger.log_or_print('Service %s status is %s'%(service, status['status_code']), lg, level='debug')
      if status['status_code'] != 0:
	logger.log_or_print('Service %s not started so restarting'%service, lg, level='error')
	subprocess.call(['service', service, 'restart'], shell=False)
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

      is_pooled, err = gluster_trusted_pools.get_peer_list()
      if is_pooled:
	mounted, err = grid_ops.is_admin_vol_mounted_local()
	if not mounted:
	  for admin_gridcell in admin_gridcells:
	    reachable, err = networking.can_ping(admin_gridcell)
	    if reachable:
	      (ret, rc), err = command.execute_with_rc('mount -t glusterfs %s:/%s %s'%(admin_gridcell, admin_vol_name, config_dir))
	      if (not err) and (rc == 0):
		mounted = True
		sync, is_change, error = sync_ctdb_files ()
		if error:
		  # It's only a best-effort, it will try next minute again.
		  pass
		if sync == False:
		  #raise Exception (err)
		  pass
		if sync == True and is_change == True:
		  subprocess.call(['service', 'ctdb', 'restart'], shell=False)

		#subprocess.call(['service', 'ctdb', 'restart'], shell=False)
		#subprocess.call(['service', 'winbind', 'restart'], shell=False)
		#subprocess.call(['service', 'smb', 'restart'], shell=False)
		subprocess.call(['service', 'nginx', 'restart'], shell=False)
		subprocess.call(['service', 'uwsgi', 'restart'], shell=False)
		if ag:
		  subprocess.call(['service', 'salt-master', 'restart'], shell=False)
		  subprocess.call(['service', 'salt-minion', 'restart'], shell=False)
		break
	      else:
		str =  'Mount from %s failed.'%admin_gridcell
		logger.log_or_print(str, lg, level='error')
	  if not mounted:
	    str =  'Failed to mounted admin volume!'
	    logger.log_or_print(str, lg, level='critical')
	else:
	  sync, is_change, err = sync_ctdb_files ()
	  if err:
	    raise Exception (err)
	  if sync == False:
	    raise Exception (err)
	  if sync == True and is_change == True:
	    subprocess.call(['service', 'ctdb', 'restart'], shell=False)

	  logger.log_or_print('Checking services', lg, level='debug')
	  for service in ['nginx']:
	    status, err = services_management.get_service_status([service])
	    if err:
	      raise Exception(err)
	    logger.log_or_print('Service %s status is %s'%(service, status['status_code']), lg, level='debug')
	    if status['status_code'] != 0:
	      logger.log_or_print('Service %s not started so restarting'%service, lg, level='error')
	      subprocess.call(['service', service, 'restart'], shell=False)
	  #UWSGI service config not complete so need to check against the actual process name
	  (ret, rc), err = command.execute_with_rc('pidof uwsgi', shell=True)
	  if rc != 0:
	    logger.log_or_print('Service uwsgi not started so restarting', lg, level='error')
	    subprocess.call(['service', 'uwsgi', 'restart'], shell=False)
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
    st = 'Error mounting admin volume : %s'%e
    logger.log_or_print(st, lg, level='critical')
    return False, st
  else:
    str = 'Admin volume mounter completed.'
    logger.log_or_print(str, lg, level='info')
    return True, None

def main():
  ret, err = mount_and_configure()
  print ret, err
  if err:
    print err
    sys.exit(-1)
    

if __name__ == '__main__':
  main()
