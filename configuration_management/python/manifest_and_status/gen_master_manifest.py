#!/usr/bin/python

import os
import re
import json
import glob
import copy

import subnet

def gen_manifest(input_ip, ip_mask, temporary_master_manifest):
    """ This module aggregates all the <ip-address>.manifest - files including self.manifest - file into a single master.manifest file. """
  
    file_list = glob.glob('/config/*.manifest')
    #print "\nfile_list : ", file_list
   
    main_dict = {}
    for fname in file_list:
        if fname == "/config/master.manifest":
            continue

        dict1 = json.loads(open(fname).read())
        #print "\ndict1 : ", dict1
        temp_list = dict1.keys()
        #print "\ntemp_list : ", temp_list

        main_dict [temp_list[0]] = {}

        """To insert disk information """

        main_dict [temp_list [0]]['disk_info'] = dict1 [temp_list [0]]['disk_info']    

        """To set the active_ip parameter and to insert interface information """

        # subnet_ips_list is a LIST, containing all the IP's in the range created by input_ip.
        # input_ip is the IP-Address given by the USER, as the active IP-Adress on that Node.

        subnet_ips_list = subnet.get_ip_list(input_ip, ip_mask)
        
        # Extract the ip-address from the dict1 [temp_list [0]]['interface_info']
        # ... and to check whether the extracted IP-Adress comes in the range of input_ip ? 
        # Using \"in\" operator to check if it exists in the list ?
        # If YES then set active_ip equals TRUE otherwise FALSE
        
        temp_dict = {}
        temp_dict [temp_list [0]] = {} 
        temp_dict [temp_list [0]]['interface_info'] = copy.deepcopy(dict1 [temp_list [0]]['interface_info'])

        # An extra dictionary is freshly built to populate a new JSON Entry; active_ip = True / False. 

        extra_dict = {}
        extra_dict [temp_list[0]] = {}
        extra_dict [temp_list[0]]['interface_info'] = {}

        for k,v in temp_dict [temp_list [0]]['interface_info'].items():
            if 'ip' in temp_dict [temp_list [0]]['interface_info'][k].keys():
                if temp_dict [temp_list [0]]['interface_info'][k]['ip'] in subnet_ips_list:
                    extra_dict [temp_list[0]]['interface_info'][k] = {}
                    extra_dict [temp_list[0]]['interface_info'][k]['active_ip'] = True 

                    if 'bcast' in temp_dict [temp_list [0]]['interface_info'][k].keys():
                        extra_dict [temp_list[0]]['interface_info'][k]['bcast'] = temp_dict [temp_list [0]]['interface_info'][k]['bcast'] 

                    if 'ip' in temp_dict [temp_list [0]]['interface_info'][k].keys():
                        extra_dict [temp_list[0]]['interface_info'][k]['ip'] = temp_dict [temp_list [0]]['interface_info'][k]['ip']
   
                    if 'mask' in temp_dict [temp_list [0]]['interface_info'][k].keys():
                        extra_dict [temp_list[0]]['interface_info'][k]['mask'] = temp_dict [temp_list [0]]['interface_info'][k]['mask']                

                else:

                    extra_dict [temp_list[0]]['interface_info'][k] = {}
                    extra_dict [temp_list[0]]['interface_info'][k]['active_ip'] = False 

                    if 'bcast' in temp_dict [temp_list [0]]['interface_info'][k].keys():
                        extra_dict [temp_list[0]]['interface_info'][k]['bcast'] = temp_dict [temp_list [0]]['interface_info'][k]['bcast'] 

                    if 'ip' in temp_dict [temp_list [0]]['interface_info'][k].keys():
                        extra_dict [temp_list[0]]['interface_info'][k]['ip'] = temp_dict [temp_list [0]]['interface_info'][k]['ip']
   
                    if 'mask' in temp_dict [temp_list [0]]['interface_info'][k].keys():
                        extra_dict [temp_list[0]]['interface_info'][k]['mask'] = temp_dict [temp_list [0]]['interface_info'][k]['mask']                
            if 'ip' not in temp_dict [temp_list [0]]['interface_info'][k].keys():    
                extra_dict [temp_list[0]]['interface_info'][k] = {}
                #extra_dict [temp_list[0]]['interface_info'][k]['active_ip'] = False
                               
 
        main_dict [temp_list [0]]['interface_info'] = extra_dict [temp_list [0]]['interface_info']    

    #print "\n\n main_dict : ", main_dict

    with open(temporary_master_manifest, 'w') as of:
        json.dump(main_dict, of, sort_keys=True, indent=2)

if __name__ == '__main__' :
    gen_manifest("192.168.1.240", "255.255.255.0", "/root/master.manifest")
