#!/usr/bin/python

""" This module will extract ip-addresses from "/config/master.manifest" file and 
    call "/opt/fractal/bin/gen_master_status" to create "/config/master.status" file, 
    using the below two commands.

    Syntax to execute a command on remote machine(rcmd); providing remote machine's IP:
    ./client 192.168.1.241 rcmd /opt/fractal/bin/gen_self_status.py

    Syntax to pull the file from the remote machine; providing remote machine's IP:
    ./client 192.168.1.241 get_file /config/self.status /config/192.168.1.241.status
"""

# Exit Code
# -1 : No master.manifest exists

import os
import subprocess
import sys
import time
import glob

import ConfigParser
import json

import command
import gen_self_status
import gen_master_status
import host_info
import ip

# To list the files in the current path

dir_path = "/config/"
os.chdir(dir_path)
status_file_list = [ filename for filename in glob.glob("*[0-9].status")]
print "\nExisting files in : ", status_file_list


# To remove the existing "IPADDRESS.status" files in the status_file_list 

if status_file_list:
    for f in status_file_list:
        os.remove(f)


# To get the current machine's ipaddressess "command.execute()" gives a tuple

op = command.execute('hostname')


# To strip the '\n' attached with the output string 

hostname = op[0].strip('\n')


# To check whether master.manifest arrived and 
# to get the local active-ip from the '/config/master.manifest'

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

# To extract the list of IP's from "master.manifest".

ips_list = []
#print json_op_master_manifest
for k, v in json_op_master_manifest.items():
    for i in json_op_master_manifest[k]:
        if i == "interface_info":
            for m in json_op_master_manifest[k][i]:
                for n in json_op_master_manifest[k][i][m]:
                    if n == "ip" and  json_op_master_manifest[k][i][m]['active_ip'] == True:
                        ips_list.append(json_op_master_manifest[k][i][m][n])
        
print "\nList of IPs extracted from /config/master.manifest : ", ips_list, "\n"

# To loop over all the ip's extracted from the master.manifest file 

for ip in ips_list:
    if ip == local_ip:
        print "Local machine's ip: ", ip
        continue

    # To pull the file from the remote machine 

    pullfile_cmd = "/opt/fractal/bin/client"+ " " + ip + " " + "get_file /config/self.status"+ " " +  "/config/" + ip + ".status"
    pcmd_list = pullfile_cmd.split()

    if ip:
        try:
            pcmd_op = subprocess.Popen(pcmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            print str(e)  

        pcmd_status = pcmd_op.communicate() [0]  
        if pcmd_op.returncode != 0:
            print "The IP, ", ip, ", is not responding." 

        if pcmd_op.returncode == 0:
            print "The IP, ", ip, ", has responded."      

# To generate master.status calling gen_master_status.gen_status()

print "\nGenerating master.status  .... "
time.sleep(1)
gen_master_status.gen_status(ips_list)


# This is to move the 'master.status' file created in /opt/fractal/temp/ to /config/.

try:
    with open("/opt/fractal/temp/master.status") as fh:
        print "\nThe file /opt/fractal/temp/master.status created .."
    os.popen("mv /opt/fractal/temp/master.status /config/")
except Exception as e:
    print str(e)


# This is to check whether the 'master.status' file has been moved to /config/.

try:
    with open("/config/master.status") as fh:
        print "The file /opt/fractal/temp/master.status moved to /config/master.status ..\n"
except Exception as e:
    print str(e)

