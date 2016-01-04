#! /usr/bin/python
import salt.wheel
import sys, os, shutil
from integralstor_gridcell import grid_ops, gluster_commands, system_info, ctdb
from integralstor_common import common
import salt.client
from pwd import getpwnam
import shutil
from time import strftime

def scan_for_nodes():
  try :
    tmp_pending_nodes, err = grid_ops.get_pending_minions()
    if err:
      raise Exception(err)
    if not tmp_pending_nodes:
      raise Exception("No GRIDCells found")
    if 'gridcell-pri.integralstor.lan' not in tmp_pending_nodes:
      raise Exception("A primary GRIDCell was not detected. Please verify that one of the GRIDCells has been configured to be a primary.")
    if 'gridcell-sec.integralstor.lan' not in tmp_pending_nodes:
      raise Exception( "A secondary GRIDCell was not detected. Please verify that one of the GRIDCells has been configured to be a secondary.")
    pending_nodes = ['gridcell-pri.integralstor.lan', 'gridcell-sec.integralstor.lan']
    print "Found the primary and secondary GRIDCells."
    print
    (success, failed), err = grid_ops.add_nodes_to_grid("System setup process",pending_nodes, first_time = True, print_progress = True)
    if err:
      raise Exception(err)
    if (not success) :
      if err:
        raise Exception(err)
      else:
        raise Exception('Error adding GRIDCells to grid : Unknown error')
  except Exception, e:
    return False, 'Error scanning for nodes : %s'%str(e)
  else:
    return True, None


def remove_nodes_from_grid():
  try :
    minions, err = grid_ops.get_accepted_minions()
    if err:
      raise Exception("Error retrieving accepted minion list")
    if minions:
      for minion in minions:
        print "Disconnecting GRIDCell %s"%minion
        rc, err = grid_ops.delete_salt_key(minion)
        if not rc:
          if err:
            raise Exception(err)
          else:
            raise Exception ("Error deleting salt key : Unknown error occurred")
  except Exception, e:
    return False, 'Error removing GRIDCells from grid : %s'%str(e)
  else:
    return True, None

def check_for_primary_and_secondary(si):
  try :
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
      raise Exception("Could not detect a primary GRIDCell!")
    if not secondary:
      raise Exception("Could not detect a secondary GRIDCell!")
      return (-1, primary, secondary)
  except Exception, e:
    return None,  "Error checking for primary and secondary GRIDCells : %s"%e
  else:
    return (primary, secondary), None


def empty_storage_pool(si, secondary):
  try :
    d, err = gluster_commands.remove_node_from_pool(si, secondary)
    if err:
      raise Exception(err)
  except Exception, e:
    return False, "Error emptying the storage pool : %s"%e
  else:
    return True, None
    

