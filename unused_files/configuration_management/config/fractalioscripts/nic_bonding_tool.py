#!/usr/bin/python

"""
This is a python based command line tool used to perform nic bonding or nic teaming.
This is works only with "-C" option.
"""

import os
import re
import subprocess
import optparse


""" 
Global variable declarations.
"""

command="ls -1 /sys/class/net/"
cmd_args=command.split()
proc =  subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

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


def get_all():

  interface_dict = {}
  for interface in ilist:

    filename = '/etc/sysconfig/network-scripts/ifcfg-' + interface
    with open(filename, 'r') as fh:
      lines = fh.readlines()   

    for item in lines:
      if re.search("IPADDR.*", item):
        pattern = re.search("IPADDR.*", item)

        # Getting the IPADDR 
        for entry in pattern.group().split("="):
          if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',entry):
            pattern_ipaddr = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',entry)
            interface_dict['ipaddress'] = pattern_ipaddr.group()
            
      if re.search("NETMASK.*", item):
        pattern = re.search("NETMASK.*", item)        

        # Getting the NETMASK 
        for entry in pattern.group().split("="):
          if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',entry):
            pattern_netmask = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',entry)
            interface_dict['netmask'] = pattern_netmask.group()

      if re.search("GATEWAY.*", item):
        pattern = re.search("GATEWAY.*", item)        

        # Getting the GATEWAY
        for entry in pattern.group().split("="):
          if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',entry):
            pattern_gateway = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',entry)
            interface_dict['gateway'] = pattern_gateway.group()

  return interface_dict


def backup_ifcfg_files():

    print "\nBacking up the existing /etc/sysconfig/network-scripts/ifcfg-xxxx scripts. "
    for interface in ilist:
         filename = "/etc/sysconfig/network-scripts/ifcfg-" + interface
         #filename = "/tmp/ifcfg-" + interface

         if os.path.isfile(filename):
             renamed_original = "/etc/sysconfig/network-scripts/original_ifcfg-" + interface
             #renamed_original = "/tmp/original_ifcfg-" + interface
             command = "mv" + " " + filename + " " + renamed_original

             return_value_mv_command = run_command(command)
             if return_value_mv_command == -1:
                 print "Error: Given command can't be executed or Function error. "
                 exit(-1)
         else:
             print "File %s doesn't exists." % filename


def write_ifcfg_bondx(bonded_device_name, ipaddr, netmask, gateway, nm_controlled='no', bootproto='none', onboot='yes', userctl='no'):

    #filename = "/tmp/ifcfg-" + bonded_device_name
    filename = "/etc/sysconfig/network-scripts/ifcfg-" + bonded_device_name

    try:

        with open(filename, "w") as fh:
            fh.write("#Script Generated file for NIC bonding, don't modify! \n")
            fh.write("DEVICE=%s \n" % bonded_device_name)
            fh.write("IPADDR=%s\n" % ipaddr)
            fh.write("NETMASK=%s\n" % netmask)
            fh.write("GATEWAY=%s\n" % gateway)
            fh.write("NM_CONTROLLED=%s\n" % nm_controlled)
            fh.write("BOOTPROTO=%s\n" % bootproto )
            fh.write("ONBOOT=%s\n" % onboot)
            fh.write("USERCTL=%s\n" % userctl)
    except IOError:
        print "Error : "

def write_ifcfg_ethx(bonded_device_name, slave_device_name, nm_controlled='no', bootproto='none', onboot='yes', userctl='no'):

    #filename = "/tmp/ifcfg-" + slave_device_name
    filename = "/etc/sysconfig/network-scripts/ifcfg-" + slave_device_name
    try:
        with open(filename, "w") as fh:
            fh.write("#Script Generated file for NIC bonding, don't modify! \n")
            fh.write("DEVICE=%s\n" % slave_device_name)
            fh.write("USERCTL=%s\n" % userctl)
            fh.write("ONBOOT=%s\n" % onboot)
            fh.write("NM_CONTROLLED=%s\n" % nm_controlled)
            fh.write("MASTER=%s\n" % bonded_device_name)
            fh.write("SLAVE=yes\n")
            fh.write("BOOTPROTO=%s\n" % bootproto)
    except IOError:
        print "Error : "


def write_to_bonding_conf(bondx, mode, miimon=100, downdelay=200, updelay=200):
    try:
        #with open("/tmp/bonding.conf", "w") as fh:
        with open("/etc/modprobe.d/bonding.conf", "w") as fh:
            fh.write("alias %s bonding \n" % bondx)
            fh.write("options %s mode=%s miimon=%s downdelay=%s updelay=%s \n" % (bondx, mode, miimon, downdelay, updelay) )

    except IOError:
        print "Error: Unable to open the file"
        exit(-1)

    # Doing a modprobe : modprobe bonding mode=active-backup(4) miimon=100 downdelay=200 updelay=200
    modprobe_command = "modprobe bonding mode=%s miimon=%s downdelay=%s updelay=%s" % (mode, miimon, downdelay, updelay)
    return_value_modprobe_command = run_command(modprobe_command)
    if return_value_modprobe_command == -1:
        print "Error: Given command can't be executed or Function error. "
        exit(-1)
 
"""
The module optparse is deprecated and aptparse is recommended.
But the module aptparse is not a available in python 2.6.6. 
So I have used optparse module.
"""

if __name__ == '__main__':
 
    parser = optparse.OptionParser()
    parser.add_option('-C', help='Multiple arguments : <mode> <miimon> <downdelay> <updelay>', dest='multi', action='store', nargs=4)

    (opts, args) = parser.parse_args()    
  
    ipdict = get_all()  

    if opts.multi is None:
      print "Provide suitable options, type <program> --help for more information."    
      exit(-1) 
     
    # Backup all the files
    print "Backing up the files .. "
    backup_ifcfg_files() 

    # Writing for /etc/sysconfig/network-scripts/ifcfg-bond0  
    write_ifcfg_bondx("bond0", ipdict["ipaddress"], ipdict["netmask"] , ipdict["gateway"])

    for slave_device_name in ilist:
        write_ifcfg_ethx("bond0", slave_device_name, nm_controlled='no', bootproto='none', onboot='yes', userctl='no')

    # Writing to /etc/modprobe.d/bonding.conf
    write_to_bonding_conf("bond0", mode=opts.multi[0], miimon=opts.multi[1], downdelay=opts.multi[2], updelay=opts.multi[3])   

    # To restarting the network service
    print "Restarting the network services .. \n"
    command = "/etc/init.d/network restart"
    proc = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
