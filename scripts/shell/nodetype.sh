#!/bin/bash

nodetype=`cat /etc/salt/grains | tail -2 | awk '{print $2}'`

if cat /etc/salt/grains | grep primary > /dev/null ; then

  `/opt/integralstor/integralstor_common/bin/fpctl clear`
  `/opt/integralstor/integralstor_common/bin/fpctl move 0 0`
  `/opt/integralstor/integralstor_common/bin/fpctl print "Fractalio Data"`
  `/opt/integralstor/integralstor_common/bin/fpctl move 0 1`
  `/opt/integralstor/integralstor_common/bin/fpctl print "  GRIDCell-P"`

elif cat /etc/salt/grains | grep secondary > /dev/null ; then
  
  `/opt/integralstor/integralstor_common/bin/fpctl clear`
  `/opt/integralstor/integralstor_common/bin/fpctl move 0 0`
  `/opt/integralstor/integralstor_common/bin/fpctl print "Fractalio Data"`
  `/opt/integralstor/integralstor_common/bin/fpctl move 0 1`
  `/opt/integralstor/integralstor_common/bin/fpctl print "  GridCell-S"`

elif cat /etc/salt/grains | grep normal > /dev/null ; then

  `/opt/integralstor/integralstor_common/bin/fpctl clear`
  `/opt/integralstor/integralstor_common/bin/fpctl move 0 0`
  `/opt/integralstor/integralstor_common/bin/fpctl print "Fractalio Data"`
  `/opt/integralstor/integralstor_common/bin/fpctl move 0 1`
  `/opt/integralstor/integralstor_common/bin/fpctl print "  GridCell"`

else 
    
  `/opt/integralstor/integralstor_common/bin/fpctl clear`
  `/opt/integralstor/integralstor_common/bin/fpctl print "Fractalio Data"`
fi
