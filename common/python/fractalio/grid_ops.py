import salt.client, salt.wheel, time
import fractalio
import socket
from fractalio import command, audit, ctdb, gluster_commands

def _regenerate_manifest_and_status(first_time = False):
  if first_time:
    path = fractalio.common.get_tmp_path()
  else:
    path = fractalio.common.get_system_status_path()
  manifest_command = "/opt/fractalio/scripts/python/generate_manifest.py %s"%path
  ret, rc = command.execute_with_rc(manifest_command)
  if rc != 0:
    return ret, rc
  status_command = "/opt/fractalio/scripts/python/generate_status.py %s"%path
  return (command.execute_with_rc(status_command))

def get_accepted_minions():
  minion_list = []
  try :
    opts = salt.config.master_config(fractalio.common.get_salt_master_config())
    wheel = salt.wheel.Wheel(opts)
    keys = wheel.call_func('key.list_all')
    minion_list = keys['minions']
  except Exception, e:
    return -1, None, "Error retrieving accepted minions : %s"%e
  else:
    return 0, minion_list, None

def get_pending_minions():
  opts = salt.config.master_config(fractalio.common.get_salt_master_config())
  wheel = salt.wheel.Wheel(opts)
  keys = wheel.call_func('key.list_all')
  pending_minions = keys['minions_pre']
  return pending_minions

def restart_minions(client, minion_list):
  try:
    r1 = client.cmd(minion_list, 'cmd.run', ['echo service salt-minion restart | at now + 1 minute'], expr_form='list')
  except Exception, e:
    return -1
  else:
    return 0

def accept_salt_key(wheel, m):
  try:
    if not wheel.call_func('key.accept', match=('%s'%m)):
      print "Error accepting GRIDCell key for %s "%m
      return -1
  except Exception, e:
    print "Error accepting GRIDCell key for %s : %s"%(m, e)
    return -1
  else:
    return 0

def delete_salt_key(hostname):
  try:
    opts = salt.config.master_config(fractalio.common.get_salt_master_config())
    wheel = salt.wheel.Wheel(opts)
    keys = wheel.call_func('key.list_all')
    if (not keys) or ('minions' not in keys) or (hostname not in keys['minions']):
      errors = "Specified GRIDCell is not part of the grid"
      return -1, errors
    wheel.call_func('key.delete', match=(hostname))
  except Exception, e:
    errors = "Error removing GRIDCell key from the grid : %s"%e
    return -1, errors
  else:
    return 0, None

def sync_salt_modules(client, minion_list):
  rc = client.cmd(minion_list, 'saltutil.sync_modules', expr_form='list')
  return rc

def get_minion_ip(client, m):
  ip = None
  try:
    r = client.cmd(m, 'grains.item', ['ip_interfaces'])
    #print r
    if r:
      #print r[m]
      #print r[m]['ip_interfaces']
      #print r[m]['ip_interfaces']['bond0']
      if 'ip_interfaces' in r[m] and r[m]['ip_interfaces']['bond0']:
        ip = r[m]['ip_interfaces']['bond0'][0]
        print "Found Bond IP : %s for GRIDCell %s"%(ip, m)
      else:
        print "Could not retrieve the IP for GRIDCell %s"%m
        return None
    else:
      print "Could not retrieve the IP for GRIDCell %s"%m
      return None
  except Exception, e:
    print "Error retrieving IP for GRIDCell for %s : %s"%(m, e)
    return None
  else:
    return ip

def add_to_dns(client, m, ip):
  try:
    if m in ['fractalio-pri.fractalio.lan', 'fractalio-sec.fractalio.lan', 'fractalio-pri', 'fractalio-sec']:
      # Dont add the primary and secondary because they are alread there!
      return 0
    r1 = client.cmd('roles:primary', 'ddns.add_host', ['fractalio.lan', m, 86400, ip], expr_form='grain', timeout=180)
    #print r1
    #print "Added %s to DNS"%m
    if not r1:
      print "Error adding DNS information for GRIDCell %s"%m
      return -1
    else:
      for key, value in r1.items():
        if value is not None and value==False:
          print "Error adding DNS information for GRIDCell %s"%m
          return -1
      print "Added %s to DNS"%m
      return 0
  except Exception, e:
    print "Error adding GRIDCell %s to DNS : %s"%(m, e)
    return -1
  else:
    return 0