def create_admin_volume(client, primary, secondary):

  try :
    admin_vol_name, err = common.get_admin_vol_name()
    if err:
      raise Exception(err)
    devel_files_path, err = common.get_devel_files_path()
    if err:
      raise Exception(err)

    print "Creating the bricks for the admin volume"
    r1 = client.cmd('roles:master', 'cmd.run_all', ['zfs create frzpool/normal/%s'%(admin_vol_name)], expr_form='grain')
    if r1:
      for node, ret in r1.items():
        #print ret
        if ret["retcode"] != 0:
          raise Exception("Error creating the brick path ZFS dataset on %s"%node)
        else:
          print "Brick path ZFS dataset created on %s"%node
          print

    print "Creating the IntegralStor Administration Volume."
    print

    cmd = "gluster --mode=script volume create %s repl 2 %s:/frzpool/normal/%s %s:/frzpool/normal/%s force --xml"%(admin_vol_name, primary,  admin_vol_name, secondary, admin_vol_name)
    #print cmd
    d, err = gluster_commands.run_gluster_command(cmd, "%s/create_volume.xml"%devel_files_path, "Admin volume creation")
    if err:
      raise Exception(err)
    if d and ("op_status" in d) and d["op_status"]["op_ret"] == 0:
      print "Creating the IntegralStor Administration Volume... Done."
      print
    else:
      err = ""
      if "op_status" in d and "op_errstr" in d["op_status"]:
        err = d["op_status"]["op_errstr"]
      if "op_errno" in d["op_status"]:
        err += ". Error number %d"%d["op_status"]["op_errno"]
      raise Exception("Error creating the admin volume : %s"%err)

    print "Setting trusted pool quorum."
    cmd = "gluster volume set all cluster.server-quorum-ratio 51% --xml"
    d, err = gluster_commands.run_gluster_command(cmd, "%s/create_volume.xml"%devel_files_path, "Admin volume creation")
    if err:
      raise Exception(err)
    if d and ("op_status" in d) and d["op_status"]["op_ret"] == 0:
      print "Setting trusted pool quorum... Done."
      print
    else:
      err = ""
      if "op_status" in d and "op_errstr" in d["op_status"]:
        err = d["op_status"]["op_errstr"]
      if "op_errno" in d["op_status"]:
        err += ". Error number %d"%d["op_status"]["op_errno"]
      raise Exception("Error setting trusted pool quorum : %s"%err)

    print "Starting the IntegralStor Administration Volume."
    d, err = gluster_commands.run_gluster_command('gluster volume start %s --xml'%admin_vol_name, '', 'Starting admin vol')
    if err:
      raise Exception(err)
    if d and ("op_status" in d) and d["op_status"]["op_ret"] == 0:
      print "Starting the IntegralStor Administration Volume... Done."
      print
    else:
      err = ""
      if "op_status" in d and "op_errstr" in d["op_status"]:
        err = d["op_status"]["op_errstr"]
      if "op_errno" in d["op_status"]:
        err += ". Error number %d"%d["op_status"]["op_errno"]
      raise Exception("Error starting the admin volume : %s"%err)
    
  except Exception, e:
    return False, 'Error creating the admin volume : %s'%str(e)
  else:
    return True, None


def remove_admin_volume(client):
  try :
    admin_vol_name, err = common.get_admin_vol_name()
    if err:
      raise Exception(err)
    devel_files_path, err = common.get_devel_files_path()
    if err:
      raise Exception(err)


    print "Stopping the IntegralStor Administration Volume."
    d, err = gluster_commands.run_gluster_command('gluster --mode=script volume stop %s force --xml'%admin_vol_name, '', 'Stopping admin vol')
    if err:
      raise Exception(err)
    if d and ("op_status" in d) and d["op_status"]["op_ret"] == 0:
      print "Stopping the IntegralStor Administration Volume... Done."
      print
    else:
      err = ""
      if "op_status" in d and "op_errstr" in d["op_status"]:
        err = d["op_status"]["op_errstr"]
      if "op_errno" in d["op_status"]:
        err += ". Error number %d"%d["op_status"]["op_errno"]
      raise Exception("Error stopping the admin volume : %s"%err)

    cmd = "gluster --mode=script volume delete %s --xml"%admin_vol_name
    #print cmd
    d, err = gluster_commands.run_gluster_command(cmd, "%s/delete_volume.xml"%devel_files_path, "Admin volume deletion")
    if err:
      raise Exception(err)
    if d and ("op_status" in d) and d["op_status"]["op_ret"] == 0:
      print "Deleting the IntegralStor Administration Volume... Done."
      print
    else:
      err = ""
      if "op_status" in d and "op_errstr" in d["op_status"]:
        err = d["op_status"]["op_errstr"]
      if "op_errno" in d["op_status"]:
        err += ". Error number %d"%d["op_status"]["op_errno"]
      raise Exception("Error deleting the admin volume : %s"%err)

    print "Deleting the bricks for the admin volume"
    r1 = client.cmd('roles:master', 'cmd.run_all', ['zfs destroy frzpool/normal/%s'%(admin_vol_name)], expr_form='grain')
    if r1:
      for node, ret in r1.items():
        #print ret
        if ret["retcode"] != 0:
          errors = "Error deleting the brick path ZFS dataset on %s"%node
          raise Exception(errors)
        else:
          print "Brick path ZFS dataset deleted on %s"%node
          print

  except Exception, e:
    return False, 'Error removing the admin volume : %s'%str(e)
  else:
    return True, None


