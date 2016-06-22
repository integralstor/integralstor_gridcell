#!/bin/bash
echo "IntegralStor Upgrade started... Do not reboot or shutdown the system."

ip=$1
echo "Adding updates repository"

touch /etc/yum.repos.d/fractalio.repo
#Create and enable the fractalio.repo for pull
cat << EOF > /etc/yum.repos.d/fractalio.repo
[fractalio]
enabled=1
name= Fractalio- Updates
baseurl=http://$ip/netboot/distros/centos/6.6/x86_64/integralstor_gridcell/v1.0/rpms_zfs-0.6.5.6
gpgcheck=0
EOF

echo "Finished adding updates repository"

echo "Pulling filesystem updates"
yes | yum update zfs zfs-dkms spl spl-dkms >&2
echo "Filesystem update successful"

echo "Pulling IntegralView updates"
# Setup IntegralStor Common
mkdir /opt/integralstor/integralstor_gridcell/install/upgrade
cd /tmp
rm -rf /tmp/integralstor_*
/usr/bin/wget -c http://$ip/netboot/distros/centos/6.6/x86_64/integralstor_gridcell/v1.0/tar_installs/integralstor_common.tar.gz
/bin/tar xzf integralstor_common.tar.gz
yes | cp -rf /tmp/integralstor_common /opt/integralstor

rm -rf /tmp/integralstor_common*

# Setup IntegralStor GRIDCell
cd /tmp
/usr/bin/wget -c http://$ip/netboot/distros/centos/6.6/x86_64/integralstor_gridcell/v1.0/tar_installs/integralstor_gridcell.tar.gz
/bin/tar xzf integralstor_gridcell.tar.gz
yes | cp -rf /tmp/integralstor_gridcell/integral_view/* /opt/integralstor/integralstor_gridcell/integral_view
yes | cp -rf /tmp/integralstor_gridcell/site-packages/integralstor_gridcell/* /opt/integralstor/integralstor_gridcell/site-packages/integralstor_gridcell
yes | cp -rf /tmp/integralstor_gridcell/version /opt/integralstor/integralstor_gridcell
yes | cp -rf /tmp/integralstor_gridcell/defaults /opt/integralstor/integralstor_gridcell
yes | cp -rf /tmp/integralstor_gridcell/scripts /opt/integralstor/integralstor_gridcell
yes | cp -rf /tmp/integralstor_gridcell/install/upgrade/* /opt/integralstor/integralstor_gridcell/install/upgrade

rm -rf /tmp/integralstor_gridcell*

#yes | cp -rf /opt/integralstor/integralstor_gridcell/config /opt/integralstor
echo "IntegralView update successful"


### Apply quota information on every reboot if quota is not applied ###
echo "Checking pool status "
echo "sh /opt/integralstor/integralstor_gridcell/scripts/shell/set_pool_quota.sh" >> /etc/rc.local
echo "Pool status ok . . . "

echo "Updating Misc Scripts"

echo -e "PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin \n$(crontab -l)" | crontab -
echo -e "SHELL=/bin/sh \n$(crontab -l)" | crontab -

if [ "$HOSTNAME" == "gridcell-pri" ]; then		# Host specific. If Gridcell is primary then only update this cron.


(crontab -l 2>/dev/null; echo ) | crontab -

(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/integralstor/integralstor_gridcell/scripts/python/poll_for_alerts.py > /tmp/out_gluster_alerts >> /tmp/err_gluster_alerts >> /opt/integralstor/integralstor_gridcell/config/logs/gluster_poll_for_alerts.log 2>&1 # Poll for alerts") | crontab -
fi

echo "Finished updating misc scripts"

echo "Pulling Database updates"
sqlite3 /opt/integralstor/integralstor_gridcell/defaults/db/integral_view_config.db <<"EOF"
ALTER TABLE email_config ADD COLUMN "email_audit" bool NOT NULL DEFAULT '0';
EOF
sqlite3 /opt/integralstor/integralstor_gridcell/defaults/db/integral_view_config.db <<"EOF"
ALTER TABLE email_config ADD COLUMN "email_quota" bool NOT NULL DEFAULT '0';
EOF
sqlite3 /opt/integralstor/integralstor_gridcell/config/db/integral_view_config.db <<"EOF"
ALTER TABLE email_config ADD COLUMN "email_audit" bool NOT NULL DEFAULT '0';
EOF
sqlite3 /opt/integralstor/integralstor_gridcell/config/db/integral_view_config.db <<"EOF"
ALTER TABLE email_config ADD COLUMN "email_quota" bool NOT NULL DEFAULT '0';
EOF
echo "Databases update successful."

echo "Removing updates repository"

#Disable the fractalio.repo once the upgrade is done.
cat << EOF > /etc/yum.repos.d/fractalio.repo
[fractalio]
enabled=0
name= Fractalio- Updates
baseurl=http://$ip/netboot/distros/centos/6.6/x86_64/integralstor_gridcell/v1.0/rpms_zfs-0.6.5.6
gpgcheck=0
EOF

echo "Successfully removed updates repository"

echo "IntegralStor GRIDCell has been successfully updated to :"
cat /opt/integralstor/integralstor_gridcell/version