def remove_from_dns(client, m, ip):
  try:
    r1 = client.cmd('roles:primary', 'ddns.delete_host', ['fractalio.lan', m], expr_form='grain', timeout=180)
    print "Removed %s from DNS"%m
    if not r1:
      print "Error removing DNS information for GRIDCell %s"%m
      return -1
    else:
      return 0
  except Exception, e:
    print "Error removing GRIDCell %s from DNS : %s"%(m, e)
    return -1
  else:
    return 0


def link_ctdb_files(client, hostname_list):
  try :
    print "Removing original CTDB config file on GRIDCell %s."%','.join(hostname_list)
    r1 = client.cmd(hostname_list, 'cmd.run_all', ['rm /etc/sysconfig/ctdb'], expr_form='list')
    print "Removed original CTDB config file on GRIDCell %s."%','.join(hostname_list)
    print "Linking the CTDB config file on GRIDCell %s."%','.join(hostname_list)
    r1 = client.cmd(hostname_list, 'cmd.run_all', ['ln -s %s/lock/ctdb /etc/sysconfig/ctdb'%fractalio.common.get_admin_vol_mountpoint()], expr_form='list')
    if r1:
      for node, ret in r1.items():
        #print ret
        if ret["retcode"] != 0:
          errors = "Error linking the CTDB config file on %s"%node
          return -1, errors
    print "Linked the CTDB config file on GRIDCell %s."%','.join(hostname_list)

    print "Removing original CTDB nodes file on GRIDCell %s."%','.join(hostname_list)
    r1 = client.cmd(hostname_list, 'cmd.run_all', ['rm /etc/ctdb/nodes'], expr_form='list')
    print "Removed original CTDB nodes file on GRIDCell %s."%','.join(hostname_list)
    print "Linking the CTDB nodes file on GRIDCell %s."%','.join(hostname_list)
    r1 = client.cmd(hostname_list, 'cmd.run_all', ['ln -s %s/lock/nodes /etc/ctdb/nodes'%fractalio.common.get_admin_vol_mountpoint()], expr_form='list')
    if r1:
      for node, ret in r1.items():
        #print ret
        if ret["retcode"] != 0:
          errors = "Error linking the CTDB nodes file on %s"%node
          #Undo the previous linking
          r1 = client.cmd(hostname_list, 'cmd.run_all', ['rm /etc/sysconfig/ctdb'], expr_form='list')
          return -1, errors
  except Exception, e:
    error_str = str(e)
    print "Encountered the following error : %s"%e
    return -1, error_str
  else:
    print "Linked the CTDB nodes file on GRIDCell %s."%','.join(hostname_list)
    print
    return 0, None

def unlink_ctdb_files(client, hostname_list):
  try :
    r1 = client.cmd(hostname_list, 'cmd.run_all', ['rm /etc/sysconfig/ctdb'], expr_form='list')
    r1 = client.cmd(hostname_list, 'cmd.run_all', ['rm /etc/ctdb/nodes'], expr_form='list')
  except Exception, e:
    error_str = str(e)
    print "Encountered the following error : %s"%e
    return -1, error_str
  else:
    print "Unlinking CTDB files on GRIDCell %s... Done."%','.join(hostname_list)
    print
    return 0, None

