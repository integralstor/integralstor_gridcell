#!/bin/sh
echo '''
	#################################################
	#						#
	#						#
	#    ///***GRIDCELL VALIDATION SCRIPT***\\\	#
	#						#
	#						#
	#################################################
'''
echo "######################	Partition Scheme Validation 		######################"
df -h /boot -t ext4 >> /tmp/tmp_part_info || echo "Partitioning '/boot --fstype ext4' is NOT done"
df -h /home -t ext4 >> /tmp/tmp_part_info || echo "Partitioning '/home --fstype ext4' is NOT done"
df -h /opt -t ext4 >> /tmp/tmp_part_info || echo "Partitioning '/opt --fstype ext4' is NOT done"
df -h / -t ext4 >> /tmp/tmp_part_info || echo "Partitioning '/ --fstype ext4' is NOT done"
swapon -s >> /tmp/tmp_part_info || echo "No swap Created"
df -h /frzpool -t zfs >> /tmp/tmp_part_info || echo "Partitioning '/frzpool --fstype zfs' is NOT done"
df -h /frzpool/normal -t zfs >> /tmp/tmp_part_info || echo "Partitioning '/frzpool/normal --fstype zfs' is NOT done"
df -h /frzpool/deduplicated -t zfs >> /tmp/tmp_part_info || echo "Partitioning '/frzpool/deduplicated --fstype zfs' is NOT done"
df -h /frzpool/compressed -t zfs >> /tmp/tmp_part_info || echo "Partitioning '/frzpool/compressed --fstype zfs' is NOT done"

echo "######################	End of Partition Scheme			######################"

echo "######################	PACKAGES VALIDATION PART 		######################"

PACKAGE_LIST="core salt-master salt-minion tuned wget smartmontools glusterfs glusterfs-fuse glusterfs-server glusterfs-api glusterfs-api-devel ctdb samba-client samba samba-winbind samba-winbind-clients ipmitool OpenIPMI kernel-devel zfs krb5-workstation bind ypbind ypserv ntp uwsgi nginx kexec-tools kexec-tools fractalio_django python-devel samba-vfs-glusterfs"

for pkg in $PACKAGE_LIST; do
    if ! rpm -qa | grep $pkg ; then
        echo "$pkg : Not Installed"
    fi
done
echo "######################	END OF PACKAGE VALIDATION PART 		######################"

echo "######################	Default Username and Group 		######################"
grep integralstor /etc/passwd >>/tmp/tmp_users_info || echo "No user Called 'Integralstor'"
grep integralstor /etc/group >>/tmp/tmp_users_info || echo "No Group Called 'Integralstor'"
grep integralstor /etc/sudoers >>/tmp/tmp_users_info || echo "No Sudoer Called 'Integralstor'"
echo "######################	End of Username and Group 		######################"
echo "######################	Active Interfaces			######################"
ip addr show dev lo >> /tmp/tmp_net || echo "'lo' interface does not exist"
ip addr show dev eth0 >> /tmp/tmp_net || echo "'eth0' interface does not exist"
ip addr show dev eth1 >> /tmp/tmp_net || echo "'eth0' interface does not exist"
ip addr show dev eth2 >> /tmp/tmp_net || echo "'eth1' interface does not exist"
ip addr show dev eth3 >> /tmp/tmp_net || echo "'eth2' interface does not exist"
ACTIVE_IP=`ifconfig | awk -vRS= -vFS="\n" '{ if ( $0 ~ /inet\ addr:/ ) { print }}' | sed 's/[ \t].*//;/^\(lo\|\)$/d'`
grep $ACTIVE_IP /etc/sysconfig/network-scripts/ifcfg-* >>/tmp/tmp_net || echo "No Active Interfaces"
GATEWAY_IP=`netstat -nr | awk '{ if ($4 ~/UG/) print; }' | awk -v CUR_IF=$IF '$NF==CUR_IF {print $2};'`
if [ ! -z "$GATEWAY_IP" ] ; then
    echo "No Gateway IP"
fi
echo "######################	End of Active Interfaces		######################"
echo "######################	Hostname				######################"
STRING=$(ifconfig | grep eth0 | head -1 | awk '{print $5}' | awk -F ':' '{print tolower($5 $6)}')
hnpart="gridcell-"$STRING
name="$hnpart.integralstor.lan"
grep $name /etc/sysconfig/network >>/tmp/tmp_host_name || echo "Error setting Hostname to gridcell.integralstor.lan or having Diff. Hostname"
echo "######################	End of Hostname				######################"
echo "######################	Hosts					######################"
ip=$(ifconfig | awk -F':' '/inet addr/&&!/127.0.0.1/{split($2,_," ");print _[1]}')
STRING=$(ifconfig | grep eth0 | head -1 | awk '{print $5}' | awk -F ':' '{print tolower($5 $6)}')
hnpart="gridcell-"$STRING
name="$hnpart.integralstor.lan"
grep $ip /etc/hosts >>/tmp/tmp_hosts || echo "No Host's IP is Set"
grep $name /etc/hosts >>/tmp/tmp_hosts || echo "No Host's NAME is Set"
grep $hnpart /etc/hosts >>/tmp/tmp_hosts || echo "No Host's HNPART is Set"
echo "######################	Hosts End				######################"
echo "######################	SSHD Status 				######################"
chkconfig --list sshd >> /tmp/tmp_ssh || echo "No SSH service"
grep integralstor /etc/ssh/sshd_config >> /tmp/tmp_allowd_ssh_user || echo "User 'Integralstor' is Not Allowed SSH user"
echo "######################	End of SSHD status			######################"
echo "######################	End of CentOS-Base repo status		######################"
grep enabled=0 /etc/yum.repos.d/CentOS-Base.repo >> /tmp/tmp_Base_repo || echo "'CentOS-Base.repo' Repositories Not Disabled"
echo "######################	End of CentOS-Base repo status		######################"
echo "######################	Directory and File Creation check	######################"

