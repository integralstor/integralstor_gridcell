#!/bin/bash
echo "Updating the ZFS and Other modules..."
yes | yum update zfs zfs-dkms spl spl-dkms >&2
echo "Successfully Updated ZFS and other modules."
echo
echo "Started Upgrading Software..."
# Setup IntegralStor Common
cd /tmp
rm -rf /tmp/integralstor_*
/usr/bin/wget -c http://192.168.1.150/netboot/distros/centos/6.6/x86_64/integralstor_gridcell/v1.0/tar_installs/integralstor_common.tar.gz
/bin/tar xzf integralstor_common.tar.gz
yes | cp -rf /tmp/integralstor_common/site-packages/integralstor_common/* /opt/integralstor/integralstor_common/site-packages/integralstor_common

# Setup IntegralStor GRIDCell
cd /tmp
/usr/bin/wget -c http://192.168.1.150/netboot/distros/centos/6.6/x86_64/integralstor_gridcell/v1.0/tar_installs/integralstor_gridcell.tar.gz
/bin/tar xzf integralstor_gridcell.tar.gz
yes | cp -rf /tmp/integralstor_gridcell/integral_view/* /opt/integralstor/integralstor_gridcell/integral_view
yes | cp -rf /tmp/integralstor_gridcell/site-packages/integralstor_gridcell/* /opt/integralstor/integralstor_gridcell/site-packages/integralstor_gridcell
#yes | cp -rf /opt/integralstor/integralstor_gridcell/config /opt/integralstor
### Apply quota information on every reboot if quota is not applied ###
echo "sh /opt/integralstor_gridcell/scripts/shell/set_pool_quota.sh" >> /etc/rc.local

(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/integralstor/integralstor_gridcell/scripts/python/poll_for_alerts.py > /tmp/out_gluster_alerts >> /tmp/err_gluster_alerts >> /opt/integralstor/integralstor_gridcell/config/logs/gluster_poll_for_alerts.log 2>&1 # Poll for alerts") | crontab -
echo "Software updated successfully."