def copy_appropriate_rc_local(client, hostname_list, action):
  try :
    if not action:
      return -1, 'No action specified'
    if action not in ['add_to_grid', 'remove_from_grid']:
      return -1, 'Invalied action specified'
    if action == 'add_to_grid':
      cmd = 'cp %s/rc_local/normal/rc.local.in_cluster /etc/rc.local'%fractalio.common.get_defaults_dir()
    else:
      cmd = 'cp %s/rc_local/normal/rc.local.not_in_cluster /etc/rc.local'%fractalio.common.get_defaults_dir()
    #print cmd
    r1 = client.cmd(hostname_list, 'cmd.run_all', [cmd], expr_form='list')
    #print r1
    if r1:
      for node, ret in r1.items():
        #print ret
        if ret["retcode"] != 0:
          errors = "Error copying the apprpriate rc.local on %s"%node
          return -1, errors
  except Exception, e:
    error_str = str(e)
    print "Encountered the following error : %s"%e
    return -1, error_str
  else:
    print "copied the appropriate rc.local on GRIDCell %s."%','.join(hostname_list)
    print
    return 0, None

def start_or_stop_services(client, hostname_list, action):
  try :
    if not action:
      return -1, 'No action specified'
    if action not in ['start', 'stop']:
      return -1, 'Invalied action specified'
    print "%sing ctdb on GRIDCell %s."%(action, ','.join(hostname_list))
    r1 = client.cmd(hostname_list, 'cmd.run_all', ['service ctdb %s'%action], expr_form='list')
    print r1
    if r1:
      for node, ret in r1.items():
        #print ret
        if ret["retcode"] != 0:
          errors = "Error %sing CTDB on %s"%(action, node)
          return -1, errors
    print "%sed ctdb on GRIDCell %s."%(action, ','.join(hostname_list))
    print "%sing winbind on GRIDCell %s."%(action, ','.join(hostname_list))
    r1 = client.cmd(hostname_list, 'cmd.run_all', ['service winbind %s'%action], expr_form='list')
    #print r1
    if r1:
      for node, ret in r1.items():
        #print ret
        if ret["retcode"] != 0:
          errors = "Error %sing winbind on %s"%(action, node)
          return -1, errors
    print "%sed winbind on GRIDCell %s."%(action, ','.join(hostname_list))
  except Exception, e:
    error_str = str(e)
    print "Encountered the following error : %s"%e
    return -1, error_str
  else:
    print "%sed all services on GRIDCells %s... Done."%(action, ','.join(hostname_list))
    print
    return 0, None

def chkconfig_services(client, hostname_list, state):
  try :
    if not state:
      return -1, "No state passed"
    if state not in ['on', 'off']:
      return -1, 'Invalid state passed'
    print "chkconfiging ctdb on GRIDCell %s."%','.join(hostname_list)
    r1 = client.cmd(hostname_list, 'cmd.run_all', ['chkconfig ctdb %s'%state], expr_form='list')
    if r1:
      for node, ret in r1.items():
        #print ret
        if ret["retcode"] != 0:
          errors = "Error chkconfiging CTDB on %s"%node
          return -1, errors
    print "chkconfiged ctdb on GRIDCell %s."%','.join(hostname_list)
    print "chkconfiging winbind on GRIDCell %s."%','.join(hostname_list)
    r1 = client.cmd(hostname_list, 'cmd.run_all', ['chkconfig winbind %s'%state], expr_form='list')
    if r1:
      for node, ret in r1.items():
        #print ret
        if ret["retcode"] != 0:
          errors = "Error chkconfiging winbind on %s"%node
          return -1, errors
    print "chkconfiged winbind on GRIDCell %s."%','.join(hostname_list)
  except Exception, e:
    error_str = str(e)
    print "Encountered the following error : %s"%e
    return -1, error_str
  else:
    print "chkconfiged all services on GRIDCells %s... Done."%','.join(hostname_list)
    print
    return 0, None

def mount_admin_volume(client, hostname_list):
  try :
    print "Mounting the IntegralStor Administration volume on GRIDCells %s."%','.join(hostname_list)
    r1 = client.cmd(hostname_list, 'cmd.run_all', ['mount -t glusterfs fractalio-pri.fractalio.lan:/%s %s'%(fractalio.common.get_admin_vol_name(), fractalio.common.get_admin_vol_mountpoint())], expr_form='list')
    #print r1
    if r1:
      for node, ret in r1.items():
        #print ret
        if ret["retcode"] != 0:
          errors = "Error mounting the admin volume on %s"%node
          return -1, errors
        else:
          print "Admin volume mounted on %s"%node
          print
  except Exception, e:
    error_str = str(e)
    print "Encountered the following error : %s"%e
    return -1, error_str
  else:
    print "Mounting the IntegralStor Administration volume on GRIDCells %s... Done."%','.join(hostname_list)
    print
    return 0, None

