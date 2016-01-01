#!/bin/bash

#IP=`ifconfig bond0 | awk '/inet addr/{print substr($2,6)}'`
if mount | grep /opt/integralstor/integralstor_gridcell/config > /dev/null; then
  if ! [ -d "/opt/integralstor/integralstor_gridcell/config/config_backup" ]; then
    mkdir /opt/integralstor/integralstor_gridcell/config/config_backup
  fi
  if ! [ -d "/opt/integralstor/integralstor_gridcell/config/config_backup/glusterd" ]; then
    mkdir /opt/integralstor/integralstor_gridcell/config/config_backup/glusterd
  fi
  if ! [ -d "/opt/integralstor/integralstor_gridcell/config/config_backup/named" ]; then
    mkdir /opt/integralstor/integralstor_gridcell/config/config_backup/named
  fi
  if [ -d "/var/lib/glusterd" ]; then
    cp -rf /var/lib/glusterd /opt/integralstor/integralstor_gridcell/config/config_backup/glusterd/$HOSTNAME
  fi
  if hostname | grep gridcell-pri > /dev/null; then
    rndc freeze integralstor.lan
    cp -rf /var/named /opt/integralstor/integralstor_gridcell/config/config_backup/named/$HOSTNAME
    rndc thaw integralstor.lan
  elif hostname | grep gridcell-sec > /dev/null; then
    cp -rf /var/named /opt/integralstor/integralstor_gridcell/config/config_backup/named/$HOSTNAME
  fi
else
  echo "Admin volume not mounted so could not backup the configuration"
fi
