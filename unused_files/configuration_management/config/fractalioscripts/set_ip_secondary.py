#!/usr/bin/python

"""
This  python script changes the ip-address of a primary node to 10.1.1.4.
"""

import os
import subprocess
import re


"""
Global Variables
"""

command = "ls -1 /sys/class/net/"
cmd_args = command.split()
proc = subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

interfaces = proc.communicate()[0]
if proc.returncode == 0:
    ilist = interfaces.split('\n')
else:
    print "Cant execute the command \"%s\". Exiting !!" % command
    exit (-1)

for slave_device_name in ilist:

    if 'lo' in ilist:
        ilist.remove('lo')

    if 'bond0' in ilist:
        ilist.remove('bond0')

    if 'bonding_masters' in ilist:
        ilist.remove('bonding_masters')

    if '' in ilist:
        ilist.remove('')

#print "ilist : ", ilist

"""
Function for executing the process in a thread safe way.
Return codes:
-1 : No command given or Function execution error

Subprocess return codes:
0  : Success
1  : Command execution failure
2  : Invalid command arguments
9  : Unknown error
"""

def run_command(cmd=None):

  if cmd is None:
    print "No command is given"
    return -1

  cmd = cmd.split()
  child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  output = child.communicate()[0]
  if child.returncode == 0:
    return output.rstrip('\n')
  else:
    return -1


"""
To get all the interface details.
"""
def get_all():

  interface_dict = {}
  for interface in ilist:
    
    interface_dict[interface] = {}
    filename = '/etc/sysconfig/network-scripts/ifcfg-' + interface
    with open(filename, 'r') as fh:
      lines = fh.readlines()

    for item in lines:

      if re.search("DEVICE.*", item):
        pattern = re.search("DEVICE.*", item)
        # Getting the DEVICE
     
        for entry in pattern.group().split('='):
          if re.search(r'[a-zA-Z0-9]+', entry):
            pattern_device =  re.search(r'[a-zA-Z0-9]+', entry)
            interface_dict[interface]['device']= pattern_device.group()

      if re.search("IPADDR.*", item):
        pattern = re.search("IPADDR.*", item)

        # Getting the IPADDR 
        for entry in pattern.group().split("="):
          if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',entry):
            pattern_ipaddr = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',entry)
            interface_dict[interface]['ipaddress'] = pattern_ipaddr.group()

      if re.search("NETMASK.*", item):
        pattern = re.search("NETMASK.*", item)

        # Getting the NETMASK 
        for entry in pattern.group().split("="):
          if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',entry):
            pattern_netmask = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',entry)
            interface_dict[interface]['netmask'] = pattern_netmask.group()

      if re.search("GATEWAY.*", item):
        pattern = re.search("GATEWAY.*", item)

        # Getting the GATEWAY
        for entry in pattern.group().split("="):
          if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',entry):
            pattern_gateway = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',entry)
            interface_dict[interface]['gateway'] = pattern_gateway.group()

  #print "i_d : ", interface_dict
  return interface_dict


def write_ifcfg_ethx(device_name, ipaddr, netmask, gateway, nm_controlled='no', bootproto='none', onboot='yes', userctl='no'):

    filename = "/tmp/ifcfg-" + device_name

    try:
        with open(filename, "w") as fh:
            fh.write("#Script Generated file for NIC bonding, don't modify! \n")
            fh.write("DEVICE=%s \n" % device_name)
            fh.write("IPADDR=%s\n" % ipaddr)
            fh.write("NETMASK=%s\n" % netmask)
            fh.write("GATEWAY=%s\n" % gateway)
            fh.write("NM_CONTROLLED=%s\n" % nm_controlled)
            fh.write("BOOTPROTO=%s\n" % bootproto )
            fh.write("ONBOOT=%s\n" % onboot)
            fh.write("USERCTL=%s\n" % userctl)
    except IOError:
        print "Error : "

if __name__ == '__main__':

  ip_dict = get_all()

  if ip_dict['eth0']['device']:
    device = ip_dict['eth0']['device']

  if ip_dict['eth0']['ipaddress']:
    ip = "10.1.1.5"
  else:
    print "Cannot continue, No IPADDRESS"
    exit (-1)

  if ip_dict['eth0']['gateway']:
    gw = ip_dict['eth0']['gateway']
  else:
    print "Cannot continue, NO GATEWAY"
    exit (-2)

  if ip_dict['eth0']['netmask']:
    nm = ip_dict['eth0']['netmask']
  else:
    print "Cannot continue, NO NETMASK"
    exit (-3)

  write_ifcfg_ethx(device_name=device, ipaddr=ip, netmask=nm, gateway=gw, nm_controlled='no', bootproto='none', onboot='yes', userctl='no')

  # Backing up only the ifcfg-eth0 file
  mv_command = "mv /etc/sysconfig/network-scripts/ifcfg-eth0 /etc/sysconfig/network-scripts/dhcp_ip_ifcfg_eth0"
  return_value_mv_command = run_command(mv_command)
  if return_value_mv_command == -1:
    print "Error: Given command can't be executed or Function error. "
    exit(-1)
 
  # Moving the newly generated file 
  if not os.path.isfile("/etc/sysconfig/network-scripts/ifcfg-eth0"):
    mv_tmp_cmd = "mv /tmp/ifcfg-eth0 /etc/sysconfig/network-scripts/ifcfg-eth0"
    return_value_mv_tmp_cmd = run_command(mv_tmp_cmd)
    if return_value_mv_tmp_cmd == -1:
      print "Error: Given command can't be executed or Function error. "
      exit(-1)
  else:
    print "Some eth0 file exists.. "
    exit (3)

  # Restarting the network services
  ret_val_nw = run_command("/etc/init.d/network restart") 
  print "ret_val_nw : ", ret_val_nw
