if ping -c 1 gridcell-pri.integralstor.lan &> /dev/null 
then
        if [ -f /opt/primary_down ]
 	then
		service salt-minion stop
		sed -i 's/gridcell-sec.integralstor.lan/gridcell-pri.integralstor.lan/' /etc/salt/minion
		service salt-minion start
 		rm /opt/primary_down
	fi	
	echo success
else
	touch /opt/primary_down
	service salt-minion stop
	sed -i 's/gridcell-pri.integralstor.lan/gridcell-sec.integralstor.lan/' /etc/salt/minion
	service salt-minion start
fi
