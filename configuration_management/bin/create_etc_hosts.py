#!/usr/bin/python

# Exit Codes
# -1 : The file /config/master_manifest doesn't exist.


import os
import json
import re


def gen_etc_hosts_file(master_manifest_file, etc_hosts_file):

    # To check whether '/config/master.manifest' exists ?
    try:
        master_manifest_output = json.load(open(master_manifest_file))
    
    except IOError as e:
        print str(e)
        exit(-1)   
    
    # List comphrension to get the hostnames of all nodes
    hostname_list = [ hostname for hostname in master_manifest_output ]
    
    
    # To get only the active ip-addresses
    ipaddresses_list = []
    for key, value in master_manifest_output.items():
        for m, n in value.items():
            if m == 'interface_info':
                for i, j in n.items():
                    for p, r in j.items():
                        if j['active_ip']:
                            if p == 'ip':
                                #print p, ": ", j['ip']
                                ipaddresses_list.append(j['ip'])

    # In order to create /etc/hosts file, combining the two lists into a dictionary.
    hostname_ip_dict = dict(zip(hostname_list, ipaddresses_list))
    
    
    with open(etc_hosts_file, "w") as fh:
        fh.write("127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4\n")
        fh.write("::1         localhost localhost.localdomain localhost6 localhost6.localdomain6\n")
        fh.write("\n \n")
        for hostname, ipaddress in hostname_ip_dict.items():
            hostname_no_domain_name_list = hostname.split('.')
            fh.write("%s \t%s \t%s\n" % (ipaddress, hostname, hostname_no_domain_name_list[0]))

    try:
        with open(etc_hosts_file) as fh:
            print "File \" %s \" has been created." % etc_hosts_file
            pass
    except IOError as e:
        print "Unable to open the file : ",etc_hosts_file  


if __name__ == '__main__':
    
    import optparse

    # Using Opt-Parser for catching command line arguments
    parser = optparse.OptionParser()

    parser.add_option('-C', help = 'multiple arguments: Master_Manifest_Filename_Full_Path <space> Etc_Hosts_Filename_Full_Path', dest='multi', action='store', nargs=2)

    (opts, args) = parser.parse_args()

    if opts.multi != None:
        gen_etc_hosts_file(opts.multi[0], opts.multi[1])    