def establish_default_configuration(client, si):


  try :

    defaults_dir, err = common.get_defaults_dir()
    if err:
      raise Exception(err)
    config_dir, err = common.get_config_dir()
    if err:
      raise Exception(err)
    ss_path, err = common.get_system_status_path()
    if err:
      raise Exception(err)
    tmp_path, err = common.get_tmp_path()
    if err:
      raise Exception(err)

    print "Copying the default configuration onto the IntegralStor administration volume."
    print

    shutil.copytree("%s/db"%defaults_dir, "%s/db"%config_dir)
    shutil.copytree("%s/ntp"%defaults_dir, "%s/ntp"%config_dir)
    shutil.copytree("%s/logs"%defaults_dir, "%s/logs"%config_dir)

    # Delete any existing NTP file
    r2 = client.cmd('roles:master', 'cmd.run_all', ['rm /etc/ntp.conf'], expr_form='grain')

    # Link the new NTP conf file on the primary onto the admin vol
    r2 = client.cmd('roles:primary', 'cmd.run_all', ['ln -s %s/ntp/primary_ntp.conf /etc/ntp.conf'%config_dir], expr_form='grain')
    if r2:
      for node, ret in r2.items():
        if ret["retcode"] != 0:
          errors = "Error linking to the NTP config file on %s"%node
          raise Exception(errors)

    # Link the new NTP conf file on the secondary onto the admin vol
    r2 = client.cmd('roles:secondary', 'cmd.run_all', ['ln -s %s/ntp/secondary_ntp.conf /etc/ntp.conf'%config_dir], expr_form='grain')
    if r2:
      for node, ret in r2.items():
        if ret["retcode"] != 0:
          errors = "Error linking to the NTP config file on %s"%node
          raise Exception(errors)

    # Create a home for the manifest and status files and move the previously generated files here..
    os.mkdir("%s/status"%config_dir)
    shutil.move("%s/master.manifest"%tmp_path, ss_path)
    shutil.move("%s/master.status"%tmp_path, ss_path)


    os.mkdir("%s/batch_processes"%config_dir)
    
    print "Copying the default configuration onto the IntegralStor administration volume... Done."
    print


    print "Setting up CIFS access.."
    print

    os.mkdir("%s/lock"%config_dir)
    os.mkdir("%s/samba"%config_dir)

    print "Creating CTDB config file"
    rc, errors = ctdb.create_config_file()
    if not rc:
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
        ip_list.append("%s"%node_info["interfaces"]["bond0"]["inet"][0]["address"])

    rc, errors = ctdb.add_to_nodes_file(client, ip_list)
    if not rc:
      if errors:
        raise Exception(errors)
      else:
        raise Exception("Error creating the CTDB nodes file : Reason unknown")
    print "Creating CTDB nodes file... Done"
    print

    print "Linking CTDB files"
    shutil.move('/etc/sysconfig/ctdb', '%s/lock/ctdb'%config_dir)
    r2 = client.cmd('*', 'cmd.run_all', ['rm /etc/sysconfig/ctdb'])
    r2 = client.cmd('*', 'cmd.run_all', ['ln -s %s/lock/ctdb /etc/sysconfig/ctdb'%config_dir])
    if r2:
      for node, ret in r2.items():
        if ret["retcode"] != 0:
          errors = "Error linking to the CTDB config file on %s"%node
          raise Exception(errors)

    # The initial add_nodes created the initial nodes file. So move this into the admin vol and link it all          

    print "Linking CTDB nodes files"
    shutil.move('/etc/ctdb/nodes', '%s/lock/nodes'%config_dir)
    r2 = client.cmd('*', 'cmd.run_all', ['rm -f /etc/ctdb/nodes'])
    r2 = client.cmd('*', 'cmd.run_all', ['ln -s %s/lock/nodes /etc/ctdb/nodes'%config_dir])
    if r2:
      for node, ret in r2.items():
        if ret["retcode"] != 0:
          errors = "Error linking to the CTDB nodes file on %s"%node
          raise Exception(errors)
    print "Linking CTDB nodes files. Done.."

    print "Linking smb.conf files"
    shutil.copyfile('%s/samba/smb.conf'%defaults_dir,'%s/lock/smb.conf'%config_dir)
    r2 = client.cmd('*', 'cmd.run_all', ['rm -f /etc/samba/smb.conf'])
    r2 = client.cmd('*', 'cmd.run_all', ['ln -s %s/lock/smb.conf /etc/samba/smb.conf'%config_dir])
    if r2:
      for node, ret in r2.items():
        if ret["retcode"] != 0:
          errors = "Error linking to the smb.conf file on %s"%node
          raise Exception(errors)
    print "Linking smb.conf files... Done"
    print

    print "Linking krb5.conf file"
    r2 = client.cmd('*', 'cmd.run_all', ['rm /etc/krb5.conf'])
    with open('%s/krb5.conf'%config_dir, 'w') as f:
      f.close()
    r2 = client.cmd('*', 'cmd.run_all', ['rm /etc/krb5.conf'])
    r2 = client.cmd('*', 'cmd.run_all', ['ln -s %s/lock/krb5.conf /etc/krb5.conf'%config_dir])
    if r2:
      for node, ret in r2.items():
        if ret["retcode"] != 0:
          errors = "Error linking to the krb5.conf file on %s"%node
          raise Exception(errors)
    print "Linking krb5.conf file... Done"
    print

    print "Setting appropriate rc.local files."
    r2 = client.cmd('*', 'cmd.run_all', ['rm /etc/rc.local'])
    r2 = client.cmd('*', 'cmd.run_all', ['rm /etc/rc.d/rc.local'])
    r2 = client.cmd('*', 'cmd.run_all', ['cp %s/rc_local/primary_and_secondary/rc.local /etc/rc.local'%defaults_dir])
    r2 = client.cmd('*', 'cmd.run_all', ['chmod 755 /etc/rc.local'])
    if r2:
      for node, ret in r2.items():
        if ret["retcode"] != 0:
          errors = "Error setting the appropriate rc.local file on %s"%node
          raise Exception(errors)
    r2 = client.cmd('*', 'cmd.run_all', ['cp %s/rc_local/primary_and_secondary/rc.local /etc/rc.d/rc.local'%defaults_dir])
    if r2:
      for node, ret in r2.items():
        if ret["retcode"] != 0:
          errors = "Error setting the appropriate rc.d/rc.local file on %s"%node
          raise Exception(errors)
    print "Setting appropriate rc.local files... Done"
    print

  except Exception, e:
    return False, 'Error establishing default configuration : %s'%str(e)
  else:
    return True, None

