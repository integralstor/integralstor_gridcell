salt=$(service salt-minion status)
if [ "$salt" == "salt-minion dead but pid file exists" ]; then
	service salt-minion restart
fi
if [ "$salt" == "salt-minion is stopped" ]; then
	service salt-minion start
fi
