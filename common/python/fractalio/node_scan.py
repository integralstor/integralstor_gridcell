import salt.client, salt.wheel, time
import command, audit,fractalio

def _regenerate_manifest(first_time = False):
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

def add_nodes(remote_addr,pending_minions, first_time = False, accessing_from = 'primary'):
  client = salt.client.LocalClient()
  opts = salt.config.master_config(fractalio.common.get_salt_master_config())
  wheel = salt.wheel.Wheel(opts)
  success = []
  failed = []
  errors = None
  ip = None
  r = {}
  if pending_minions:
    print "Accepting the following GRIDCells : %s"%','.join(pending_minions)
    for m in pending_minions:
      ip = None
      print "Accepting %s"%m
      if wheel.call_func('key.accept', match=('%s'%m)):
        command_to = 'salt %s saltutil.sync_all'%(m)
        ret, ret_code = command.execute_with_rc(command_to)
        #print ret, ret_code
        #time.sleep(5)
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
          if first_time:
            r1 = client.cmd('roles:primary', 'ddns.add_host', ['fractalio.lan', m, 86400, ip], expr_form='grain', timeout=180)
          else:
            if accessing_from == 'primary':
              r1 = client.cmd('roles:primary', 'ddns.add_host', ['fractalio.lan', m, 86400, ip], expr_form='grain', timeout=180)
            else:
              r1 = client.cmd('roles:secondary', 'ddns.add_host', ['fractalio.lan', m, 86400, ip], expr_form='grain', timeout=180)
          print "Added %s to DNS"%m
          #r1 = client.cmd(m,'hosts.set_host', [ip, m])
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

  return (success, failed, errors)

def main():
  _regenerate_manifest(True)

if __name__ == "__main__":
  main()