def undo_default_configuration(client):


  try :
    defaults_dir, err = common.get_defaults_dir()
    if err:
      raise Exception(err)

    r2 = client.cmd('roles:master', 'cmd.run_all', ['rm /etc/ntp.conf'], expr_form='grain')

    print "Unlinking CTDB files"
    r2 = client.cmd('*', 'cmd.run_all', ['rm /etc/sysconfig/ctdb'])
    r2 = client.cmd('*', 'cmd.run_all', ['rm /etc/ctdb/nodes'])

    r2 = client.cmd('*', 'cmd.run_all', ['rm /etc/samba/smb.conf'])
    r2 = client.cmd('*', 'cmd.run_all', ['rm /etc/rc.local'])
    r2 = client.cmd('*', 'cmd.run_all', ['cp %s/rc_local/normal/rc.local.not_in_cluster /etc/rc.local'%defaults_dir])

  except Exception, e:
    return False, 'Error undoing the default configuration : %s'%str(e)
  else:
    return True, None




def undo_setup(client, si, primary, secondary):
  try :
    print '--------------------------------Undoing setup begin------------------------------'
    if client:
      grid_ops.start_or_stop_services(client, [primary, secondary], 'stop')
      print "Undoing the default IntegralStor configuration .. "
      print
      rc, err = undo_default_configuration(client)
      if err:
        print err
      else:
        print "Undoing the default IntegralStor configuration .. Done"
        print
      print 'Unmounting the admin volume'
      print
      ret, err = grid_ops.unmount_admin_volume(client, [primary, secondary])
      if err:
        print err
        print

      print "Removing the IntegralStor Administration volume.."
      print
      ret, err = remove_admin_volume(client)
      if err:
        print "Error removing the IntegralStor Administration volume.. : %s"%err
      print "Deleting the IntegralStor Administration volume.. Done."
      print
      if si and secondary:
        print "Removing the initial storage pool with the primary and secondary GRIDCells..."
        print
        rc, err = empty_storage_pool(si, secondary)
        if err:
          print err
        else:
          print "Removing the initial storage pool with the primary and secondary GRIDCells... Done."
          print
      print 'Restarting minions'
      print
      ret, err = grid_ops.restart_minions(client, [primary, secondary])
      if err:
        print err
        print
      print "Removing GRIDCells from grid.."
      print
      ret, err = remove_nodes_from_grid()
      if err:
        print err
      else:
        print "Removing GRIDCells from grid.. Done."
        print
  except Exception, e:
    print "Error rolling back the setup : "%e
    print '--------------------------------Undoing setup end------------------------------'
    return -1
  else:
    print '--------------------------------Undoing setup end------------------------------'
    return 0

