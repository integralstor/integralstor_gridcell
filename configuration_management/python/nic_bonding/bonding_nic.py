#!/usr/bin/python

# Python script to perform NIC Bonding / NIC Teaming.

import os
import subprocess


def run_command(command = None):

    if not command:
        return None
    
    command_list = command.split()
    
    ret = ('', '')  
 
    try:
        process = subprocess.Popen(command_list, stdout = subprocess.PIPE, stderr = subprocess.PIPE )
        ret = process.communicate() 

    except Exception as e:
        ret = [ list(i) for item in ret ]
        ret = str(e)

    return ret 


def write_ifcfg_bondx(ipaddr, netmask, gateway, nm_controlled='no', bootproto='none', onboot='yes', userctl='no'):
   
    filename = "/etc/sysconfig/network-scripts/ifcfg-bond0"
    try:
        
        with open(filename, "w") as fh:
            fh.write("#Script Generated file for NIC bonding, don't modify! \n")         
            fh.write("DEVICE=bond0 \n")
            fh.write("IPADDR=%s\n" % ipaddr)
            fh.write("NETMASK=%s\n" % netmask)
            fh.write("GATEWAY=%s\n" % gateway)
            fh.write("NM_CONTROLLED=%s\n" % nm_controlled)
            fh.write("BOOTPROTO=%s\n" % bootproto )
            fh.write("ONBOOT=%s\n" % onboot)
            fh.write("USERCTL=%s\n" % userctl)
    except Exception as e:
            print str(e)
           
    
def write_ifcfg_ethx(device, bondx, nm_controlled='no', bootproto='none', onboot='yes', userctl='no'):
    
    if device is None:
       print "Cannot Continue, No device name. Exiting !!"
       exit(-1)
   
    #filename = "/etc/sysconfig/network-scripts/ifcfg-" + device
    filename = "/etc/sysconfig/network-scripts/ifcfg-" + device
    try:
        with open(filename, "w") as fh:
            fh.write("#Script Generated file for NIC bonding, don't modify! \n")         
            fh.write("DEVICE=%s\n" % device)
            fh.write("USERCTL=%s\n" % userctl)
            fh.write("ONBOOT=%s\n" % onboot)
            fh.write("NM_CONTROLLED=%s\n" % nm_controlled)
            fh.write("MASTER=%s\n" % bondx)
            fh.write("SLAVE=yes\n")
            fh.write("BOOTPROTO=%s\n" % bootproto)
    except Exception as e:
        print str(e)


def write_to_bonding_conf(bondx, mode, miimon=100, downdelay=200, updelay=200):
    try:
        with open("/etc/modprobe.d/bonding.conf", "w") as fh:
            fh.write("alias %s bonding \n" % bondx)         
            fh.write("options %s mode=%s miimon=%s downdelay=%s updelay=%s \n" % (bondx, mode, miimon, downdelay, updelay) )

    except Exception as e:
        print str(e)
        exit(-1)

def backup_ifcfg_files():

    # to get the list of all interfaces
    interfaces = os.popen('ifconfig | cut -c 1-8 | sort | uniq -u').read()
    i_list = interfaces.split()

    if 'lo' in interfaces:
        i_list.remove('lo')

    print "\nBacking up the existing /etc/sysconfig/network-scripts/ifcfg-xxxx scripts. "
    answer = raw_input("Do you want to continue (y/n) : ")

    if answer == "n" :
        print "Exiting !! "
        exit (1)

    if answer == "y" :
       for interface in i_list:
            filename = "/etc/sysconfig/network-scripts/ifcfg-" + interface
            #print "filename  : ", filename

            if os.path.isfile(filename):
                renamed_original = "/etc/sysconfig/network-scripts/origin_ifcfg-" + interface
                command = "mv" + " " + filename + " " + renamed_original
                #print "command ", command
                os.popen(command)


