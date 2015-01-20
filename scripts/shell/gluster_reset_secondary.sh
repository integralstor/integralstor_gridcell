echo "Removing pools ..."
rm -rf /frzpool/normal/fractalio_admin_vol

echo "Editing fstab"
sed -i '/localhost/d' /etc/fstab

echo "Unmounting admin_vol"
umount /opt/fractalio/mnt/admin_vol 

echo "Stopping salt-minion"
service salt-minion stop

zfs destroy frzpool/normal/fractalio_admin_vol

service salt-minion restart

echo "Start the salt minion now"
