#! /usr/bin/python
import salt.wheel
import sys, os, shutil, socket, struct, sys, shutil
from integralstor_gridcell import grid_ops, system_info, ctdb, gluster_trusted_pools, xml_parse
from integralstor_common import common, networking, command
import salt.client
import distutils.dir_util
from time import strftime,sleep

def get_admin_gridcells():
  admin_server_list = []
  try:
    me = socket.getfqdn()
    print "Scanning the network for GRIDCells .."
    print

    pending_minions, err = grid_ops.get_pending_minions()
    if err:
      raise Exception(err)

    if me not in pending_minions:
      raise Exception('Please configure the bootstrap admin agent on this GRIDCell to point to the local IP address before running the first time setup.')

    if not pending_minions or len(pending_minions) < 2:
      raise Exception('Please ensure that there are atleast two GRIDCells powered on and whose admin agent has been configured to point to this GRIDCell.')

    print 'The GRIDCell on which you are running the first time setup will automatically be used as one of the admin GRIDCells.'
    print 'In addition to this one, the system has detected the following GRIDCells that can be configured as admin GRIDCells: \n'
    pending_minions.remove(me)
    for index, minion in enumerate(pending_minions, start=1):
      if minion == me:
        continue
      print '%d. %s'%(index, minion)
    print

    str_to_print = 'Enter the number corresponding to one other GRIDCells from the above list that will act as admin GRIDCells : '

    valid_input = False
    while not valid_input:
      admin_server_list = []
      input = raw_input(str_to_print)
      if input:
        try:
          admin_server_index = int(input.strip())
        except Exception, e:
          print 'Please enter a valid number from the list above'
          continue
        if admin_server_index < 1 or admin_server_index > len(pending_minions):
          print 'Please enter a valid number from the list above'
          continue
        admin_server_list.append(pending_minions[admin_server_index-1])
        '''
        try:
          admin_server_index_list = [x.strip() for x in input.split(',')]
        except Exception, e:
          print "Invalid value. Please try again."
          continue
        #Check for uniqueness now
        if (len(admin_server_index_list) > len(set(admin_server_index_list))):
          print "Please enter two distinct GRIDCell numbers."
          continue
        if len(admin_server_index_list) != 2:
          print "Please enter exactly two other GRIDCell numbers."
          continue
        admin_server_list = []
        all_ok = True
        for admin_server_index_str in admin_server_index_list:
          try:
            admin_server_index = int(admin_server_index_str)
            if admin_server_index < 1 or admin_server_index > len(pending_minions):
              raise Exception('Invalid index')
          except Exception, e:
            print 'Please enter a valid number from the list above'
            all_ok = False
            break
          admin_server_list.append(pending_minions[admin_server_index-1])
        if not all_ok:
          continue
        '''
        admin_server_list.append(me)
        print "\nThe following are the choices that you have made :"
        print
        print 'Admin server(s) : %s'%','.join(admin_server_list)
        print
        print
        conf_str = 'Confirm the use of the above choices? (y/n) :'
      
        commit = 'n'
        valid_conf = False
        while not valid_conf:
          input = raw_input(conf_str)
          if input:
            if input.lower() in ['y', 'n']:
              valid_conf = True
              commit = input.lower()
          if not valid_conf:
            print "Invalid value. Please try again."
        print
  
        if commit == 'y':
          valid_input = True
  except Exception, e:
    return None, 'Error getting admin GRIDCells selection : %s'%str(e)
  else:
    return admin_server_list, None

def empty_storage_pool(admin_gridcells):
  try :
    me = socket.getfqdn()
    errors = []
    for admin_gridcell in admin_gridcells:
      if admin_gridcell != me:
        print 'Removing %s from the distributed storage pool.'%admin_gridcell
        d, err = gluster_trusted_pools.remove_a_gridcell_from_gluster_pool(admin_gridcell)
        if err:
          errors.append(err)
        else:
          print 'Removing %s from the distributed storage pool.. Done.'%admin_gridcell
    if errors:
      raise Exception(err)
  except Exception, e:
    return False, "Error clearing the distributed storage pool : %s"%e
  else:
    return True, None
    