def initiate_setup():

  added_nodes = False
  created_storage_pool = False
  created_admin_vol = False
  mounted_admin_vol = False
  created_default_config = False
  client = None
  si = None
  primary = None
  secondary = None

  try :
    client = salt.client.LocalClient()
    do = raw_input("Scan for new nodes?")
    if do == 'y':
      print "Scanning the network for GRIDCells .."
      print
      rc, err = scan_for_nodes()
      if not rc :
        if err:
          e =  err
        else:
          e = 'Error scanning for GRIDCells'
        raise Exception(e)
      print "Scanning the network for GRIDCells.. Done."
      print

    print "Loading GRIDCell information"
    print

    si, err = system_info.load_system_config(first_time = True)
    if not si:
      raise Exception("Error loading GRIDCell information : %s"%err)

    print "Loading GRIDCell information...Done."
    print

    print "Checking for primary and secondary GRIDCell presence."
    print
    tup, err = check_for_primary_and_secondary(si)
    if tup:
      primary = tup[0]
      secondary = tup[1]
    if err:
      raise Exception(err)
    print "Checking for primary and secondary GRIDCell presence.. Done."
    print

    do = raw_input("Create storage pool?")
    if do == 'y':
      d, err = gluster_commands.add_a_node_to_pool(secondary)
      if not d:
        e = None
        if err:
          e =  "Error creating the storage pool : %s"%err
        else:
          e = "Error creating the storage pool : Unknown error"
        raise Exception(e)

    try :
      ipl = []
      ip = si[primary]["interfaces"]["bond0"]["inet"][0]["address"]
      if ip:
        ipl.append(ip)
      ip = si[secondary]["interfaces"]["bond0"]["inet"][0]["address"]
      if ip:
        ipl.append(ip)
    except Exception, e:
      raise Exception("Error retrieving IPs of primary and/or secondary GRIDCell(s)")

    rc, err = ctdb.add_to_nodes_file(client, ipl)
    if not rc :
      if err:
        raise Exception("Error adding IPs of the GRIDCell(s) to the CTDB nodes file : %s"%err)
      else:
        raise Exception("Error adding IPs of the GRIDCell(s) to the CTDB nodes file")


    do = raw_input("Create admin volume?")
    if do == 'y':
      print "Creating the IntegralStor Administration volume.."
      print
      rc, err = create_admin_volume(client, primary, secondary)
      if not rc:
        if err:
          raise Exception(err)
        else:
          raise Exception('Error creating admin volume : unknown error')
      print "Creating the IntegralStor Administration volume.. Done."
      print

    created_admin_vol = True

    print "Mounting the IntegralStor Administration volume.."
    print
    rc, err  = grid_ops.mount_admin_volume(client, [primary, secondary])
    if not rc :
      e = None
      if err:
        e =  "Error mounting admin vol : %s"%err
      else:
        e =  "Error mounting admin vol"
      raise Exception(e)
    print "Mounting the IntegralStor Administration volume.. Done."
    print

    print "Establishing the default IntegralStor configuration .."
    print
    rc, err = establish_default_configuration(client, si)
    if not rc:
      if err:
        raise Exception(err)
      else:
        raise Exception('Unknown error')
    print "Establishing the default IntegralStor configuration .. Done"
    print

    print "Starting services.."
    print
    rc,err = grid_ops.start_or_stop_services(client, [primary, secondary], 'start')
    if not rc:
      e = None
      if err:
        e =  "Error starting services on the GRIDCells : %s"%err
      else:
        e =  "Error starting services on the GRIDCells"
      raise Exception(e)
    print "Starting services.. Done."
    platform_root, err = common.get_platform_root()
    if err:
      raise Exception(err)
    with open('%s/first_time_setup_completed'%platform_root, 'w') as f:
      f.write('%s'%strftime("%Y-%m-%d %H:%M:%S"))

  except Exception, e:
    print '----------------ERROR----------------------'
    print 'Error setting up the GRIDCell system : %s.\n\n We will now undo the setup that has been done do far'%str(e)
    print '----------------ERROR----------------------'
    print
    undo_setup(client, si, primary, secondary)
    return False, 'Error setting up the GRIDCell system : %s'%str(e)
  else:
    return True, None
        

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
  print 

