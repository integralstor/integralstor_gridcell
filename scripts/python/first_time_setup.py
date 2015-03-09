
import salt.wheel
import fractalio, sys, os, shutil
from fractalio import grid_ops, gluster_commands, system_info, ctdb
import salt.client
from pwd import getpwnam
import shutil
from time import strftime

def scan_for_nodes():
  try :
    print "Scanning the network for GRIDCells .."
    print
    pending_nodes = grid_ops.get_pending_minions()
    if pending_nodes:
      print "Found the following GRIDCells : %s"%",".join(pending_nodes)
      print
      success, failed, err = grid_ops.add_nodes_to_grid("System setup process",pending_nodes, first_time = True)
      if (not success) or (err):
        print "Errors scanning for GRIDCells : %s"%err
        print
        return -1
    else:
      print "No GRIDCells found!"
      print
      return 0
  except Exception, e:
    print "Encountered the following error : %s"%e
    return -1
  else:
    print "Scanning the network for GRIDCells.. Done."
    print
    return 0


def remove_nodes_from_grid():
  try :
    print "Disconnecting GRIDCells.."
    print
    rc, minions, err = grid_ops.get_accepted_minions()
    if rc != 0:
      if err:
        raise Exception("Error retrieving accepted minion list")
      else:
        raise Exception(err)
    if minions:
      for minion in minions:
        print "Disconnecting GRIDCell %s"%minion
        rc, err = grid_ops.delete_salt_key(minion)
        if rc != 0:
          if err:
            raise Exception (err)
          else:
            raise Exception ("Unknown error occurred")
  except Exception, e:
    print "Error disconnecting GRIDCells : %s"%e
    return -1
  else:
    print "Disconnecting GRIDCells.. Done."
    print
    return 0

def check_for_primary_and_secondary(si):
  try :
    primary = None
    secondary = None
    print "Checking for primary and secondary GRIDCell presence."
    print
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
      return -1
    print "Detected primary GRIDCell : %s"%primary
    print
    if not secondary:
      print "Could not detect a secondary node!"
      return (-1, primary, secondary)
    print "Detected secondary GRIDCell : %s"%secondary
    print
  except Exception, e:
    print "Encountered the following error : %s"%e
    return -1, None, None
  else:
    print "Checking for primary and secondary GRIDCell presence.. Done."
    print
    return (0, primary, secondary)

'''
def create_storage_pool():
  try :
    print "Creating an initial storage pool with the primary and secondary GRIDCells..."
    print
    d = gluster_commands.run_gluster_command('gluster peer probe %s --xml'%secondary, '', 'Adding nodes to cluster')
    if d and ("op_status" in d) and d["op_status"]["op_ret"] == 0:
      print "Creating an initial storage pool with the primary and secondary GRIDCells... Done"
      print
      return 0
    else:
      err = ""
      if "op_status" in d and "op_errstr" in d["op_status"]:
        err = d["op_status"]["op_errstr"]
      if "op_errno" in d["op_status"]:
        err += "Error number : %d"%d["op_status"]["op_errno"]
      print "Error creating the storage pool : %s"%err
      print "Please check to make sure that glusterd is running on the primary and secondary nodes."
      return -1
  except Exception, e:
    print "Encountered the following error : %s"%e
    return -1
  else:
    print "Creating an initial storage pool with the primary and secondary GRIDCells... Done."
    print
    return 0
'''

def empty_storage_pool(si, secondary):
  try :
    print "Removing the initial storage pool with the primary and secondary GRIDCells..."
    print
    rc, d, err = gluster_commands.remove_node_from_pool(si, secondary)
  except Exception, e:
    print "Encountered the following error : %s"%e
    return -1
  else:
    print "Removing the initial storage pool with the primary and secondary GRIDCells... Done."
    print
    return 0
    