def unmount_admin_volume(client, hostname_list):
  try :
    print "Unmounting the IntegralStor Administration volume on GRIDCells %s."%','.join(hostname_list)
    r1 = client.cmd(hostname_list, 'cmd.run_all', ['umount %s'%fractalio.common.get_admin_vol_mountpoint()], expr_form='list')
    #print r1
    if r1:
      for node, ret in r1.items():
        #print ret
        if ret["retcode"] != 0:
          errors = "Error unmounting the admin volume on %s"%node
          return -1, errors
        else:
          print "Admin volume unmounted on %s"%node
          print
  except Exception, e:
    error_str = str(e)
    print "Encountered the following error : %s"%e
    return -1, error_str
  else:
    print "Unmounting the IntegralStor Administration volume on GRIDCells %s... Done."%','.join(hostname_list)
    print
    return 0, None

def set_pool_status(client, hostname_list, part_of_pool):
  try :
    if part_of_pool:
      cmd = 'touch /opt/fractalio/part_of_pool'
    else:
      cmd = 'rm /opt/fractalio/part_of_pool'

    r1 = client.cmd(hostname_list, 'cmd.run_all', [cmd], expr_form='list')
    #print r1
    if r1:
      for node, ret in r1.items():
        #print ret
        if ret["retcode"] not in [0, 1]:
          errors = "Error setting pool status on %s"%node
          return -1, errors
  except Exception, e:
    error_str = str(e)
    print "Encountered the following error : %s"%e
    return -1, error_str
  else:
    print "Setting the pool status on GRIDCell %s... Done."%','.join(hostname_list)
    print
    return 0, None

def revert_add_node_to_storage(si, client, hostname, ip):

  # This is a revert so its a best effort 
  error_list = []
  rc, d, error = gluster_commands.remove_node_from_pool(si, hostname)
  #print d
  #print error
  #print rc
  if rc != 0 and error:
    error_list.append(error)
  rc, error = ctdb.remove_from_nodes_file([ip])
  if rc != 0 and error:
    error_list.append(error)
  if client:
    rc, error = set_pool_status(client, [hostname], False)
    if rc != 0 and error:
      error_list.append(error)
    rc, error = copy_appropriate_rc_local(client, [hostname], 'remove_from_grid')
    if rc != 0 and error:
      error_list.append(error)
    rc, error = start_or_stop_services(client, [hostname], 'stop')
    if rc != 0 and error:
      error_list.append(error)
    rc, error = chkconfig_services(client, [hostname], 'off')
    if rc != 0 and error:
      error_list.append(error)
    rc, error = unlink_ctdb_files(client, [hostname])
    if rc != 0 and error:
      error_list.append(error)
    rc, error = unmount_admin_volume(client, [hostname])
    if rc != 0 and error:
      error_list.append(error)
  return rc, error_list

