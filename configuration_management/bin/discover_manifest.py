#!/usr/bin/python

""" This is a CLI tool to generate /config/master.manifest file. 

    Syntax to execute a command on remote machine(rcmd); providing remote machine's IP:
    ./client 192.168.1.241 rcmd /opt/fractal/bin/gen_self_manifest.py

    Syntax to pull the file from the remote machine; providing remote machine's IP:
    ./client 192.168.1.241 get_file /config/self.manifest /config/192.168.1.241.manifest
"""

import os
import subprocess
import sys
import time
import glob
import re

import ConfigParser
import json

import gen_self_manifest
import gen_master_manifest
import host_info
import ip
import subnet
import command
import get_host_mask_info
import ping_all_ip_list
import validate_file_accessibility


def discover(input_ip, ip_mask, input_filename, temporary_master_manifest, retry_count, sleep_value):
    """ This function with the specified parameters loops over all the IP's over the subnet (derived from subnet.py module) and builds the "master.manifest" file and returns a dictionary. """


    # To list the files in the current path
    dir_path = "/config/"
    os.chdir(dir_path)
    status_file_list = [ filename for filename in glob.glob("*[0-9].manifest")]

  
    # To remove the existing files in the status_file_list
    if status_file_list:
        for f in status_file_list:
            os.remove(f)

    
    # To create /config/self.manifest in the local machine
    gen_self_manifest.gen_manifest()


    # Global dict for successfully responded IP-Addresses
    ip_dict = {} 
    ip_responded_with_manifest = []


    # To get a list of successfully pinged IPs
    pinged_ip_list =  ping_all_ip_list.get_list_of_pinged_ips(input_ip, ip_mask, input_filename)
    
    print "\nDiscovering Fractal Nodes from the set of Active IP's, please wait .... \n"


    # Printing the status to the input_filename
    with open(input_filename, 'a') as FILE:
        FILE.write("\nDiscovering Fractal Nodes from the set of Active IPs, please wait ....\n")
        FILE.flush()
    

    # To loop-over all the ip's in the subnet
    i = 0
    while (i < int(retry_count)):
        for ip in pinged_ip_list:

            # For local-ip : i.e IP of the local machine 
            if ip == input_ip:
                print "Discovered Fractal Node with IP : ", ip

                # Writing to the input_file
                with open(input_filename, 'a') as FILE:
                    FILE.write("\nDiscovered Fractal Node with IP : %s \n" % ip)
                    FILE.flush()

                # Assuming that the local machine is a part of Node discovery process        
                ip_responded_with_manifest.append(ip)
                continue
    
            # To execute a command on remote machine using ./client command
            remote_rcmd = "/opt/fractal/bin/client" + " " + ip + " " + "rcmd /opt/fractal/bin/gen_self_manifest.py"
            return_rcmd = command.execute(remote_rcmd)

            #print "ip = %s, return_rcmd: %s" % (ip, return_rcmd)
            
            # Joining all the values of Tuples, in order to write into a filename 
            joined_return_rcmd = ' '.join( str(i) for i in return_rcmd )        
  
            # To get the file from successfully pinged IP using ./client command
            # Here, return_rcmd is a tuple
            for item in return_rcmd:
                if item.strip('\n') == 'Success':
                    getfile_cmd = "/opt/fractal/bin/client"+ " " + ip + " " + "get_file /config/self.manifest"+ " " +  "/config/" + ip + ".manifest"
                    return_getfile = command.execute(getfile_cmd)
                    #print "return_getfile : ", return_getfile
                    for item in return_getfile:
                        pattern = re.search(".*\sbytes of data.*", item)
                        if pattern:  
                            print "Discovered Fractal Node with IP : ", ip

                            with open(input_filename, 'a') as FILE:
                                FILE.write("Discovered Fractal Node with IP : %s \n" % ip)
                                FILE.flush()
                         
                            ip_responded_with_manifest.append(ip) 

         
        time.sleep(int(sleep_value))
        print "\nLoop ", i, " over"
        print "\nRetrying for ", sleep_value, "seconds more.."
        print "\n****************************** "
        print "****************************** "
        i = i + 1
 
    print "\nGenerating master.manifest .... \n"
    

    # Calling "gen_master_manifest.py" to generate "master.manifest"
    time.sleep(1)
    gen_master_manifest.gen_manifest(input_ip, ip_mask, temporary_master_manifest)


    # To confirm "temporary_master_manifest" - file name given by the admin or user for "master.manifest" ..
    # .. has been generated or not ? 
    try: 
        with open(temporary_master_manifest, 'r') as fh:
            print "master.manifest file has been generated as : ", temporary_master_manifest

            # For the '==done==' in the input_file, indicating the polling process ends here.
            with open(input_filename, 'a') as FILE:
                FILE.write("\nmaster.manifest file has successfully been generated as : %s \n" % temporary_master_manifest) 
                FILE.write("\n==done==\n") 
                FILE.flush()
    except Exception as e:
        print str(e)
        return -1     


    # This "return_dict" - dictionary gives information about total_ips polled, successfully responded ip's and 
    # .. generated temporary master.manifest filename.     
    return_dict = {}
    return_dict['Total_ips'] = len(pinged_ip_list)
    return_dict['Successfully_responded_ips'] = ip_responded_with_manifest
    return_dict['Generated_file_name'] = temporary_master_manifest

    return return_dict

  