def create_admin_volume(client, primary, secondary):

  try :
    print "Creating the IntegralStor Administration volume.."
    print

    print "Creating the bricks for the admin volume"
    r1 = client.cmd('roles:master', 'cmd.run_all', ['zfs create frzpool/normal/%s'%(fractalio.common.get_admin_vol_name())], expr_form='grain')
    if r1:
      for node, ret in r1.items():
        #print ret
        if ret["retcode"] != 0:
          errors = "Error creating the brick path ZFS dataset on %s"%node
          print errors
          print "Exiting now.."
          return -1
        else:
          print "Brick path ZFS dataset created on %s"%node
          print

    print "Creating the IntegralStor Administration Volume."
    print

    cmd = "gluster --mode=script volume create %s repl 2 %s:/frzpool/normal/%s %s:/frzpool/normal/%s force --xml"%(fractalio.common.get_admin_vol_name(), primary,  fractalio.common.get_admin_vol_name(), secondary, fractalio.common.get_admin_vol_name())
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
    
  except Exception, e:
    print "Encountered the following error : %s"%e
    return -1
  else:
    print "Creating the IntegralStor Administration volume.. Done."
    print
    return 0


def remove_admin_volume(client):
  try :
    print "Removing the IntegralStor Administration volume.."
    print

    print "Stopping the IntegralStor Administration Volume."
    d = gluster_commands.run_gluster_command('gluster volume stop %s force --xml'%fractalio.common.get_admin_vol_name(), '', 'Stopping admin vol')
    if d and ("op_status" in d) and d["op_status"]["op_ret"] == 0:
      print "Stopping the IntegralStor Administration Volume... Done."
      print
    else:
      err = ""
      if "op_status" in d and "op_errstr" in d["op_status"]:
        err = d["op_status"]["op_errstr"]
      if "op_errno" in d["op_status"]:
        err += ". Error number %d"%d["op_status"]["op_errno"]
      print "Error stopping the admin volume : %s"%err

    cmd = "gluster volume delete %s force --xml"%fractalio.common.get_admin_vol_name()
    #print cmd
    d = gluster_commands.run_gluster_command(cmd, "%s/delete_volume.xml"%fractalio.common.get_devel_files_path(), "Admin volume deletion")
    if d and ("op_status" in d) and d["op_status"]["op_ret"] == 0:
      print "Deleting the IntegralStor Administration Volume... Done."
      print
    else:
      err = ""
      if "op_status" in d and "op_errstr" in d["op_status"]:
        err = d["op_status"]["op_errstr"]
      if "op_errno" in d["op_status"]:
        err += ". Error number %d"%d["op_status"]["op_errno"]
      print "Error deleting the admin volume : %s"%err

    print "Deleting the bricks for the admin volume"
    r1 = client.cmd('roles:master', 'cmd.run_all', ['zfs destroy frzpool/normal/%s'%(fractalio.common.get_admin_vol_name())], expr_form='grain')
    if r1:
      for node, ret in r1.items():
        #print ret
        if ret["retcode"] != 0:
          errors = "Error deleting the brick path ZFS dataset on %s"%node
          print errors
        else:
          print "Brick path ZFS dataset deleted on %s"%node
          print

  except Exception, e:
    print "Encountered the following error : %s"%e
    return -1
  else:
    print "Deleting the IntegralStor Administration volume.. Done."
    print
    return 0

def mount_admin_volume(client):
  try :
    print "Mounting the IntegralStor Administration volume on the primary and secondary GRIDCells."
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
  except Exception, e:
    print "Encountered the following error : %s"%e
    return -1
  else:
    print "Mounting the IntegralStor Administration volume on the primary and secondary GRIDCells... Done."
    print
    return 0

def unmount_admin_volume(client):
  try :
    print "Unmounting the IntegralStor Administration volume on the primary and secondary GRIDCells."
    r1 = client.cmd('roles:master', 'cmd.run_all', ['umount %s'%fractalio.common.get_admin_vol_mountpoint()], expr_form='grain')
    if r1:
      for node, ret in r1.items():
        #print ret
        if ret["retcode"] != 0:
          errors = "Error unmounting the admin volume on %s"%node
          print errors
        else:
          print "Admin volume unmounted on %s"%node
          print
  except Exception, e:
    print "Encountered the following error : %s"%e
    return -1
  else:
    print "Unmounting the IntegralStor Administration volume on the primary and secondary GRIDCells... Done."
    print
    return 0

