echo "Stopping all gluster volumes and services"
gluster volume stop integralstor_admin_vol
gluster volume delete integralstor_admin_vol

echo "Deleting all the pools"
zfs destroy frzpool/normal/integralstor_admin_vol
rm -rf /frzpool/normal/integralstor_admin_vol

echo "Detaching peers"
gluster peer detach gridcell-sec.integralstor.lan

service glusterd restart
"Editing fstab"
sed -i '/localhost/d' /etc/fstab

echo "Unmounting admin_vol"
umount /opt/integralstor/integralstor_gridcell/config


salt '*' saltutil.clear_cache
salt-key -D

echo "Stopping salt master and minion"
service salt-master stop
service salt-minion stop

echo "Deleteing salt pki"
rm -rf /etc/salt/pki

echo "Starting salt master and minion"
service salt-master start
service salt-minion start

rm /etc/ctdb/nodes
rm /etc/sysconfig/ctdb
touch /etc/ctdb/nodes
touch /etc/sysconfig/ctdb


#cp /opt/fractalio/defaults/named/named.conf /etc/named.conf
#service named restart

echo "Phew ! All done ahoy ! Now start the salt-minion and please the status of named"

