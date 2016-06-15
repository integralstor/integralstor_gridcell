#!/bin/bash

touch /etc/yum.repos.d/fractalio.repo
echo
read -t 60 -p "Enter the IP from which the upgrade needs to be happen: " input
echo "Pulling updates from : " $input
read -t 30 -p "Press 'yes' to Confirm: " confirm

if [ "$confirm" == "yes" ]; then

#Create and enable the fractalio.repo for pull
cat << EOF > /etc/yum.repos.d/fractalio.repo
[fractalio]
enabled=1
name= Fractalio- Updates
baseurl=http://$input/netboot/distros/centos/6.6/x86_64/integralstor_gridcell/v1.0/rpms_zfs-0.6.5.6
gpgcheck=0
EOF
cd /tmp
wget -c http://$input/netboot/distros/centos/6.6/x86_64/integralstor_gridcell/v1.0/updater.sh
chmod +x /tmp/updater.sh
/tmp/updater.sh
read -t 30 -p "Successfully Updated to Latest software. Press 'yes' to restart the system now: " again
	if [ "$again" == "yes" ]; then
		reboot now
	else
		echo "You must restart your server before the new settings will take effect."
	fi
else
echo "Something went wrong. Please try again..."
fi
rm -f /tmp/updater.sh

#Disable the fractalio.repo once the upgrade is done.
cat << EOF > /etc/yum.repos.d/fractalio.repo
[fractalio]
enabled=0
name= Fractalio- Updates
baseurl=http://$input/netboot/distros/centos/6.6/x86_64/integralstor_gridcell/v1.0/rpms_zfs-0.6.5.6
gpgcheck=0
EOF