def add_a_node_to_storage_pool(si, hostname):
  #hosts is a list of dicts with each dict containing the node name and the node info dict (from si)
  ol = []
  error_list = []
  d = None
  client = None
  ip = None

  if not si:
    return -1, None, "Could not determine the configuration of the system!"
  if not hostname: 
    return -1, None, "GRIDCell not found!"
  if hostname not in si:
    return -1, None, "Could not determine the configuration of the GRIDCell!"

    
  try :
    ip = si[hostname]["interfaces"]["bond0"]["inet"][0]["address"]
  except Exception, e:
    pass

  if not ip:
    return -1, None, "Could not determine the IP of thespecified GRIDCell"


  try :
    localhost = socket.getfqdn().strip()
    if hostname.lower().strip() == localhost.lower().strip():
      return -1, None, "Need not add the local host to the pool as it is already a part of the storage pool"
    #print 'adding node'
    rc, d, err  = gluster_commands.add_a_node_to_pool(hostname)
    #print 'added node'
    if rc != 0:
      error_list.append(err)
      rc1, e_list = revert_add_node_to_storage(si, client, hostname, ip)
      if e_list:
        error_list.extend(e_list)
      return rc, d, error_list

    ret, rc = _regenerate_manifest_and_status(False)
    if rc != 0:
      rc1, e_list = revert_add_node_to_storage(si, client, hostname, ip)
      if e_list:
        error_list.extend(e_list)
      return rc, d, error_list
  
    #print 'add ctdbnode'
    rc, err = ctdb.add_to_nodes_file([ip])
    #print 'added ctdbnode'
    if rc != 0:
      error_list.append(err)
      rc1, e_list = revert_add_node_to_storage(si, client, hostname, ip)
      if e_list:
        error_list.extend(e_list)
      return -1, d, error_list
  
    client = salt.client.LocalClient()
    #print '3'
    rc, error = mount_admin_volume(client, [hostname])
    #print '3'
    if rc != 0:
      error_list.append(error)
      rc1, e_list = revert_add_node_to_storage(si, client, hostname, ip)
      if e_list:
        error_list.extend(e_list)
      return -1, d, error_list
    
    #print '4'
    rc, error = link_ctdb_files(client, [hostname])
    #print '4'
    if rc != 0:
      error_list.append(error)
      rc1, e_list = revert_add_node_to_storage(si, client, hostname, ip)
      if e_list:
        error_list.extend(e_list)
      return -1, d, error_list
  
    #print '5'
    rc, error = chkconfig_services(client, [hostname], 'on')
    #print '5'
    if rc != 0:
      error_list.append(error)
      rc1, e_list = revert_add_node_to_storage(si, client, hostname, ip)
      if e_list:
        error_list.extend(e_list)
      return -1, d, error_list

    #print '6'
    rc, error = start_or_stop_services(client, [hostname], 'start')
    #print '6'
    if rc != 0:
      error_list.append(error)
      rc1, e_list = revert_add_node_to_storage(si, client, hostname, ip)
      if e_list:
        error_list.extend(e_list)
      return -1, d, error_list

    #print '7'
    rc, error = copy_appropriate_rc_local(client, hostname, 'add_to_grid')
    #print '7'
    if rc != 0:
      error_list.append(error)
      rc1, e_list = revert_add_node_to_storage(si, client, hostname, ip)
      if e_list:
        error_list.extend(e_list)
      return -1, d, error_list

    #print '8'
    rc, error = set_pool_status(client, [hostname], True)
    #print '8'
    if rc != 0:
      error_list.append(error)
      rc1, e_list = revert_add_node_to_storage(si, client, hostname, ip)
      if e_list:
        error_list.extend(e_list)
      return -1, d, error_list

  except Exception, e:
    error = str(e)
    error_list.append(error)
    return -1, d, error_list
  else:
    return 0, d, None

def revert_remove_node_from_storage(si, client, hostname, ip):

  # This is a revert so its a best effort 
  error_list = []
  rc, d, error = gluster_commands.add_a_node_to_pool(hostname)
  #print d
  #print error
  #print rc
  if rc != 0 and error:
    error_list.append(error)
  rc, error = ctdb.add_to_nodes_file([ip])
  if rc != 0 and error:
    error_list.append(error)
  if client:
    rc, error = mount_admin_volume(client, [hostname])
    if rc != 0 and error:
      error_list.append(error)
    rc, error = link_ctdb_files(client, [hostname])
    if rc != 0 and error:
      error_list.append(error)
    rc, error = chkconfig_services(client, [hostname], 'on')
    if rc != 0 and error:
      error_list.append(error)
    rc, error = start_or_stop_services(client, [hostname], 'start')
    if rc != 0 and error:
      error_list.append(error)
    rc, error = copy_appropriate_rc_local(client, hostname, 'add_to_grid')
    if rc != 0 and error:
      error_list.append(error)
    rc, error = set_pool_status(client, [hostname], True)
    if rc != 0 and error:
      error_list.append(error)
  return rc, error_list