DIR_LIST="/opt/integralstor /opt/integralstor/integralstor_gridcell/tmp /run/samba /var/log/integralstor/integralstor_gridcell /opt/integralstor/integralstor_gridcell/config /srv/salt/_modules /opt/integralstor/integralstor_gridcell /opt/integralstor/integralstor_utils /usr/lib/python2.6/site-packages/integralstor_utils /usr/lib/python2.6/site-packages/integralstor_gridcell /etc/nginx/sites-enabled /etc/uwsgi/vassals"
for path in $DIR_LIST; do
    if [[ ! -d "$path" ]]; then
	echo "'$path' Directory Does Not Exist"
    fi
done

FILE_LIST="/opt/integralstor/ramdisks.conf /opt/integralstor/platform /var/log/integralstor/integralstor_gridcell/integral_view.log /opt/integralstor/integralstor_utils.tar.gz /opt/integralstor/integralstor_gridcell.tar.gz /etc/resolv.conf /etc/init/start-ttys.conf /etc/init/integralstor_gridcell_menu.conf /etc/nginx/sites-enabled/integral_view_nginx.conf /etc/uwsgi/vassals/integral_view_uwsgi.ini /etc/init.d/ramdisk /etc/modprobe.d/zfs.conf"

for path in $FILE_LIST; do
    if [[ ! -e "$path" ]]; then
        echo "'$path' File Does Not Exist"
    fi
done

echo "######################	End of Directory and File Creation Chk	######################"


echo "######################	ISCSI					######################"
echo "######################	End of ISCSI				######################"

echo "######################	Zip files				######################"
cat /usr/lib/python2.6/site-packages/sos/plugins/iscsi.py >>/tmp/tmp_iscsi || echo "No iscsi installed"
cat /usr/lib/python2.6/site-packages/dnspython-1.12.0-py2.6.egg-info >>/tmp/tmp_dnspython || echo "No dnspython installed"
cat /usr/bin/iostat >> /tmp/tmp_systat || /usr/bin/sadf >> /tmp/tmp_systat || echo "No Systat Installed"
cat /usr/lib64/libgfapi.so >>/tmp/tmp_libgfapipython || echo "No libgfapipython installed"
cat /usr/lib/python2.6/site-packages/setuptools-11.3.1-py2.6.egg >> /tmp/tmp_setuptool || echo "No Setuptools Installed"
grep uwsgi /usr/sbin/uwsgi >> /tmp/tmp_uwsgi || echo "No UWSGI Installed"
cat /usr/lib64/python2.6/site-packages/netifaces-0.10.4-py2.6-linux-x86_64.egg >> /tmp/tmp_netifaces || echo "No Netifaces Installed"
cat /usr/bin/crontab >> /tmp/tmp_crontab || echo "No Crontab Installed"
echo "######################	End of Zip files			######################"

echo "######################	Salt					######################"
cat /etc/salt/minion | grep gridcell-pri.integralstor.lan  || echo "The salt minion is not having its master server name"
cat /etc/salt/grains | grep gridcell || echo "The roles not set to gridcell"
cat /etc/salt/grains | grep normal || echo "The roles not set to normal"
cat /etc/salt/master | grep file_recv: || echo "The file_recv not set to True"

cat /etc/salt/master | grep file_roots: >>/tmp/tmp_srv-salt || echo "The roles not set to /srv/salt"
cat /etc/salt/master | grep base: >>/tmp/tmp_srv-salt || echo "The roles not set to /srv/salt"
cat /etc/salt/master | grep /srv/salt || echo "The roles not set to /srv/salt"
echo "######################	End of salt				######################"

echo "######################/conf.d/sites-enabled/g /etc/nginx/nginx.conf######################"
grep sites-enabled /etc/nginx/nginx.conf >> /tmp/tmp_sites_enabled || echo "No Sites_enabled in nginx.conf"
echo "######################/conf.d/sites-enabled/g /etc/nginx/nginx.conf######################"

echo "######################		/etc/nsswitch.conf       	######################"
grep nsswitch.conf /etc/nsswitch.conf >> /tmp/tmp_nsswitch || echo "No nsswitch.conf"
echo "######################		end of /etc/nsswitch		######################"

echo "######################	rc.local of /usr/bin/uwsgi		 ######################"
grep /var/log/integralstor/integralstor_gridcell/integral_view.log /etc/rc.local >> /tmp/tmp_rc.local || echo "'rc.local' not written /usr/bin/uwsgi"
echo "######################	End of rc.local of /usr/bin/uwsgi	 ######################"

echo "######################	Other Services Status			######################"
chkconfig --list nfs >> /tmp/tmp_ssh || echo "No NFS service"
chkconfig --list smb >> /tmp/tmp_ssh || echo "No SMB service"
#chkconfig --list tgtd >> /tmp/tmp_ssh || echo "No TGTD service"
chkconfig --list winbind >> /tmp/tmp_ssh || echo "No WINBIND service"
chkconfig --list ntpd >> /tmp/tmp_ssh || echo "No NTPD service"
chkconfig --list ramdisk >> /tmp/tmp_ssh || echo "No RAMDISK service"
echo "######################	End of Other Services			######################"
echo "######################		********END********		######################"