def establish_default_configuration(client):

  print "Establishing the default IntegralStor configuration .. Done"
  print

  try :

    #shutil.copytree("%s"%fractalio.common.get_defaults_dir(), "%s/defaults"%fractalio.common.get_admin_vol_mountpoint())

    print "Copying the default configuration onto the IntegralStor administration volume."
    print

    shutil.copytree("%s/db"%fractalio.common.get_defaults_dir(), "%s/db"%fractalio.common.get_admin_vol_mountpoint())
    shutil.copytree("%s/ntp"%fractalio.common.get_defaults_dir(), "%s/ntp"%fractalio.common.get_admin_vol_mountpoint())
    shutil.copytree("%s/logs"%fractalio.common.get_defaults_dir(), "%s/logs"%fractalio.common.get_admin_vol_mountpoint())

    # Delete any existing NTP file
    r2 = client.cmd('roles:master', 'cmd.run_all', ['rm /etc/ntp.conf'], expr_form='grain')
    if r2:
      for node, ret in r2.items():
        if ret["retcode"] != 0:
          errors = "Error deleting the original NTP config file on %s"%node
          print errors
          print "Exiting now.."
          return -1

    # Link the new NTP conf file on the primary onto the admin vol
    r2 = client.cmd('roles:primary', 'cmd.run_all', ['ln -s %s/ntp/primary_ntp.conf /etc/ntp.conf'%fractalio.common.get_admin_vol_mountpoint()], expr_form='grain')
    if r2:
      for node, ret in r2.items():
        if ret["retcode"] != 0:
          errors = "Error linking to the NTP config file on %s"%node
          print errors
          print "Exiting now.."
          return -1

    # Link the new NTP conf file on the secondary onto the admin vol
    r2 = client.cmd('roles:secondary', 'cmd.run_all', ['ln -s %s/ntp/secondary_ntp.conf /etc/ntp.conf'%fractalio.common.get_admin_vol_mountpoint()], expr_form='grain')
    if r2:
      for node, ret in r2.items():
        if ret["retcode"] != 0:
          errors = "Error linking to the NTP config file on %s"%node
          print errors
          print "Exiting now.."
          return -1

    # Create a home for the manifest and status files and move the previously generated files here..
    os.mkdir("%s/status"%fractalio.common.get_admin_vol_mountpoint())
    shutil.move("%s/master.manifest"%fractalio.common.get_tmp_path(), fractalio.common.get_system_status_path())
    shutil.move("%s/master.status"%fractalio.common.get_tmp_path(), fractalio.common.get_system_status_path())


    os.mkdir("%s/batch_processes"%fractalio.common.get_admin_vol_mountpoint())
    
    print "Copying the default configuration onto the IntegralStor administration volume... Done."
    print


    print "Setting up CIFS access.."
    print

    os.mkdir("%s/lock"%fractalio.common.get_admin_vol_mountpoint())
    os.mkdir("%s/samba"%fractalio.common.get_admin_vol_mountpoint())

    print "Creating CTDB config file"
    rc, errors = ctdb.create_config_file()
    if rc != 0:
      if errors:
        raise Exception(errors)
      else:
        raise Exception("Error creating the CTDB configuration file : Reason unknown")
    print "Creating CTDB config file... Done"
    print

    print "Creating CTDB nodes file"

    ip_list = []
    for node_name, node_info in si.items():
      if "interfaces" in node_info and "bond0" in node_info["interfaces"] and "inet" in node_info["interfaces"]["bond0"] and len(node_info["interfaces"]["bond0"]["inet"]) == 1:
        ip_list.append("%s\n"%node_info["interfaces"]["bond0"]["inet"][0]["address"])

    rc, errors = ctdb.add_to_nodes_file(ip_list)
    if rc != 0:
      if errors:
        raise Exception(errors)
      else:
        raise Exception("Error creating the CTDB nodes file : Reason unknown")
    print "Creating CTDB nodes file... Done"
    print

    print "Linking CTDB files"
    shutil.move('/etc/sysconfig/ctdb', '%s/lock/ctdb'%fractalio.common.get_admin_vol_mountpoint())
    r2 = client.cmd('*', 'cmd.run_all', ['rm /etc/sysconfig/ctdb'])
    r2 = client.cmd('*', 'cmd.run_all', ['ln -s %s/lock/ctdb /etc/sysconfig/ctdb'%fractalio.common.get_admin_vol_mountpoint()])
    if r2:
      for node, ret in r2.items():
        if ret["retcode"] != 0:
          errors = "Error linking to the CTDB config file on %s"%node
          print errors
          print "Exiting now.."
          return -1

    # The initial add_nodes created the initial nodes file. So move this into the admin vol and link it all          

    shutil.move('/etc/ctdb/nodes', '%s/nodes'%fractalio.common.get_admin_vol_mountpoint())
    r2 = client.cmd('*', 'cmd.run_all', ['rm /etc/ctdb/nodes'])
    r2 = client.cmd('*', 'cmd.run_all', ['ln -s %s/lock/nodes /etc/ctdb/nodes'%fractalio.common.get_admin_vol_mountpoint()])
    if r2:
      for node, ret in r2.items():
        if ret["retcode"] != 0:
          errors = "Error linking to the CTDB nodes file on %s"%node
          print errors
          print "Exiting now.."
          return -1

    print "Linking smb.conf files"
    shutil.copyfile('%s/samba/smb.conf'%fractalio.common.get_defaults_dir(),'%s/lock/smb.conf'%fractalio.common.get_admin_vol_mountpoint())
    r2 = client.cmd('*', 'cmd.run_all', ['rm /etc/samba/smb.conf'])
    r2 = client.cmd('*', 'cmd.run_all', ['ln -s %s/lock/smb.conf /etc/samba/smb.conf'%fractalio.common.get_admin_vol_mountpoint()])
    if r2:
      for node, ret in r2.items():
        if ret["retcode"] != 0:
          errors = "Error linking to the smb.conf file on %s"%node
          print errors
          print "Exiting now.."
          return -1
    print "Linking smb.conf files... Done"
    print

  except Exception, e:
    print "Encountered the following error : %s"%e
    return -1
  else:
    print "Establishing the default IntegralStor configuration .. Done"
    print
    return 0

