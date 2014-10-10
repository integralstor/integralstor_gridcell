#!/usr/bin/python

""" Be careful !! 
    This script will set the hostname of the node to the last 4 digits of the MAC address prefixed by a "fractal- " , immediately. 
"""

import os
import subprocess

import host_info

def command_execution(command = None):
    """This function executes a command and returns the output in the form of a tuple. 
       Exits in the case of an exception. 
    """
    args = command.split()

    output = (' ', ' ')
   
    if command is None:
        return None

    try:
        op = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)

    except Exception as e:
        print str(e)
        exit(-1)

    output =  op.communicate()

    return output


def set_MAC_addr_as_hostname():
    """ This function sets the hostname of the node to "fractal-XXXX", 
        where 'XXXX' will be combination of (without colon) last two fields mac-address of the NIC on that node. 
    """ 

    list_of_dictionaries = host_info.get_ip_info()
    
    list_MAC_addr = []

    for dictionary in list_of_dictionaries:
        for key, value in dictionary.items():
            if key == 'mac_addr':
                list_MAC_addr.append(value)

    for mac_addr in list_MAC_addr:
         if mac_addr == '00:00:00:00:00:00' :
             continue
         else:
             # mac_addr[12:] --> gives last two fields of MAC, 
             # mac_addr[12:].split(':') --> splits into a list without the colon character ':'
             # ''.join(mac_addr[12:].split(':')) --> joins the above list items

             part_of_hostname = ''.join(mac_addr[12:].split(':')) 
            
             # Change the part_of_hostname into lowercase letters
             lowercase_part_of_hostname = part_of_hostname.lower()
 
             # Steps to change the hostname
             # Writing into the '/etc/sysconfig/network' file
 
             hostname_full = 'fractal-' + lowercase_part_of_hostname + '.fractal.lan'

             command1="hostname" + " " + hostname_full
             #print "Cmd 1 executing ... : ", command1

             command_execution(command1)

             command2 = 'mv /etc/sysconfig/network /etc/sysconfig/network_original'
             #print "Cmd 2 executing ...:  ", command2

             command_execution(command2)  
               
             with open('/etc/sysconfig/network', 'w') as fh:
                 fh.write("# Script generated file\n")
                 fh.write("NETWORKING=\"yes\"\n")
                 fh.write("HOSTNAME=\"%s\"\n" % hostname_full) 
        
                 
             command3 = '/etc/init.d/network restart'
             #print "Cmd 3 executing ... ", command3
              
             print "Setting the new hostname as : ", hostname_full
             print "Restarting the Network Services ... " 
             print "Executing the command : ", command3
             print "Please wait ..."
           
             command_execution(command3)              

             break             

if __name__ == "__main__":
    set_MAC_addr_as_hostname()