def main():
  display_initial_screen()
  ret, err = initiate_setup()
  if not err:
    print "Successfully configured the primary and secondary GRIDCells! You can now use IntegralView to administer the system.".center(80, ' ')
  print
  print

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

def mount_admin_volume(client):
  try :
    config_dir, err = common.get_config_dir()
    if err:
      raise Exception(err)
    admin_vol_name, err = common.get_admin_vol_name()
    if err:
      raise Exception(err)
    print "Mounting the IntegralStor Administration volume on the primary and secondary GRIDCells."
    r1 = client.cmd('roles:master', 'cmd.run_all', ['mount -t glusterfs localhost:/%s %s'%(admin_vol_name, config_dir)], expr_form='grain')
    if r1:
      for node, ret in r1.items():
        #print ret
        if ret["retcode"] != 0:
          print ret['retcode']
          errors = "Error mounting the admin volume on %s"%node
          raise Exception(errors)
          print errors
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
    config_dir, err = common.get_config_dir()
    if err:
      raise Exception(err)
    print "Unmounting the IntegralStor Administration volume on the primary and secondary GRIDCells."
    r1 = client.cmd('roles:master', 'cmd.run_all', ['umount %s'%config_dir()], expr_form='grain')
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
def restart_minions():
  try:
    client = salt.client.LocalClient()
    r1 = client.cmd('roles:master', 'cmd.run', ['echo service salt-minion restart | at now + 1 minute'], expr_form='grain')
  except Exception, e:
    return -1
  else:
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
          raw_input('press a key')
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
    print "Stopping services on the active GRIDCells.."
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
'''
'''
def create_storage_pool():
  try :
    print "Creating an initial storage pool with the primary and secondary GRIDCells..."
    print
    d, err = gluster_commands.run_gluster_command('gluster peer probe %s --xml'%secondary, '', 'Adding nodes to cluster')
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
