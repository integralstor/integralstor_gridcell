#!/usr/bin/python

import os
import glob
import json
import command 


def get_local_ip():

    # To get the current machine's ipaddressess "command.execute()" gives a tuple
    op = command.execute('hostname')


    # To strip the '\n' attached with the output string
    hostname = op[0].strip('\n')


    filename = "/config/master.manifest"
    try:
        with open('/config/master.manifest') as fh:
            json_op_master_manifest = json.load(fh)

    except IOError as e:
        print str(e)
        exit(-1)


    # Code to get the 'ip' field from the interface whose 'active_ip' field is TRUE

    for k, v in json_op_master_manifest.items():
        if k == hostname:
            for inner_key, inner_value in v.items():
                if inner_key == 'interface_info':
                    for i, j in inner_value.items():
                        for m,n in j.items():
                            if m == 'active_ip' and m:
                                 local_ip = j['ip']

    #print "local_ip   : ", local_ip
    return local_ip


def gen_status(ips_list = None):
    # This module combines all the /config/<ipaddress>.status files and /config/self.status files into a single /config/master.status file.

    if not ips_list:
        print "No IPs to form /config/master.status, exiting.."
    
    else:
        
        #print "IPs extracted from master.manifest : ", ips_list 
        status_file_list = glob.glob('/config/*.status')  
        #print "\nThe <ipaddress>.status file_list inside /config/ : ", status_file_list                        

        ips_list.append('self') 
 
        # Extracting the /config/master.manifest contents inorder to extract the hostname,
        # .. in case if any of the ip (nodes) fails in the interval of generating /config/master.status
        # .. from /config/master.manifest file 
        filename = "/config/master.manifest"
        try:
            with open('/config/master.manifest') as fh:
                json_op_master_manifest = json.load(fh)

        except IOError as e:
            print str(e)
            exit(-1)

        # Main dictionary to hold all the *.status files.        
        main_dict = {}

        # default_status_dict : indicates a default dictionary. 
        default_status_dict = {}
        default_status_dict['hostname'] = {}
        default_status_dict['hostname']['cpu_status'] = {}
        default_status_dict['hostname']['disk_status'] = {}
        default_status_dict['hostname']['interface_status'] = {}
        default_status_dict['hostname']['system_status'] = "down"
        
        #print "default_dict : ", default_dict
 
        #print "ips_list : ", ips_list 
  
        # To skip the local_ip
        local_ip = get_local_ip()         
        if local_ip is None:
           print "No local_ip, exiting.."
           exit(-1)

        for ip in ips_list:
            status_file_item = "/config/" + ip + ".status"        # This is string concat is to provide full path names as in the status_file list.     
            #print "s : ", status_file_item    
            if status_file_item in status_file_list:
                #print "s : ", status_file_item    
                try:                                              # This is to load the JSON file, status_file_item = "/config/192.168.1.241.status" .
                    status_dict = json.loads(open(status_file_item).read()) 
                except Exception as e:
                    print str(e)
                    exit (-1) 

                #print "status_dict : ", status_dict
                temp_list = status_dict.keys()
                main_dict[temp_list[0]]= {} 
                
                # Inserting all the keys from individual <ipaddress>.status files into the main_dict.

                if 'cpu_status' in status_dict[temp_list[0]] :
                    main_dict [temp_list[0]]['cpu_status'] = status_dict [temp_list[0]]['cpu_status'] 

                if 'disk_status' in status_dict[temp_list[0]]:
                    main_dict [temp_list[0]]['disk_status'] = status_dict [temp_list[0]]['disk_status']

                if 'interface_status' in status_dict[temp_list[0]]:
                    main_dict [temp_list[0]]['interface_status'] = status_dict [temp_list[0]]['interface_status']
                 
                if 'psu_status' in status_dict[temp_list[0]]:
                    main_dict [temp_list[0]]['psu_status'] = status_dict [temp_list[0]]['interface_status']
                
                # The below is for the 'system_status' key in main_dict. 
                # The values of cpu_status and the disk_status will be examined.
             
                if 'cpu_status' in status_dict[temp_list[0]] and 'disk_status' in status_dict[temp_list[0]] :
                        for item in status_dict[temp_list[0]]['disk_status'] : 
                            for key in status_dict[temp_list[0]]['disk_status'][item] :
                                if status_dict[temp_list[0]]['disk_status'][item][key] == 'PASSED' and status_dict[temp_list[0]]['cpu_status']['status'] == 'ok' :
                                    main_dict [temp_list[0]]['system_status'] = 'healthy'
                                else:
                                    main_dict [temp_list[0]]['system_status'] = 'degraded'    # This is for, if disk status fails and CPU status fails..
                if 'cpu_status' in status_dict[temp_list[0]] or 'disk_status' in status_dict[temp_list[0]] :
                        for item in status_dict[temp_list[0]]['disk_status'] :
                            for key in status_dict[temp_list[0]]['disk_status'][item] :
                                if status_dict[temp_list[0]]['disk_status'][item][key] == 'PASSED' :
                                    main_dict [temp_list[0]]['system_status'] = 'healthy'
                                else:
                                    main_dict [temp_list[0]]['system_status'] = 'degraded'    # This is for, if disk status fails and CPU status fails..                
                elif status_dict[temp_list[0]]['cpu_status']['status'] == 'ok' :
                                    main_dict [temp_list[0]]['system_status'] = 'healthy'
                else:
                     main_dict [temp_list[0]]['system_status'] = 'down'                       # None of the parameters (cpu_status, disk_status)are present.    
                        

            elif status_file_item == "/config/" + local_ip + ".status" :
                continue
              
            else:
                # Extracting the hostname related to the ip not found in status-file list from /config/master.manifest file.

                for hostname, value in json_op_master_manifest.items():
                    for value in json_op_master_manifest[hostname]: 
                        if value == 'interface_info':
                            for eth_info in json_op_master_manifest[hostname][value]:
                                if 'ip' in json_op_master_manifest[hostname][value][eth_info] and json_op_master_manifest[hostname][value][eth_info]['ip'] == ip: 
                                    #print hostname 
                                    main_dict[hostname] = default_status_dict['hostname']

            #print " ***** main_dict **** : ", main_dict                  
            #print json.dumps(main_dict, sort_keys=True, indent=2)

            # To create the JSON file 
            with open('/opt/fractal/temp/master.status','w') as of:
                json.dump(main_dict, of, sort_keys=True, indent=2)


if __name__ == "__main__":
    #gen_status()
    print get_local_ip()
