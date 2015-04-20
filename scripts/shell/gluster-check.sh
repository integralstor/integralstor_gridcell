#!/bin/bash

#check peer status
`gluster peer status | grep State | grep "Disconnected" >> /dev/null 2>&1`
if [ $? -eq 0 ]; then

   for vol in `gluster volume list`
   do
       state=`gluster volume info $vol | grep Status | grep "Started" >> /dev/null 2>&1`
       if [ $? -eq 0 ]; then
            status=`gluster volume status $vol | grep "Y" | wc -l`
            if [ $status -lt 3 ]; then
                 gluster volume start $vol force
            fi
       fi
   done
fi