def main():
    """ First comes the command line options else skip to Interactive - GUI """

    import optparse
    import valid_ip
    import validate_file_accessibility


    # First comes the command line options else skip to Interactive - GUI 
    # Using Opt-Parser for catching command line arguments
    parser = optparse.OptionParser()

    parser.add_option('-M', help = 'multiple arguments: IP-Address <space> Subnet-Mask <space> Polling_Results_Filename <space> Temporary_Master_Manifest <space> Retry_Count <space> Sleep_Value', dest='multi', action='store', nargs=6)

    (opts, args) = parser.parse_args()
   

    # IP-Address and Mask parameter's validation for Command Line parameters usage.
    if opts.multi != None:
        bool_value_ip = valid_ip.is_valid_ip(opts.multi[0])    

        if not bool_value_ip:
            print "\n***Not a Valid IP-Address format *** :", opts.multi[0], "\nPlease enter a valid IP-Address."

        bool_value_mask = valid_ip.is_valid_ip(opts.multi[1])

        if not bool_value_mask:
            print "\n***Not a Valid  Subnet-mask format *** :", opts.multi[1], "\nPlease enter a valid Subnet-mask."

        # To validate the  "Polling_Results_Filename" and "Temporary_master_manifest filenames"
        ret_val_multi2 = validate_file_accessibility.file_validation(opts.multi[2])             

        if ret_val_multi2 is None:
            pass

        if ret_val_multi2 == -1:
            return -1

        ret_val_multi3 = validate_file_accessibility.file_validation(opts.multi[3])             

        if ret_val_multi3 is None:
            pass

        if ret_val_multi3 == -1:
            return -1
    
        
    # Calling discover(.....) to poll and generate /config/master.manifest file
    if opts.multi != None:
        discover(opts.multi[0], opts.multi[1], opts.multi[2], opts.multi[3], opts.multi[4], opts.multi[5])


    # If no arguments are given then start Commandline UI
    if len(sys.argv) == 1:
        print "\n*** Starting Interactive CLI... ***\n"
        
        # To get and display the list of IP's in the local machine
        ips_list = host_info.get_ip_info()

        # List of local machine's IP-Addresses
        local_ips = []

        try:
            for i in ips_list:
                intermediate_list=[]
                intermediate_list.append(i['ip'])
                intermediate_list.append(i['mask'])
                local_ips.append(intermediate_list)
        except KeyError as e:
            print str(e)

        for item in local_ips:
            print local_ips.index(item), "\b)", item

        choice_ip = int(raw_input("\nIP-Adressess are found as above, \nPress the Slno. of your matching IP-Address ans Mask THEN Press Enter: "))

        # List Comphrension to validate invalid choice entered by the user
        list_of_indexes = [ local_ips.index(ix) for ix in local_ips ]

        if isinstance(choice_ip, str):
            print "Please enter a valid serial number from the above list !!"
            return -1

        if int(choice_ip) not in list_of_indexes:
            print "Please enter a valid serial number from the above list !!"
            return -1

        ip_addr_selected = ''
        for ip_addr in local_ips:
            if int(choice_ip) == local_ips.index(ip_addr):
                print "\nYour selected choice is : ", local_ips.index(ip_addr)
                print "\nRelated IP and Mask of your selected choice is : ", ip_addr
                ip_addr_selected = ip_addr
    
        input_ip = ip_addr_selected [0]
        ip_mask = ip_addr_selected [1]
        
        input_filename = raw_input("\nEnter a Filename (Full Path) to write polling results : ")
        
        # Validating the "input_filename"
        ret_val_input_filename = validate_file_accessibility.file_validation(input_filename)
        if ret_val_input_filename == -1:
            return -1
    
        retry_count = raw_input("\nEnter retry_count value (i.e Number of times all the IPs int the subnet will be polled. Min = 1) : ")
        sleep_value = raw_input("\nEnter the sleep_value (i.e Polling Time Interval b/w each iteration untill retry_count exceeds) : ")
          
        temporary_master_manifest = raw_input("\nEnter a Filename (Full Path) to Temporary_Master_Manifest : ")

        # Validating the "temporary_master_manifest"
        ret_val_temporary_master_manifest = validate_file_accessibility.file_validation(temporary_master_manifest )
        if ret_val_temporary_master_manifest == -1:
            return -1

        # Calling discover(.....) to poll and generate /config/master.manifest file
        discover(input_ip, ip_mask, input_filename, temporary_master_manifest, retry_count, sleep_value)


if __name__ == "__main__":
    main()
    
