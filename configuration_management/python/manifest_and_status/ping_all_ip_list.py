#!/usr/bin/python

import subprocess
import re

import subnet
import command

def get_list_of_pinged_ips(ip, mask, input_filename):
    all_ips_lst = subnet.get_ip_list(ip, mask)

    print "\nScanning the Network for Active IP's is under progress, please wait ....\n"
   
    # Writing into the input file under progress
    with open(input_filename, 'a') as file:
        file.write("\n")
        file.write("Scanning the Network for Active IP's is under progress, please wait ....\n")
        file.write("\n")
        file.flush()
  
    pinged_ips = []
    for ip in all_ips_lst:

        cmd = "ping -c 1 -w 1" + " " + ip
    
        # Gives all the output of the ping command in a tuple.
        ret = command.execute(cmd) 
        op_lst = list(ret)

        # This list converts the tuple into a list. 
        pinged_lst = op_lst[0].split('\n')

        # This regex extracts the received packets from the pinged_lst
        reobj1 = re.compile(",\s+[0-9]+ received.*")
        for item in pinged_lst:
            if reobj1.search(item):
                ent1 = re.search('\s[0-9]+\s[a-zA-Z]+,', item)    
                string = ent1.group()
                pattern = re.search('\s[0-9]+', string)
                numb_of_rcvd_packets = (pattern.group()).lstrip() # This is to extract the integer
                #print "Pinged ", ip, " and ", "Number of Received : ", numb_of_rcvd_packets

                if int(numb_of_rcvd_packets) > 0:                 # Bcoz, type of numb_of_rcvd_packets is a string
                    print "Discovered Active IP : ", ip 
                    with open(input_filename, 'a') as fh:
                        fh.write("Discovered Active IP : %s \n"  % ip)     
                        fh.flush()

                    pinged_ips.append(ip)

    return pinged_ips           

if __name__ == '__main__':
    get_list_of_pinged_ips('192.168.1.240', '255.255.255.0', "/tmp/demo")
