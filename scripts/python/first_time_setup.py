
import fractalio, sys, os, shutil
from fractalio import node_scan, gluster_commands, system_info
import salt.client
from pwd import getpwnam

def initiate_setup():
  errors = ""
  #The new manifest and status shd have been regenerated so now get the system status dict and use that to generate the admin volume
  print "Scanning the network for GRIDCells .."
  print
  pending_nodes = node_scan.get_pending_minions()
  if pending_nodes:
    print "Found the following GRIDCells : %s"%",".join(pending_nodes)
    print
    success, failed, errors = node_scan.add_nodes("System setup process",pending_nodes, first_time = True)
    if (not success) or (errors):
      print "Errors scanning for GRIDCells : %s"%errors
      print
      sys.exit(-1)
    
  else:
    print "No GRIDCells found!"
    print
    return 0
  do_not_proceed = True
  print "Loading GRIDCell information"
  print
  si = system_info.load_system_config(first_time = True)
  print "Loading GRIDCell information...Done."
  print
  primary = None
  secondary = None
  print "Checking for primary and secondary GRIDCell presence."
  for node_name, node in si.items():
    if "roles" not in node:
      continue
    roles = node["roles"]
    if "primary" in roles:
      primary = node_name
    elif "secondary" in roles:
      secondary = node_name
  if not primary:
    print "Could not detect a primary GRIDCell!"
    print "Exiting.."
    return -1
  if not secondary:
    print "Could not detect a secondary node!"
    print "Exiting.."
    return -1
  print "Detected primary GRIDCell : %s"%primary
  print
  print "Detected secondary GRIDCell : %s"%secondary
  print
  print "Checking for primary and secondary GRIDCell presence... Done."
  print
  print
  print "Creating an initial storage pool with the primary and secondary GRIDCells."
  print
  d = gluster_commands.run_gluster_command('gluster peer probe %s --xml'%secondary, '', 'Adding nodes to cluster')
  if d and ("op_status" in d) and d["op_status"]["op_ret"] == 0:
    print "Creating an initial storage pool with the primary and secondary GRIDCells... Done"
    print
  else:
    err = ""
    if "op_status" in d and "op_errstr" in d["op_status"]:
      err = d["op_status"]["op_errstr"]
    if "op_errno" in d["op_status"]:
      err += "Error number : %d"%d["op_status"]["op_errno"]
    print "Error creating the storage pool : %s"%err
    print "Please check to make sure that glusterd is running on the primary and secondary nodes."
    print "Exiting now.."
    return -1
  #Test d here!
  print "Creating the IntegralStor Administration Volume."
  print
  cmd = "gluster --mode=script volume create %s repl 2 %s:/frzpool/normal/%s %s:/frzpool/normal/%s --xml"%(fractalio.common.get_admin_vol_name(), primary,  fractalio.common.get_admin_vol_name(), secondary, fractalio.common.get_admin_vol_name())
  #print cmd
  d = gluster_commands.run_gluster_command(cmd, "%s/create_volume.xml"%fractalio.common.get_devel_files_path(), "Admin volume creation")
  if d and ("op_status" in d) and d["op_status"]["op_ret"] == 0:
    print "Creating the IntegralStor Administration Volume... Done."
    print
  else:
    err = ""
    if "op_status" in d and "op_errstr" in d["op_status"]:
      err = d["op_status"]["op_errstr"]
    if "op_errno" in d["op_status"]:
      err += ". Error number %d"%d["op_status"]["op_errno"]
    print "Error creating the admin volume : %s"%err
    print "Exiting now.."
    return -1
  #print d

  #print 'mount -t glusterfs localhost:/%s %s'%(fractalio.common.get_admin_vol_name(), fractalio.common.get_admin_vol_mountpoint())
  print "Starting the IntegralStor Administration Volume."
  d = gluster_commands.run_gluster_command('gluster volume start %s --xml'%fractalio.common.get_admin_vol_name(), '', 'Starting admin vol')
  if d and ("op_status" in d) and d["op_status"]["op_ret"] == 0:
    print "Starting the IntegralStor Administration Volume... Done."
    print
  else:
    err = ""
    if "op_status" in d and "op_errstr" in d["op_status"]:
      err = d["op_status"]["op_errstr"]
    if "op_errno" in d["op_status"]:
      err += ". Error number %d"%d["op_status"]["op_errno"]
    print "Error starting the admin volume : %s"%err
    print "Exiting now.."
    return -1
  #print d
  print "Mounting the IntegralStor Administration volume on the primary and secondary GRIDCells."
  client = salt.client.LocalClient()
  r1 = client.cmd('roles:master', 'cmd.run_all', ['mount -t glusterfs localhost:/%s %s'%(fractalio.common.get_admin_vol_name(), fractalio.common.get_admin_vol_mountpoint())], expr_form='grain')
  if r1:
    for node, ret in r1.items():
      #print ret
      if ret["retcode"] != 0:
        errors = "Error mounting the admin volume on %s"%node
        print errors
        print "Exiting now.."
        return -1
      else:
        print "Admin volume mounted on %s"%node
        print
  print "Mounting the IntegralStor Administration volume on the primary and secondary GRIDCells... Done."
  print

  print "Setting the IntegralStor Administration volume to mount on reboot on the primary and secondary GRIDCells."
  print
  r2 = client.cmd('roles:master', 'mount.set_fstab', [fractalio.common.get_admin_vol_mountpoint(), 'localhost:/%s'%fractalio.common.get_admin_vol_name(), 'nfs', 'rw'], expr_form='grain')
  if r2:
    for node, ret in r2.items():
      if ret not in ["new", "present"]:
        errors = "Error setting the fstab entry for the admin volume on %s"%node
        print errors
        print "Exiting now.."
        return -1
      else:
        print "Set the admin volume fstab entry on GRIDCell %s"%node
  print "Setting the IntegralStor Administration volume to mount on reboot on the primary and secondary GRIDCells... Done."
  print

  '''
  print "Stopping the DNS server on the primary and secondary GRIDCells."
  print
  #Stop the DNS servers and move the config to the admin volume and the restart it
  r3 = client.cmd('roles:primary', 'cmd.run_all', ['service named stop'], expr_form='grain')
  if r3:
    for node, ret in r3.items():
      if ret["retcode"] != 0:
        errors = "Error stopping the DNS server on %s"%node
        print errors
        print "Exiting now.."
        return -1
      else:
        print "Stopped the DNS server on GRIDCell %s"%node

  print "Stopping the DNS server on the primary and secondary GRIDCells... Done."
  print

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
        if ret["retcode"] != 0:
          errors += "Error starting the DNS server from the new config location on %s"%node
  '''

  #Phew! Finally all ok. Copy the rest of the stuff and go ahead
  print "Copying the default configuration onto the IntegralStor administration volume."
  print
  shutil.copytree("%s/db"%fractalio.common.get_defaults_dir(), "%s/db"%fractalio.common.get_admin_vol_mountpoint())
  shutil.copytree("%s/logs"%fractalio.common.get_defaults_dir(), "%s/logs"%fractalio.common.get_admin_vol_mountpoint())
  os.mkdir("%s/status"%fractalio.common.get_admin_vol_mountpoint())
  shutil.move("%s/master.manifest"%fractalio.common.get_tmp_path(), fractalio.common.get_system_status_path())
  shutil.move("%s/master.status"%fractalio.common.get_tmp_path(), fractalio.common.get_system_status_path())
  print "Copying the default configuration onto the IntegralStor administration volume... Done."
  print
  return 0


def main():
  i = 0
  while i < 40:
    print
    i += 1
  print "Welcome to the initial setup of your IntegralStor system.".center(80, ' ')
  i = 0
  while i < 10:
    print
    i += 1
  print "Please ensure that all your GRIDCells are connected to the network and powered on. It is especially important that the primary and secondary GRIDCells are powered on and connected for this process to complete successfully.".center(80, ' ')
  print
  print
  print
  inp = raw_input ("Press <Enter> when you are ready to proceed : ")
  print "Continuing"
  ret = initiate_setup()
  if ret == 0:
    print "Successfully configured the primary and secondary GRIDCells! You can now use IntegralView to administer the system.".center(80, ' ')

if __name__ == "__main__":
  main()