def remove_a_node_from_storage_pool(si, hostname):
  client = None
  ip = None
  error_list = []
  d = None

  try :
    ip = si[hostname]["interfaces"]["bond0"]["inet"][0]["address"]
  except Exception, e:
    pass
  try :
    client = salt.client.LocalClient()
    #print '8'
    rc, error = set_pool_status(client, [hostname], False)
    #print rc
    #print error
    #print '8'
    if rc != 0:
      error_list.append(error)
      rc1, e_list = revert_remove_node_from_storage(si, client, hostname, ip)
      if e_list:
        error_list.extend(e_list)
      return -1, d, error_list

    #print '7'
    rc, error = copy_appropriate_rc_local(client, hostname, 'remove_from_grid')
    #print '7'
    if rc != 0:
      error_list.append(error)
      rc1, e_list = revert_remove_node_from_storage(si, client, hostname, ip)
      if e_list:
        error_list.extend(e_list)
      return -1, d, error_list
    #print '6'
    rc, error = start_or_stop_services(client, [hostname], 'stop')
    #print '6'
    if rc != 0:
      error_list.append(error)
      rc1, e_list = revert_remove_node_from_storage(si, client, hostname, ip)
      if e_list:
        error_list.extend(e_list)
      return -1, d, error_list
    #print '5'
    rc, error = chkconfig_services(client, [hostname], 'off')
    #print '5'
    if rc != 0:
      error_list.append(error)
      rc1, e_list = revert_remove_node_from_storage(si, client, hostname, ip)
      if e_list:
        error_list.extend(e_list)
      return -1, d, error_list
    #print '4'
    rc, error = unlink_ctdb_files(client, [hostname])
    #print '4'
    if rc != 0:
      error_list.append(error)
      rc1, e_list = revert_remove_node_from_storage(si, client, hostname, ip)
      if e_list:
        error_list.extend(e_list)
      return -1, d, error_list
    #print '3'
    rc, error = unmount_admin_volume(client, [hostname])
    #print '3'
    if rc != 0:
      error_list.append(error)
      rc1, e_list = revert_remove_node_from_storage(si, client, hostname, ip)
      if e_list:
        error_list.extend(e_list)
      return -1, d, error_list
    #print 'ctdbnode'
    rc, err = ctdb.remove_from_nodes_file([ip])
    #print 'ctdbnode'
    if rc != 0:
      error_list.append(err)
      rc1, e_list = revert_remove_node_from_storage(si, client, hostname, ip)
      if e_list:
        error_list.extend(e_list)
      return -1, d, error_list
    #print 'removing node'
    rc, d, err  = gluster_commands.remove_node_from_pool(si, hostname)
    #print 'removing node'
    if rc != 0:
      error_list.append(err)
      rc1, e_list = revert_remove_node_from_storage(si, client, hostname, ip)
      if e_list:
        error_list.extend(e_list)
      return rc, d, error_list
  except Exception, e:
    error = str(e)
    error_list.append(error)
    return -1, d, error_list
  else:
    return 0, d, None

