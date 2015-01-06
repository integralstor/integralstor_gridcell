import salt.client, salt.wheel
import command, audit

def _regenerate_manifest(first_time):
  if first_time:
    path = fractalio.common.get_tmp_path()
  else:
    path = fractalio.common.get_system_status_path()
  manifest_command = "/opt/fractalio/monitoring/generate_manifest.py %s"%path
  command.execute_with_rc(manifest_command)
  status_command = "/opt/fractalio/monitoring/generate_status.py %s"%path
  return (command.execute_with_rc(status_command))

def get_pending_minions():
  opts = salt.config.master_config(fractalio.common.get_salt_master_config())
  wheel = salt.wheel.Wheel(opts)
  keys = wheel.call_func('key.list_all')
  pending_minions = keys['minions_pre']
  return pending_minions

def add_nodes(remote_addr,pending_minions, first_time = False):
  client = salt.client.LocalClient()
  opts = salt.config.master_config(fractalio.common.get_salt_master_config())
  wheel = salt.wheel.Wheel(opts)
  success = []
  failed = []
  errors = None
  ip = None
  r = {}
  if pending_minions:
    for m in pending_minions:
      #print "Accepting %s"%m
      if wheel.call_func('key.accept', match=('%s'%m)):
        command_to = 'salt %s saltutil.sync_all'%(m)
        command.execute(command_to)
        r = client.cmd(m, 'grains.items')
        if r:
          if 'ip_interfaces' in r[m] and r[m]['ip_interfaces']['bond0']:
            ip = r[m]['ip_interfaces']['bond0'][0]
        if ip:
          r1 = client.cmd('roles:master', 'ddns.add_host', ['fractalio.lan', m, 86400, ip], expr_form='grain')
          #r1 = client.cmd(m,'hosts.set_host', [ip, m])
          if not r1:
            errors = "Error adding the DNS information for %s"%m
        else:
            errors = "Error adding the DNS information for %s. No IP address information found."%m
        audit.audit("hardware_scan_node_added", "Added a new node %s to the grid"%m,remote_addr )
        success.append(m)
      else:
        failed.append(m)
    ret, rc = _regenerate_manifest(first_time)
    if rc != 0:
      if errors:
        errors += "Error regenerating the new configuration : "
      else:
        errors = "Error regenerating the new configuration : "
      errors += ",".join(command.get_output_list(ret))
      errors += ",".join(command.get_error_list(ret))

  return (success, failed, errors)