def establish_default_configuration(client, si, admin_gridcells):
  try :

    platform_root, err = common.get_platform_root()
    if err:
      raise Exception(err)

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

    print "\nCopying the default configuration onto the IntegralStor administration volume."

    shutil.copytree("%s/db"%defaults_dir, "%s/db"%config_dir)
    shutil.copytree("%s/ntp"%defaults_dir, "%s/ntp"%config_dir)
    shutil.copytree("%s/logs"%defaults_dir, "%s/logs"%config_dir)

    # Delete any existing NTP file
    r2 = client.cmd('roles:master', 'cmd.run_all', ['rm /etc/ntp.conf'], expr_form='grain')

    # Link the new NTP conf file on the primary onto the admin vol
    ip_info, err = networking.get_ip_info('bond0')
    if err:
      raise Exception(err)
    ip_l = struct.unpack('!L',socket.inet_aton(ip_info['ipaddr']))[0]
    netmask_l = struct.unpack('!L',socket.inet_aton(ip_info['netmask']))[0]
    network_l = ip_l&netmask_l
    network = socket.inet_ntoa(struct.pack('!L',network_l))
    r2 = client.cmd('roles:master', 'integralstor.configure_ntp_master',admin_gridcells, kwarg={'network':network, 'netmask':ip_info['netmask']}, expr_form='grain')
    if r2:
      errors = ''
      for node, ret in r2.items():
        if not ret[0]:
          print r2
          errors += "Error configuring NTP on %s : %s"%(node, ret[1])
      if errors:
        raise Exception(errors)

    # Create a home for the manifest and status files and move the previously generated files here..
    os.mkdir("%s/status"%config_dir)
    shutil.move("%s/master.manifest"%tmp_path, ss_path)
    shutil.move("%s/master.status"%tmp_path, ss_path)

    
    print "Copying the default configuration onto the IntegralStor administration volume... Done."
    print


    print "Setting up CIFS access.."

    os.mkdir("%s/lock"%config_dir)
    os.mkdir("%s/samba"%config_dir)

    os.mkdir("%s/logs/task_logs"%config_dir, 0777)

    '''
    Commenting out as we wont use CTDB for this release
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

    rc, errors = ctdb.add_to_nodes_file(ip_list)
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
          print r2
          errors = "Error linking to the CTDB config file on %s"%node
          raise Exception(errors)
    print "Linking CTDB files.. Done."
    print

    # The initial add_nodes created the initial nodes file. So move this into the admin vol and link it all          

    print "Linking CTDB nodes files"
    #shutil.move('/etc/ctdb/nodes', '%s/lock/nodes'%config_dir)
    r2 = client.cmd('*', 'cmd.run_all', ['rm -f /etc/ctdb/nodes'])
    r2 = client.cmd('*', 'cmd.run_all', ['ln -s %s/lock/nodes /etc/ctdb/nodes'%config_dir])
    if r2:
      for node, ret in r2.items():
        if ret["retcode"] != 0:
          print r2
          errors = "Error linking to the CTDB nodes file on %s"%node
          raise Exception(errors)
    print "Linking CTDB nodes files. Done.."
    print
    '''

    print "Linking smb.conf files"
    shutil.copyfile('%s/samba/smb.conf'%defaults_dir,'%s/lock/smb.conf'%config_dir)
    r2 = client.cmd('*', 'cmd.run_all', ['rm -f /etc/samba/smb.conf'])
    r2 = client.cmd('*', 'cmd.run_all', ['ln -s %s/lock/smb.conf /etc/samba/smb.conf'%config_dir])
    if r2:
      for node, ret in r2.items():
        if ret["retcode"] != 0:
          print r2
          errors = "Error linking to the smb.conf file on %s"%node
          raise Exception(errors)
    print "Linking smb.conf files... Done"
    print

    print "Linking Kerberos config file"
    r2 = client.cmd('*', 'cmd.run_all', ['rm /etc/krb5.conf'])
    with open('%s/lock/krb5.conf'%config_dir, 'w') as f:
      f.close()
    r2 = client.cmd('*', 'cmd.run_all', ['ln -s %s/lock/krb5.conf /etc/krb5.conf'%config_dir])
    if r2:
      for node, ret in r2.items():
        if ret["retcode"] != 0:
          print r2
          errors = "Error linking to the krb5.conf file on %s"%node
          raise Exception(errors)
    print "Linking Kerberos config file... Done"
    print

    print "Setting appropriate boot time init files."
    r2 = client.cmd('*', 'cmd.run_all', ['rm /etc/rc.local'])
    r2 = client.cmd('*', 'cmd.run_all', ['rm /etc/rc.d/rc.local'])
    r2 = client.cmd('*', 'cmd.run_all', ['cp %s/rc_local/rc.local /etc/rc.local'%defaults_dir])
    r2 = client.cmd('*', 'cmd.run_all', ['chmod 755 /etc/rc.local'])
    if r2:
      for node, ret in r2.items():
        if ret["retcode"] != 0:
          print r2
          errors = "Error setting the appropriate rc.local file on %s"%node
          raise Exception(errors)
    print "Setting appropriate boot time init files... Done"
    print

  except Exception, e:
    return False, 'Error establishing default configuration : %s'%str(e)
  else:
    return True, None

