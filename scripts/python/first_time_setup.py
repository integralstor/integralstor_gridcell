
import fractalio, sys, os, shutil
from fractalio import node_scan, gluster_commands
import salt.client
from pwd import getpwnam

def initiate_setup():
  #The new manifest and status shd have been regenerated so now get the system status dict and use that to generate the admin volume
  pending_nodes = node_scan.get_pending_minions()

  if pending_nodes:
    success, failed, errors = node_scan.add_nodes("System setup process",pending_nodes)
    if (not success) or (errors):
      print "Errors scanning for GRIDCells : %s"%errors
      sys.exit(-1)
    
  else:
    print "No GRIDCells found!"
    return 0

  do_not_proceed = True
  si = system_info.load_system_config(first_time = True)
  primary = None
  secondary = None
  for node_name, node in si.items():
    if "roles" not in node:
      continue
    roles = node["roles"]
    if "primary" in roles:
      primary = node_name
    elif "secondary" in roles:
      secondary = node_name
  if not primary:
    errors += "Could not detect a primary node!"
  if not secondary:
    errors += "Could not detect a secondary node!"
  if primary and secondary:
    cmd = "gluster volume create %s repl 2 %s:%s/%s %s:%s/%s"%(fractalio.common.get_admin_vol_name(), primary, fractalio.common.get_admin_vol_mountpoint(), fractalio.common.get_admin_vol_name(), secondary, fractalio.common.get_admin_vol_mountpoint(), fractalio.common.get_admin_vol_name())
    d = gluster_commands.run_gluster_command(cmd, "%s/create_volume.xml"%fractalio.common.get_devel_files_path(), "Admin volume creation")

    if d and ("op_status" in d) and d["op_status"]["op_ret"] == 0:
      client = salt.client.LocalClient()
      r1 = client.cmd('roles:master', 'cmd.run_all', ['mount -t glusterfs localhost:/%s %s'%(fractalio.common.get_admin_vol_name(), fractalio.common.get_admin_vol_mountpoint())], expr_form='grain')
      if r1:
        for node, ret in r1.items():
          if ret.retcode != 0:
            errors += "Error mounting the admin volume on %s"%node
      if not errors:
        r2 = client.cmd('roles:master', 'mount.set_fstab', [fractalio.common.get_admin_vol_mountpoint(), 'localhost:/%s'%fractalio.common.get_admin_vol_name(), 'nfs', 'rw'], expr_form='grain')
        if r2:
          for node, ret in r2.items():
            if ret not in ["new", "present"]:
              errors += "Error setting the fstab entry for the admin volume on %s"%node
        if not errors:
          #Stop the DNS servers and move the config to the admin volume and the restart it
          r3 = client.cmd('roles:primary', 'cmd.run_all', ['service named stop'], expr_form='grain')
          if r3:
            for node, ret in r3.items():
              if ret.retcode != 0:
                errors += "Error stopping the DNS server on %s"%node
          if not errors:
            shutil.copytree("%s/named"%fractalio.common.get_defaults_dir(), fractalio.common.get_admin_vol_mountpoint())
            named_uid = getpwnam('named').pw_uid
            named_gid = getpwnam('named').pw_gid
            for root, dirs, files in os.walk("%s/named"%fractalio.common.get_admin_vol_mountpoint()):  
              for d in dirs:  
                os.chown(os.path.join(root, d), named_uid, named_gid)
              for f in files:
                os.chown(os.path.join(root, f), named_uid, named_gid)
            r4 = client.cmd('roles:master', 'cmd.run_all', ['service named start'], expr_form='grain')
            if r4:
              for node, ret in r4.items():
                if ret.retcode != 0:
                  errors += "Error starting the DNS server from the new config location on %s"%node
            if not errors:
              #Phew! Finally all ok. Copy the rest of the stuff and go ahead
              shutil.copytree("%s/db"%fractalio.common.get_defaults_dir(), fractalio.common.get_admin_vol_mountpoint())
              shutil.copytree("%s/logs"%fractalio.common.get_defaults_dir(), fractalio.common.get_admin_vol_mountpoint())
              os.mkdir("%s/status"%fractalio.common.get_admin_vol_mountpoint())
              shutil.move("%s/master.manifest"%fractalio.common.get_tmp_path(), fractalio.common.get_system_status_path())
              print "Successfully configured the primary and secondary GRIDCells! You can now use IntegralView to administer the system."
              return 0
    else:
      if "op_status" in d and "op_errstr" in d["op_status"]:
        if d["op_status"]["op_errstr"]:
         errors += "Error creating the administration volume : %s"%d["op_status"]["op_errstr"]
  if errors:
    print "Encountered the following hard errors so could not proceed : %s. Please ensure that the primary and secondary nodes are connected and then try again."%errors
    return -1


def main():
  ret = initiate_setup()

if __name__ == "__main__":
  main()