def undo_default_configuration(client):

  print "Undoing the default IntegralStor configuration .. Done"
  print

  try :

    r2 = client.cmd('roles:master', 'cmd.run_all', ['rm /etc/ntp.conf'], expr_form='grain')
    if r2:
      for node, ret in r2.items():
        if ret["retcode"] != 0:
          errors = "Error deleting the NTP config file on %s"%node
          print errors



    print "Linking CTDB files"
    r2 = client.cmd('*', 'cmd.run_all', ['rm /etc/sysconfig/ctdb'])
    r2 = client.cmd('*', 'cmd.run_all', ['rm /etc/ctdb/nodes'])

    r2 = client.cmd('*', 'cmd.run_all', ['rm /etc/samba/smb.conf'])

  except Exception, e:
    print "Encountered the following error : %s"%e
    return -1
  else:
    print "Undoing the default IntegralStor configuration .. Done"
    print
    return 0



def start_services(client):

  try :
    print "Starting services on the active GRIDCells.."
    print

    r2 = client.cmd('roles:master', 'cmd.run_all', ['service ntpd restart'], expr_form='grain')
    if r2:
      for node, ret in r2.items():
        if ret["retcode"] != 0:
          errors = "Error restarting the NTP config file on %s"%node
          print errors
          print "Exiting now.."
          return -1

    r2 = client.cmd('*', 'cmd.run_all', ['service ctdb start'])
    if r2:
      for node, ret in r2.items():
        if ret["retcode"] != 0:
          errors = "Error starting CTDB service on %s"%node
          print errors
          print "Exiting now.."
          return -1
  except Exception, e:
    print "Encountered the following error : %s"%e
    return -1
  else:
    print "Starting services on the active GRIDCells.. Done."
    print
    return 0