def undo_default_configuration(client):


  try :
    platform_root, err = common.get_platform_root()
    if err:
      raise Exception(err)
    defaults_dir, err = common.get_defaults_dir()
    if err:
      raise Exception(err)

    try:
      os.remove('%s/master.status'%platform_root)
    except OSError:
      pass

    r2 = client.cmd('roles:master', 'cmd.run_all', ['rm /etc/ntp.conf'], expr_form='grain')

    print "Unlinking CTDB files"
    r2 = client.cmd('roles:master', 'cmd.run_all', ['rm /etc/sysconfig/ctdb'], expr_form='grain')
    r2 = client.cmd('roles:master', 'cmd.run_all', ['rm /etc/ctdb/nodes'], expr_form='grain')

    r2 = client.cmd('roles:master', 'cmd.run_all', ['rm /etc/samba/smb.conf'], expr_form='grain')
    r2 = client.cmd('roles:master', 'cmd.run_all', ['rm /etc/rc.local'], expr_form='grain')
    r2 = client.cmd('roles:master', 'cmd.run_all', ['cp %s/salt/master /etc/salt'%defaults_dir])
    r2 = client.cmd('roles:master', 'cmd.run_all', ['cp %s/salt/minion /etc/salt'%defaults_dir])

  except Exception, e:
    return False, 'Error undoing the default configuration : %s'%str(e)
  else:
    return True, None


def undo_setup(client, si, admin_gridcells):
  try :
    print '--------------------------------Undoing setup begin------------------------------'
    if client:
      do = raw_input("Stop services?")
      if do == 'y':
        grid_ops.start_or_stop_services(client, admin_gridcells, 'stop')

      do = raw_input("Undo cron setup?")
      if do == 'y':
        print "Undoing the cron setup.. "
        print
        rc, err = grid_ops.undo_setup_cron(client, admin_gridcells, admin_gridcells = True)
        if err:
          print err
        else:
          print "Undoing the cron setup.. Done."
          print

      do = raw_input("Undo default configuration?")
      if do == 'y':
        print "Undoing the default IntegralStor configuration .. "
        print
        rc, err = undo_default_configuration(client)
        if err:
          print err
        else:
          print "Undoing the default IntegralStor configuration .. Done"
          print

      do = raw_input("Undo default configuration?")
      if do == 'y':
        print 'Unmounting the admin volume'
        print
        ret, err = grid_ops.unmount_admin_volume(client, admin_gridcells)
        if err:
          print err
          print

      do = raw_input("Remove admin volume?")
      if do == 'y':
        print "Removing the IntegralStor Administration volume.."
        print
        ret, err = grid_ops.remove_admin_volume(client)
        if err:
          print "Error removing the IntegralStor Administration volume.. : %s"%err
        print "Deleting the IntegralStor Administration volume.. Done."
        print

      do = raw_input("Undo the distributed storage pool?")
      if do == 'y':
        print "Removing the distributed storage pool..."
        print
        rc, err = empty_storage_pool(admin_gridcells)
        if err:
          print err
        else:
          print "Removing the distributed storage pool... Done."
          print

      do = raw_input("Forget existing admin GRIDCells?")
      if do == 'y':
        print "Removing GRIDCells from grid.."
        print
        ret, err = grid_ops.delete_all_salt_keys()
        if err:
          print err
        else:
          print "Removing GRIDCells from grid.. Done."
          print

      '''
      do = raw_input("Restart minions?")
      if do == 'y':
        print 'Restarting minions'
        print
        ret, err = grid_ops.restart_minions(client, admin_gridcells)
        if err:
          print err
          print
      '''
      do = raw_input("Restart salt master?")
      if do == 'y':
        command.get_command_output('service salt-master restart')
  except Exception, e:
    print "Error rolling back the setup : %s"%e
    print '--------------------------------Undoing setup end------------------------------'
    return -1
  else:
    print '--------------------------------Undoing setup end------------------------------'
    return 0


