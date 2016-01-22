#!/bin/bash
salt=$(/sbin/service salt-minion status)
if [ "$salt" == "salt-minion dead but pid file exists" ]; then
	/sbin/service salt-minion restart
fi
if [ "$salt" == "salt-minion is stopped" ]; then
	/sbin/service salt-minion start
fi