def add_nodes_to_grid(remote_addr,pending_minions, first_time = False, accessing_from = 'primary'):

  success = []
  accepted_failed_minions = []
  failed = []
  errors = ""

  if pending_minions:

    ip = None
    client = salt.client.LocalClient()
    opts = salt.config.master_config(fractalio.common.get_salt_master_config())
    wheel = salt.wheel.Wheel(opts)

    print "Accepting the following GRIDCells : %s"%','.join(pending_minions)
    
    for m in pending_minions:

      ip = None
      print "Accepting GRIDCell %s"%m
      rc = accept_salt_key(wheel, m)
      if rc != 0:
        print "Failed to add %s to salt"%m
        errors += "Failed to add %s to salt. "%m
        failed.append(m)
        continue
      print "Accepted GRIDCell %s"%m

    time.sleep(20)
    for m in pending_minions:
      ip = get_minion_ip(client, m)
      if not ip:
        accepted_failed_minions.append(m)
        print "Error retrieving the IP from GRIDCell %s"%m
        errors += "Error retrieving the IP from GRIDCell %s. "%m
        #Cannot add to DNS so remove from salt as well
        failed.append(m)
        continue

      print 'Adding GRIDCell %s to DNS'%m
      rc = add_to_dns(client, m, ip)
      print 'Added GRIDCell %s to DNS'%m
      if rc != 0:
        accepted_failed_minions.append(m)
        errors += "Error adding the DNS information for %s. No IP address information found. "%m
        print "Error adding DNS information for GRIDCell %s"%m
        failed.append(m)
        continue


      #All went well so audit and continue to the next
      print "Successfully added GRIDCell %s to the grid"%m

      if not first_time:
      	audit.audit("hardware_scan_node_added", "Added a new GRIDCell %s to the grid"%m,remote_addr )
      success.append(m)

    #Some failed so kick off minion restart and then delete their keys
    if accepted_failed_minions:
      restart_minions(client, accepted_failed_minions)
      for m in accepted_failed_minions:
        r, err = delete_salt_key(m)
        if (not r) and err:
          errors += err

    if success:
      print "Syncing modules to GRIDCells"
      rc = sync_salt_modules(client, success)
      print "Syncing modules to GRIDCells.. Done."
      print

      #print "Successfully added : %s"%success
      #print "Failed adding : %s"%failed

      print "Regenerating manifest and status"

      ret, rc = _regenerate_manifest_and_status(first_time)


      if rc != 0:
        if errors:
          errors += "Error regenerating the new configuration : "
        else:
          errors = "Error regenerating the new configuration : "
        errors += ",".join(command.get_output_list(ret))
        errors += ",".join(command.get_error_list(ret))
      else:
        print "Regenerated manifest and status"

  return (success, failed, errors)



def main():
  #_regenerate_manifest_and_status(True)
  add_nodes_to_grid("1.1.1.1",['a', 'b'], first_time = False, accessing_from = 'primary')

if __name__ == "__main__":
  main()

'''
      if wheel.call_func('key.accept', match=('%s'%m)):
	      time.sleep(20)
        command_to = 'salt %s saltutil.sync_all'%(m)
        ret, ret_code = command.execute_with_rc(command_to)
        #print ret, ret_code
        time.sleep(20)
        r = client.cmd(m, 'grains.item', ['ip_interfaces'], timeout=180)
        #print r
        if r:
          #print r[m]
          #print r[m]['ip_interfaces']
          #print r[m]['ip_interfaces']['bond0']
          if 'ip_interfaces' in r[m] and r[m]['ip_interfaces']['bond0']:
            ip = r[m]['ip_interfaces']['bond0'][0]
            print "Found Bond IP : %s"%ip
          else:
            print "Could not find the Bond IP"
        if ip:
          print "Adding %s to DNS"%m
          r1 = client.cmd('roles:primary', 'ddns.add_host', ['fractalio.lan', m, 86400, ip], expr_form='grain', timeout=180)
          print "Added %s to DNS"%m
          if not r1:
            errors = "Error adding the DNS information for GRIDCell %s"%m
            print "Error adding DNS information for GRIDCell %s"%m
          else:
            audit.audit("hardware_scan_node_added", "Added a new GRIDCell %s to the grid"%m,remote_addr )
            success.append(m)
        else:
            errors = "Error adding the DNS information for %s. No IP address information found."%m
            print "Error retrieving the IP from GRIDCell %s"%m
      else:
        failed.append(m)
    #print "Successfully added : %s"%success
    #print "Failed adding : %s"%failed
    print "Regenerating manifest and status"
    ret, rc = _regenerate_manifest_and_status(first_time)
    print "Regenerated manifest and status"
    if rc != 0:
      if errors:
        errors += "Error regenerating the new configuration : "
      else:
        errors = "Error regenerating the new configuration : "
      errors += ",".join(command.get_output_list(ret))
      errors += ",".join(command.get_error_list(ret))
'''
