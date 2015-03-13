import salt.client, salt.wheel, time
import fractalio
from fractalio import command, audit, ctdb

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

def _regenerate_manifest(first_time = False):
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

def get_pending_minions():
  opts = salt.config.master_config(fractalio.common.get_salt_master_config())
  wheel = salt.wheel.Wheel(opts)
  keys = wheel.call_func('key.list_all')
  pending_minions = keys['minions_pre']
  return pending_minions

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

def sync_salt_modules(client):
  rc = client.cmd('*', 'saltutil.sync_modules')
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

def add_nodes_to_grid(remote_addr,pending_minions, first_time = False, accessing_from = 'primary'):

  success = []
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
        print "Error retrieving the IP from GRIDCell %s"%m
        errors += "Error retrieving the IP from GRIDCell %s. "%m
        #Cannot add to DNS so remove from salt as well
        r, err = delete_salt_key(m)
        if (not r) and err:
          errors += err
        failed.append(m)
        continue

      print 'Adding GRIDCell %s to DNS'%m
      rc = add_to_dns(client, m, ip)
      print 'Added GRIDCell %s to DNS'%m
      if rc != 0:
        errors += "Error adding the DNS information for %s. No IP address information found. "%m
        print "Error adding DNS information for GRIDCell %s"%m
        r, err = delete_salt_key(m)
        if (not r) and err:
          errors += err
        failed.append(m)
        continue

      '''
      rc = ctdb.add_to_nodes_file(ip)
      if rc != 0:
        errors += "Error adding the GRIDCell %s to the CTDB nodes file. "%m
        print "Error adding the GRIDCell %s to the CTDB nodes file. "%m
        r = remove_from_dns(client, m)
        if r != 0:
          errors += "Error removing %s from DNS"%m
        r, err = delete_salt_key(m)
        if (not r) and err:
          errors += err
        failed.append(m)
        continue
      '''

      #All went well so audit and continue to the next
      print "Successfully added GRIDCell %s to the grid"%m

      if not first_time:
      	audit.audit("hardware_scan_node_added", "Added a new GRIDCell %s to the grid"%m,remote_addr )
      success.append(m)

    print "Syncing modules to GRIDCells"
    rc = sync_salt_modules(client)
    print "Syncing modules to GRIDCells.. Done."
    print

    #print "Successfully added : %s"%success
    #print "Failed adding : %s"%failed

    print "Regenerating manifest and status"

    ret, rc = _regenerate_manifest(first_time)

    print "Regenerated manifest and status"

    if rc != 0:
      if errors:
        errors += "Error regenerating the new configuration : "
      else:
        errors = "Error regenerating the new configuration : "
      errors += ",".join(command.get_output_list(ret))
      errors += ",".join(command.get_error_list(ret))

  return (success, failed, errors)



def main():
  #_regenerate_manifest(True)
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
    ret, rc = _regenerate_manifest(first_time)
    print "Regenerated manifest and status"
    if rc != 0:
      if errors:
        errors += "Error regenerating the new configuration : "
      else:
        errors = "Error regenerating the new configuration : "
      errors += ",".join(command.get_output_list(ret))
      errors += ",".join(command.get_error_list(ret))
'''