def stop_services(client):
  try :
    print "Stoppong services on the active GRIDCells.."
    print

    r2 = client.cmd('roles:master', 'cmd.run_all', ['service ntpd restart'], expr_form='grain')
    if r2:
      for node, ret in r2.items():
        if ret["retcode"] != 0:
          errors = "Error stopping the NTP config file on %s"%node
          print errors

    r2 = client.cmd('*', 'cmd.run_all', ['service ctdb start'])
    if r2:
      for node, ret in r2.items():
        if ret["retcode"] != 0:
          errors = "Error stopping CTDB service on %s"%node
          print errors
  except Exception, e:
    print "Encountered the following error : %s"%e
    return -1
  else:
    print "Stopping services on the active GRIDCells.. Done."
    print
    return 0


def initiate_setup():

  added_nodes = False
  created_storage_pool = False
  created_admin_vol = False
  mounted_admin_vol = False
  created_default_config = False

  try :
    do = raw_input("Scan for new nodes?")
    if do == 'y':
      rc = scan_for_nodes()
      if rc != 0:
        remove_nodes_from_grid()
        return rc

    added_nodes = True

    print "Loading GRIDCell information"
    print
    si = system_info.load_system_config(first_time = True)
    if not si:
      print "Error loading GRIDCell information"
      remove_nodes_from_grid()
      return -1

    print "Loading GRIDCell information...Done."
    print

    rc, primary, secondary = check_for_primary_and_secondary(si)
    if rc != 0:
      remove_nodes_from_grid()
      return rc

    do = raw_input("Create storage pool?")
    if do == 'y':
      if ("secondary" in si) and ("interfaces" in si[secondary]) and ("bond0" in si[secondary]["interfaces"]) and ("inet" in si[secondary]["interfaces"]["bond0"]) and ("address" in si[secondary]["interfaces"]["bond0"]["inet"]) :
        rc, d, err = gluster_commands.add_a_node_to_pool(secondary, si[secondary]["interfaces"]["bond0"]["inet"]["address"])
        if rc != 0:
          if err:
            print "Error creating the storage pool : %s"%err
          else:
            print "Error creating the storage pool : Unknown error"
          empty_storage_pool(si, secondary)
          remove_nodes_from_grid()
          return rc

    created_storage_pool = True

    client = salt.client.LocalClient()

    do = raw_input("Create admin volume?")
    if do == 'y':
      rc = create_admin_volume(client, primary, secondary)
      if rc != 0:
        remove_admin_volume(client)
        empty_storage_pool(si, secondary)
        remove_nodes_from_grid()
        return rc

    created_admin_vol = True

    rc = mount_admin_volume(client)
    if rc != 0:
      unmount_admin_volume(client)
      remove_admin_volume(client)
      empty_storage_pool(si, secondary)
      remove_nodes_from_grid()
      return rc

    mounted_admin_vol = True

    rc = establish_default_configuration(client)
    if rc != 0:
      undo_default_configuration(client)
      unmount_admin_volume(client)
      remove_admin_volume(client)
      empty_storage_pool(si, secondary)
      remove_nodes_from_grid()
      return rc

    created_default_config = True

    rc = start_services(client)
    if rc != 0:
      stop_services(client)
      undo_default_configuration(client)
      unmount_admin_volume(client)
      remove_admin_volume(client)
      empty_storage_pool(si, secondary)
      remove_nodes_from_grid()
      return rc
    with open('/opt/fractalio/first_time_setup_completed', 'w') as f:
      f.write('%s'%strftime("%Y-%m-%d %H:%M:%S"))

  except Exception, e:
    print "Encountered the following error : %s"%e
    if client:
      stop_services(client)
    if client and created_default_config:
      undo_default_configuration(client)
    if client and mounted_admin_vol:
      unmount_admin_volume(client)
    if client and created_admin_vol:
      remove_admin_volume(client)
    if client and created_storage_pool:
      empty_storage_pool(si, secondary)
    if client and added_nodes:
      remove_nodes_from_grid()
    return -1
  else:
    return 0
        

