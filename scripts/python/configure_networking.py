import os, socket, re, sys
from integralstor_common import networking, command

def configure_networking():

  try :
    os.system('clear')
    change_ip = False
    change_netmask = False
    change_default_gateway = False
    change_bonding_type = False
    change_jumbo_frames = False
  
    interfaces, err = networking.get_interfaces()
    if err:
      raise Exception(err)
    if 'bond0' not in interfaces.keys():
      if_list = interfaces.keys()
      ret, err = networking.create_bond('bond0', if_list, 6)
      if err:
        raise Exception(err)
      config_changed = True

    ip_info, err = networking.get_ip_info('bond0')
    if err:
      raise Exception(err)

    '''
    if not ip_info :
      raise Exception("No bonding configured! Incorrect configuration. : %s"%err)
    '''
  
    config_changed = False
    if ip_info:
      ip = ip_info["ipaddr"]
      str_to_print = 'Enter IP address (currently "%s", press enter to retain current value) : '%ip
    else:
      ip = None
      str_to_print = "Enter IP address (currently not configured) : "

    valid_input = False
    while not valid_input :
      input = raw_input(str_to_print)
      if input:
        vi, err = networking.validate_ip(input)
        if vi:
          valid_input = True
          ip = input
          change_ip = True
          config_changed = True
      else:
        if ip:
          #IP already existed and they are now not changing it so its ok.
          valid_input = True
      if not valid_input:
        print "Invalid value. Please try again."
    print
  
    if ip_info:
      netmask = ip_info["netmask"]
      str_to_print = 'Enter netmask (currently "%s", press enter to retain current value) : '%netmask
    else:
      netmask = None
      str_to_print = "Enter netmask (currently not set) : "

    valid_input = False
    while not valid_input:
      input = raw_input(str_to_print)
      if input:
        vi, err = networking.validate_netmask(input)
        if vi:
          valid_input = True
          netmask = input
          change_netmask = True
          config_changed = True
      else:
        if netmask:
          #IP already existed and they are now not changing it so its ok.
          valid_input = True
      if not valid_input:
        print "Invalid value. Please try again."
    print
  
  
    default_gateway = None
    if ip_info and "default_gateway" in ip_info:
      default_gateway = ip_info["default_gateway"]
    else:
      default_gateway = None
    if default_gateway:
      str_to_print = 'Enter the default gateway\'s IP address (currently "%s", press enter to retain current value) : '%default_gateway
    else:
      str_to_print = "Enter the default gateway's IP address (currently not set, press enter to retain current value) : "
    valid_input = False
    while not valid_input:
      input = raw_input(str_to_print)
      if input:
        vi, err = networking.validate_ip(input)
        if vi:
          valid_input = True
          default_gateway = input
          change_default_gateway = True
          config_changed = True
      else:
        valid_input = True
      if not valid_input:
        print "Invalid value. Please try again."
    print
  
  
    hostname = socket.gethostname()
    str_to_print = 'Enter the GRIDCell hostname (currently "%s", press enter to retain current value) : '%hostname
    valid_input = False
    change_hostname = False
    while not valid_input:
      input = raw_input(str_to_print)
      if input:
        vi, err = networking.validate_hostname(input)
        if vi:
          valid_input = True
          hostname = input
          change_hostname = True
          config_changed = True
      else:
        valid_input = True
      if not valid_input:
        print "Invalid value. Please try again."
    print


    bonding_type, err = networking.get_bonding_type('bond0')
    print "Ethernet NIC bonding configuration"
    print "----------------------------------"
    print "Ethernet bonding aggregates the bandwidth of all available ethernet ports giving high throughput and failover."
    print "We support two modes. "
    print "The first is LACP (also called 802.3ad) which requires configuration on any switch). The second is balance-alb which does not require switch configuration but may not be supported on all switches. "
    valid_input = False
    while not valid_input:
      print "Valid choices for this selection  are 4 (for 802.3ad or LACP) and 6 (for balance-alb)."
      print
      if bonding_type == -1:
        str_to_print = "Enter bonding mode (currently not configured, press enter to retain current value) : "
      else:
        str_to_print = "Enter bonding mode (currently %s, press enter to retain current value) : "%bonding_type
      input = raw_input(str_to_print)
      if input:
        if input.lower() in ['4', '6']:
          valid_input = True
          bonding_type = int(input)
          change_bonding_type = True
          config_changed = True
      else:
        valid_input = True
      if not valid_input:
        print "Invalid value. Please try again."
    print
  
    
    jfe, err = networking.jumbo_frames_enabled('bond0')
    if jfe:
      jumbo_frames = 'y'
      jfe_str = "enabled"
    else:
      jumbo_frames = 'n'
      jfe_str = "disabled"
    print "Jumbo frames support"
    print "--------------------"
    print "Enabling jumbo frames improves network throughput but requires configuration on the switch side."
    print "If you enable it here, please set the MTU size on the switch to 9000"
    valid_input = False
    while not valid_input:
      str_to_print = "Enable jumbo frames (currently %s, press enter to retain current value) (y/n)? : "%jfe_str
      print
      input = raw_input(str_to_print)
      if input:
        if input.lower() in ['y', 'n']:
          valid_input = True
          jumbo_frames = input.lower()
          change_jumbo_frames = True
          config_changed = True
      else:
        valid_input = True
      if not valid_input:
        print "Invalid value. Please try again."
    print

    print "Final confirmation"
    print "------------------"
  
    print
    print "The following are the choices that you have made :"
    print "IP address : %s"%ip
    print "Net Mask : %s"%netmask
    print "Hostname : %s"%hostname
    print "Default gateway : %s"%default_gateway
    if bonding_type == 4:
      print "NIC Bonding mode : LACP"
    elif bonding_type == 6:
      print "NIC Bonding mode : balance-alb"
    else:
      print "NIC Bonding mode (unsupported!!) : %d"%bonding_type
  
    print "Enable jumbo frames : %s"%jumbo_frames
  
    if not config_changed:
      print
      print
      raw_input('No changes have been made to the configurations. Press enter to return to the main menu.')
      return 0

    str_to_print = 'Commit the above changes? (y/n) :'
      
    commit = 'n'
    valid_input = False
    while not valid_input:
      input = raw_input(str_to_print)
      if input:
        if input.lower() in ['y', 'n']:
          valid_input = True
          commit = input.lower()
      if not valid_input:
        print "Invalid value. Please try again."
    print
  
    if commit == 'y':
      print "Committing changes!"
    else:
      print "Discarding changes!"
  
    if commit != 'y':
      return 0
  
    restart_networking = False
    ip_dict = {}
    errors = []


    if change_ip or change_netmask or change_default_gateway or change_jumbo_frames:
      ip_dict["ip"] = ip
      ip_dict["netmask"] = netmask
      ip_dict["default_gateway"] = default_gateway
      if jumbo_frames == 'y':
        ip_dict["mtu"] = 9000
      else:
        ip_dict["mtu"] = 1500
      rc, err = networking.set_bond_ip_info(ip_dict)
      if not rc:
        if err:
          errors.append("Error setting IP configuration : %s"%err)
        else:
          errors.append("Error setting IP configuration ")
      restart_networking = True

    if change_hostname:
      ret, err = networking.set_hostname(hostname, 'integralstor.lan')
      if err:
        raise Exception(err)
      restart_networking = True

    if change_hostname or change_ip:
      ret, err = networking.set_hosts_file_entry(hostname, ip)
      if err:
        raise Exception(err)
  
    restart = False
    if restart_networking:
      print
      print
      valid_input = False
      while not valid_input:
        str_to_print = 'Restart network services now (y/n) :'
        print
        input = raw_input(str_to_print)
        if input:
          if input.lower() in ['y', 'n']:
            valid_input = True
            if input.lower() == 'y':
              restart = True
        if not valid_input:
          print "Invalid value. Please try again."
      print
    if restart:
      (r, rc), err = command.execute_with_rc('service network restart')
      if err:
        raise Exception(err)
      if rc == 0:
        print "Network service restarted succesfully."
      else:
        print "Error restarting network services."
        raw_input('Press enter to return to the main menu')
        return -1
  except Exception, e:
    print "Error configuring network settings : %s"%e
    return -1
  else:
    return 0

if __name__ == '__main__':

  rc = configure_networking()
  sys.exit(rc)

    
