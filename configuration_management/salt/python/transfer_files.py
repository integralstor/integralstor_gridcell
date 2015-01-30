#!/usr/bin/python

import salt.client

"""
Python code to copy files and directories into the minion - Omkar MN
"""

local = salt.client.LocalClient()


minion = raw_input("Enter the minion ip or minion's hostname as in salt-key -L : ")

source1 = 'salt://conf_files/zfs.conf'
source2 = 'salt://conf_files/resolv.conf'
source3 = 'salt://conf_files/ramdisk'
source_fpctl = 'salt://conf_files/fpctl'
source_nodetype = 'salt://conf_files/nodetype.sh'

target1 = '/etc/modprobe.d/zfs.conf'
target2 = '/etc/resolv.conf'
target3 = '/etc/rc.local'
target4 = '/etc/init.d/ramdisk'
target_fpctl = '/opt/fractalio/bin/fpctl'
target_nodetype = '/opt/fractalio/scripts/shell/nodetype.sh'

source_dnspython = '/srv/salt/fr_software/dnspython-1.12.0'
source_setuptools = '/srv/salt/fr_software/setuptools-11.3.1'
source_uwsgi = '/srv/salt/fr_software/uwsgi-2.0.9'
source_libgfapi = 'srv/salt/fr_software/libgfapi-python'
target5 = '/opt/fractalio/installed-software'

# For fpctl and nodetype.sh
local.cmd (minion, 'cp.get_file', [source_fpctl, target_fpctl ])
local.cmd (minion, 'cmd.run', ['chmod +x /opt/fractalio/bin/fpctl'])
local.cmd (minion, 'cp.get_file', [source_nodetype, target_nodetype])
local.cmd (minion, 'cmd.run', ['echo "/bin/bash /opt/fractalio/scripts/shell/nodetype.sh" >> /etc/rc.local'])

# For dnspython
local.cmd (minion, 'cp.get_dir', [source_dnspython , target5])
local.cmd (minion, 'cmd.run', ['python /opt/fractalio/installed-software/dnspython-1.12.0/setup.py install'])

# For setuptools
local.cmd (minion, 'cp.get_dir', [source_setuptools, target5])
local.cmd (minion, 'cmd.run', ['python /opt/fractalio/installed-software/setuptools-11.3.1/setup.py install'])

# For uwsgi
local.cmd (minion, 'cp.get_dir', [source_uwsgi, target5])
local.cmd (minion, 'cmd.run', ['python /opt/fractalio/installed-software/uwsgi-2.0.9/setup.py install'])


# For libgfapi
local.cmd (minion, 'cp.get_dir', [source_libgfapi, target5])
local.cmd (minion, 'cmd.run', ['python /opt/fractalio/installed-software/libgfapi/setup.py install'])


# For zfs.conf
retval_zfs = local.cmd(minion, 'cp.get_file', [source1, target1])

# For resolv.conf
# backing up existing /etc/resolv.conf
retval_rename = local.cmd(minion, 'cmd.run', ['mv /etc/resolv.conf /etc/original_resolv_conf'])
retval_zfs = local.cmd(minion, 'cp.get_file', [source2, target2])

# Installing dnspython, setuptools and uwsgi 

# Samba directory creation
retval_samba = local.cmd(minion, 'cmd.run', ['mkdir -p /run/samba'])
retval_samba_ser = local.cmd(minion, 'cmd.run', ['/etc/init.d/smb start'])
retval_samba_chk = local.cmd(minion, 'cmd.run', ['chkconfig smb on'])

# Glusterd
retval_glusterd_ser = local.cmd(minion, 'cmd.run', ['/etc/init.d/glusterd start'])
retval_glusterd_chk = local.cmd(minion, 'cmd.run', ['chkconfig glusterd on'])

# For modprobe dev_intf ; running ipmitool after every reboot
local.cmd(minion, 'cmd.run', ['modprobe ipmi_devintf'])
local.cmd(minion, 'cmd.run', ['echo "modprobe ipmi_devintf" >> /etc/rc.local'])

# Editing of /etc/init.d/zfs file
local.cmd(minion, 'cmd.run', ['sed -i "s/\$ZFS mount -a/\$ZFS mount -O -a/" /etc/init.d/zfs'])

# Copying "ramdisk" file into /etc/init.d/
retval_ramd = local.cmd(minion, 'cp.get_file', [source3, target4])

# Changing permissions to /etc/init.d/ramdisk
retval_serv = local.cmd(minion, 'cmd.run', ['service ramdisk start'])
retval_chk = local.cmd(minion, 'cmd.run', ['chkconfig ramdisk on'])
retval_perm = local.cmd(minion, 'cmd.run', ['chmod +x /etc/init.d/ramdisk'])

# Starting the named services
retval_ser_name = local.cmd(minion, 'cmd.run', ['service named start'])
retval_named = local.cmd(minion, 'cmd.run', ['chkconfig named on'])

# To reboot
retval_named = local.cmd(minion, 'cmd.run', ['shutdown -r now'])

# To replace the 10.1.1.200 entry in /etc/salt/minion file
retval_salt = local.cmd (minion, 'cmd.run', ['sed -i \'s/master: 10.1.1.200/master: primary.fractalio.lan/\' /etc/salt/minion'])
retval_rm = local.cmd(minion, 'cmd.run', ['rm -rf /etc/salt/pki/minion/minion_master.pub'])
retval_shutdown = local.cmd(minion, 'cmd.run', ['shutdown -r now'])

