#!/usr/bin/python

"""
This code copies the named.conf_secondary file frome /srv/salt to the destinated minion i.e. path given on the minion side.
"""

import salt.client

local = salt.client.LocalClient()
minion = raw_input("Enter the minion ip or minion's hostname as in salt-key -L : ")

# Source paths
source_named_conf_secondary = "salt://secondary/named.conf_secondary"

# Target paths
target_named_conf_secondary = "/etc/named.conf"

# Backing up and Copying the named.conf file
local.cmd(minion, 'cmd.run', ['mv /etc/named.conf /etc/original_named_conf'])
retval_named_conf_secondary = local.cmd (minion, 'cp.get_file', [source_named_conf_secondary, target_named_conf_secondary])