if __name__ == '__main__':
    

    # To display the Menu
    print "\n##### Welcome to NIC bonding CLI tool #####\n"
    print "This program is a software tool written in python, used to perform NIC bonding or NIC teaming in mode 4 (802.3ad) or in mode 6 (balance-alb) on a CentOS 6.4 machine. " 
    print "\nType any of the choices fro the below list : \n"
    print "a) Configure NIC bonding\n", "b) Quit \n"
    answer = raw_input( "Enter your choice below : ")

    if answer == 'b':
        print "Exiting ..!!"

    
    # To perform nic-bonding
    if answer == 'a':
        output = run_command('ls -1 /sys/class/net') [0]

        interface_list = output.split()
        if 'lo' in output:
            interface_list.remove('lo')

        print "\nList of available interfaces are as below : \n"

        for index, interface in enumerate(interface_list):
            print index + 1 , "\b)", interface

        input_list =  raw_input('\nFrom the above list, Please enter the interface name of your choice (seperated by a space) (if you want to quit now Press "q"): \n') 

        # Performing Input Validation
        if input_list == 'q':
            print "Pressed 'q', exiting ..!!"
            exit(0)

        for input in input_list.split():
            if input not in interface_list:
                print "\nYou have entered : %s " % input_list
                print "\nWrong Input ! Please enter your choice from above the list of available interfaces."
                exit(-1)  
 
        #print "input_list : ", input_list
        #print "input_list.splt : ", input_list.split()        

        # First things First, back up the existing ifcfg-ethx files
        # backup_existing_ethx_files()
        backup_ifcfg_files()


        # Step 1: To create /etc/sysconfig/network-scripts/ifcfg-ethX
        bondx = "bond0"
        
        for device in input_list.split():
            print "\nCreating /etc/sysconfig/network-scripts/ifcfg-"+ device +  " files .." 
            write_ifcfg_ethx(device, bondx, nm_controlled='no', bootproto='none', onboot='yes', userctl='no')

        
        # Step 2: To create /etc/sysconfig/network-scripts/ifcfg-bondx
        ipaddr = raw_input("\nEnter the ipaddress for bonding : ")
        netmask = raw_input("Enter the netmask for bonding : ")
        gateway = raw_input("Enter the gateway for bonding : ")

        nm_controlled = raw_input("Enter the nm_controlled value for bonding (Default = 'no') : ")
        bootproto = raw_input("Enter the bootproto value for bonding (Default = 'none') : ")
        onboot = raw_input("Enter the onboot value for bonding (Default = 'yes') : ")
        userctl = raw_input("Enter the userctl value for bonding (Default = 'no') : ")

        write_ifcfg_bondx(ipaddr, netmask, gateway, nm_controlled='no', bootproto='none', onboot='yes', userctl='no')
        

        # Step 3 : To create /etc/modprobe.d/bonding.conf
        print "\nCreating /etc/sysconfig/network-scripts/ifcfg-bondx files .." 
        mode = raw_input("\nEnter your mode of bonding (positive integer) : ")
        miimon = raw_input("Enter the miimon value for nic bonding (positive integer) (Default = 100) : ")
        downdelay = raw_input("Enter the downdelay value for nic bonding (positive integer)(Default =200) : ") 
        updelay = raw_input("Enter the updelay value for nic bonding (positive integer) (Default = 200) : ")  
        write_to_bonding_conf(bondx, mode, miimon=100, downdelay=200, updelay=200)   


        # Step 4 : To execute modprobe command
        command = raw_input("Enter the modprobe command for bonding : ")
        #command = "modprobe bonding" + " " + "mode="+ str(mode) + " " + "miimon=" + str(miimon) + " "  + "downdelay=" +  str(downdelay) + " " + "updelay=" + str(updelay) 
  
        try :
            print run_command(command)
                     
        except Exception as e:
            print str(e)        

        print "Restart your network services .. "  
        # Step 5 : To restart the network service
        """restart_network = "/etc/init.d/network restart"
        print "\nRestarting the network .."
      
        try :
            print run_command(restart_network)

        except Exception as e:
            print str(e)
        """ 
 
          
