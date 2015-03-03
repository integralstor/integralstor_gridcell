#!/bin/bash

service salt-minion stop
rm -rf /var/cache/salt
rm -rf /var/run/salt
rm -rf /etc/salt/pki
rm /etc/salt/minion/minion_id
service salt-minion start
