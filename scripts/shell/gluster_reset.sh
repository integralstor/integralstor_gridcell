echo "Stopping all gluster volumes and services"
gluster volume stop fractalio_admin_vol
gluster volume delete fractalio_admin_vol

echo "Deleting all the pools"
rm -rf /frzpool/normal/fractalio_admin_vol

echo "Detaching peers"
gluster peer detach secondary.fractalio.lan

"Editing fstab"
sed -i '/localhost/d' /etc/fstab

echo "Unmounting admin_vol"
umount /opt/fractalio/mnt/admin_vol 

echo "Please press 'y'"
salt '*' saltutil.clear_cache

salt-key -D

echo "Stopping salt minion"

service salt-minion stop

echo "Phew ! All done ahoy ! Now start the salt-minion and please the status of named"