def initiate_setup():

  client = None
  si = None
  admin_gridcells = []

  try :
    client = salt.client.LocalClient()
    me = socket.getfqdn()

    do = raw_input("Scan for and accept admin GRIDCells?")
    if do == 'y':
      #Get the hostnames of the three gridcells to be flagged as admin gridcells
      admin_gridcells, err = get_admin_gridcells()
      if err:
        raise Exception(err)

      #Accept their keys, get their bond0 IP, add them to the hosts file(DNS), sync modules, regenrate manifest and status, update the minions to point to the admin gridcells, flag them as admin gridcells by setting the appropriate grains and restart the minions.
      (success, failed), err = grid_ops.add_gridcells_to_grid(None, admin_gridcells, admin_gridcells, first_time = True, print_progress = True, admin_gridcells = True, restart_salt_minions = False, establish_cron = False)
      #print success, failed, err
      if err:
        raise Exception(err)
      if (not success) :
        raise Exception('Error adding GRIDCells to grid : Unknown error')
      else:
        print 'Successfully added the following GRIDCells to the grid : %s'%','.join(success)

      if failed:
        raise Exception('Error adding %s to the grid. Error : '%(','.join(failed), err))

    print "Loading GRIDCell information"

    si, err = system_info.load_system_config(first_time = True)
    if not si:
      raise Exception("Error loading GRIDCell information : %s"%err)

    print "Loading GRIDCell information...Done."
    print

    #Create the gluster trusted storage pool
    do = raw_input("Create the distributed storage pool?")
    if do == 'y':
      print 'Creating the distributed storage pool.'
      for admin_gridcell in admin_gridcells:  
        if admin_gridcell != me:
          d, err = gluster_trusted_pools.add_a_gridcell_to_gluster_pool(admin_gridcell)
          if err:
            raise Exception(err)
      print 'Creating the distributed storage pool.. Done.'
      print

    #Create and start the admin volume
    do = raw_input("Create the admin volume?")
    if do == 'y':
      rc, err = grid_ops.create_admin_volume(client, admin_gridcells)
      if not rc:
        if err:
          raise Exception(err)
        else:
          raise Exception('Error creating admin volume : unknown error')



    do = raw_input("Mount the admin volume?")
    if do == 'y':
      sleep(10)
      print "Mounting the IntegralStor Administration volume.."
      rc, err  = grid_ops.mount_admin_volume(client, admin_gridcells)
      if not rc :
        e = None
        if err:
          e =  "Error mounting admin vol : %s"%err
        else:
          e =  "Error mounting admin vol"
        raise Exception(e)
      print "Mounting the IntegralStor Administration volume.. Done."
      print

    do = raw_input("Create the default configuration?")
    if do == 'y':
      sleep(10)
      #Create all the required directories and link them to the appropriate places and setup CTDB and NTP as well.
      print
      print "Establishing the default IntegralStor configuration .."
      rc, err = establish_default_configuration(client, si, admin_gridcells)
      if not rc:
        if err:
          raise Exception(err)
        else:
          raise Exception('Unknown error')
      print "Establishing the default IntegralStor configuration .. Done"
      print

    do = raw_input("Start services?")
    if do == 'y':
      sleep(10)
      #Start CTDB, samba and winbind on the nodes..
      print "Starting services.."
      rc,err = grid_ops.start_or_stop_services(client, admin_gridcells, 'start')
      if not rc:
        e = None
        if err:
          e =  "Error starting services on the GRIDCells : %s"%err
        else:
          e =  "Error starting services on the GRIDCells"
        raise Exception(e)
      print "Starting services.. Done."
      print

      rc = client.cmd('*','cmd.run_all',['service uwsgi start'])    
      if rc:
        for node, ret in rc.items():
          if ret["retcode"] != 0:
            errors = "Error restarting uwsgi service on %s"%node
            print errors

    do = raw_input("Setup cron on the admin GRIDCells?")
    if do == 'y':
      print
      print "Establishing the cron on the admin GRIDCells.."
      rc, err = grid_ops.setup_cron(client, admin_gridcells, admin_gridcells = True)
      if not rc:
        if err:
          raise Exception(err)
        else:
          raise Exception('Unknown error')
      print "Establishing the cron on the admin GRIDCells.. Done."
      print

    do = raw_input("Setup high availability for the admin service?")
    if do == 'y':
      print "\nSetting up high availability for the admin service.."
      print
 

      #Create the pki directory in the admin dir so all admin gridcells can point to it..
      os.makedirs('/opt/integralstor/integralstor_gridcell/config/salt/pki')
      distutils.dir_util.copy_tree('/etc/salt/pki/master', '/opt/integralstor/integralstor_gridcell/config/salt/pki/master')

      others = []
      for admin_gridcell in admin_gridcells:
        if admin_gridcell != me:
          others.append(admin_gridcell)
  
      print 'Sharing the admin master keys'
      rc = client.cmd(others,'cmd.run_all',['yes | cp -rf /opt/integralstor/integralstor_gridcell/config/salt/pki/master /etc/salt/pki/master'], expr_form='list')
      if rc:
        for node, ret in rc.items():
          if ret["retcode"] != 0:
            errors = "Error restoring master config on %s from admin vol "%node
            print errors
      print 'Sharing the admin master keys.. Done.'
      print
  
      print 'Configuring the admin service to use the admin vol.'
      rc = client.cmd('*','cmd.run_all',['yes | cp /opt/integralstor/integralstor_gridcell/defaults/salt/master /etc/salt/master'])
      if rc:
        for node, ret in rc.items():
          if ret["retcode"] != 0:
            errors = "Error copying the master config on %s"%node
            print errors
      print 'Configuring the admin service to use the admin vol.. Done.'
      print
      
      print 'Restarting the admin master service'
      #rc = client.cmd('*','cmd.run_all',['service salt-master restart'])
      rc = client.cmd(others,'cmd.run_all',['service salt-master restart'], expr_form='list')
      if rc:
        for node, ret in rc.items():
          if ret["retcode"] != 0:
            errors = "Error restarting salt-master on %s"%node
            print errors
      print 'Restarting the admin master service.. Done.'
      print

      sleep(10)
      print 'Scheduling restarting of the admin slave service'
      #rc = client.cmd('*','cmd.run_all',['service salt-minion restart'])    
      rc = client.cmd('*','cmd.run_all',['echo service salt-minion restart | at now + 1 minute'])
      if rc:
        for node, ret in rc.items():
          if ret["retcode"] != 0:
            errors = "Error restarting salt-minion service on %s"%node
            print errors
      print 'Restarting the admin slave service.. Done.'
      print

      print "Setting up high availability for the admin service.. Done."
      print


    platform_root, err = common.get_platform_root()
    if err:
      raise Exception(err)


    with open('%s/first_time_setup_completed'%platform_root, 'w') as f:
      f.write('%s'%strftime("%Y-%m-%d %H:%M:%S"))

    do = raw_input("Restart salt master?")
    if do == 'y':
      command.get_command_output('service salt-master restart')

  except Exception, e:
    print '----------------ERROR----------------------'
    print 'Error setting up the GRIDCell system : %s.\n\n We will now undo the setup that has been done do far'%str(e)
    print '----------------ERROR----------------------'
    print
    undo_setup(client, si, admin_gridcells)
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
  print "Please ensure that you have selected three (3) GRIDCells to be your administration GRIDCells, that they are connected to the network, the ZFS pool has been created and the network configuration done on all of them.".center(80, ' ')
  print
  print
  print
  inp = raw_input ("Press <Enter> if you are ready to proceed or 'q <Enter>' to quit : ")
  if not inp:
    return True
  else:
    return False
  print 

def main():
  ret = display_initial_screen()
  if not ret:
    print 'Exiting initial setup..'
    sys.exit(0)
  ret, err = initiate_setup()
  if not err:
    print 'Successfully configured the administration GRIDCells!'
    print
    print 'You may now use IntegralView by typing "http://<ip_address_of_admin_gridcell>/" to configure the rest of the system.'.center(80, ' ')
  print
  print

if __name__ == "__main__":
  main()