def display_initial_screen():
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

def main():
  display_initial_screen()
  ret = initiate_setup()
  if ret == 0:
    print "Successfully configured the primary and secondary GRIDCells! You can now use IntegralView to administer the system.".center(80, ' ')

if __name__ == "__main__":
  main()


















'''
    print "Setting the IntegralStor Administration volume to mount on reboot on the primary and secondary GRIDCells."
    print
    r2 = client.cmd('roles:master', 'mount.set_fstab', [fractalio.common.get_admin_vol_mountpoint(), 'localhost:/%s'%fractalio.common.get_admin_vol_name(), 'glusterfs', 'defaults, _netdev'], expr_form='grain')
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

  #No need to mess around with DNS now. Keeping code temporarily in case things change
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

  shutil.copytree("%s/named"%fractalio.common.get_defaults_dir(), "%s/named"%fractalio.common.get_admin_vol_mountpoint())
  #os.mkdir("%s/named/master"%fractalio.common.get_admin_vol_mountpoint())
  #os.mkdir("%s/named/slave"%fractalio.common.get_admin_vol_mountpoint())
  named_uid = getpwnam('named').pw_uid
  named_gid = getpwnam('named').pw_gid
  for root, dirs, files in os.walk("%s/named"%fractalio.common.get_admin_vol_mountpoint()):  
    for d in dirs:  
      os.chown(os.path.join(root, d), named_uid, named_gid)
    for f in files:
      os.chown(os.path.join(root, f), named_uid, named_gid)
  r4 = client.cmd('roles:primary', 'cmd.run_all', ['rm /etc/named.conf'], expr_form='grain')
  if r4:
    for node, ret in r4.items():
      if ret["retcode"] != 0:
        errors += "Error deleting the DNS config file on %s"%node
  r4 = client.cmd('roles:primary', 'cmd.run_all', ['cp %s/named/master/named.conf_primary /etc/named.conf'%fractalio.common.get_admin_vol_mountpoint()], expr_form='grain')
  if r4:
    for node, ret in r4.items():
      if ret["retcode"] != 0:
        errors += "Error copying the DNS config file to the config location on %s"%node
  r4 = client.cmd('roles:secondary', 'cmd.run_all', ['rm /etc/named.conf'], expr_form='grain')
  if r4:
    for node, ret in r4.items():
      if ret["retcode"] != 0:
        errors += "Error deleting the DNS config file on %s"%node
  r4 = client.cmd('roles:secondary', 'cmd.run_all', ['cp %s/named/slave/named.conf_slave /etc/named.conf'%fractalio.common.get_admin_vol_mountpoint()], expr_form='grain')
  if r4:
    for node, ret in r4.items():
      if ret["retcode"] != 0:
        errors += "Error copying the DNS config file to the config location on %s"%node
  r4 = client.cmd('roles:master', 'cmd.run_all', ['service named start'], expr_form='grain')
  if r4:
    for node, ret in r4.items():
      if ret["retcode"] != 0:
        errors += "Error starting the DNS server from the new config location on %s"%node



    r2 = client.cmd('*', 'cmd.run_all', ['chkconfig smb off'])
    if r2:
      for node, ret in r2.items():
        if ret["retcode"] != 0:
          errors = "Error turning off smbd autostart on %s"%node
          print errors
          print "Exiting now.."
          return -1

    r2 = client.cmd('*', 'cmd.run_all', ['chkconfig ctdb on'])
    if r2:
      for node, ret in r2.items():
        if ret["retcode"] != 0:
          errors = "Error turning on CTDB autostart on %s"%node
          print errors
          print "Exiting now.."
          return -1
'''
