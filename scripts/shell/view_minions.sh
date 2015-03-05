#!/bin/bash
hn=`hostname`
if [ $hn == "fractalio-pri" ]
then
  echo "Node connection status :"
  salt-key -L
else
  echo 'This can only be run on a primary GRIDCell'
fi
