#!/bin/bash

if [ "$HOSTNAME" = "gridcell-pri" ]; then		#Checks if it is Primary master then exit, else continue.
	echo "This is Primary Master so exiting..."
        exit 0
	service ntpd stop

	sleep 3
elif [ "$HOSTNAME" = "gridcell-sec" ]; then		#if it is secondary then sync with Primary else if it is normal then with pri or sec.
        ntpdate -u gridcell-pri.integralstor.lan
        echo "NTP of $HOSTNAME is synched with NTP of gridcell-pri."
	sleep 3
else
	sleep 3
        ntpdate -u gridcell-pri.integralstor.lan || ntpdate -u gridcell-sec.integralstor.lan
        echo "NTP of $HOSTNAME is synched with NTP of Master servers."
fi

service ntpd start

