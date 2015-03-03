chmod +x /opt/fractalio/bin/fpctl
mkdir -p /run/samba
chkconfig ctdb on
chkconfig glusterd on
chkconfig named on
modprobe ipmi_devintf
echo "modprobe ipmi_devintf" >> /etc/rc.local
chmod +x /etc/init.d/ramdisk
chkconfig ramdisk on
yes | rm -rf /etc/salt/pki/minion/minion_master.pub
yes | rm /etc/salt/minion_id
sed -i 's/\$ZFS mount -a/\$ZFS mount -O -a/' /etc/init.d/zfs
sed -i 's/master: 10.1.1.200/master: fractalio-pri/' /etc/salt/minion
rm -rf /tmp/*
shutdown -r now
