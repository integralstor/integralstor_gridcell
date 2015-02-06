#!/usr/bin/python

"""
This code copies the named.conf_primary and fractalio.for files frome /srv/salt to the destination i.e. path given on the minion side.
"""

import salt.client

local = salt.client.LocalClient()
minion = raw_input("Enter the minion ip or minion's hostname as in salt-key -L : ")

# Source paths
source_named_conf_primary = "salt://primary/named.conf_primary"
source_forw_zone_file = "salt://primary/fractalio.for"

# Target paths
target_named_conf_primary = "/etc/named.conf"
target_forw_zone_file = "/var/named/fractalio.for"

# Backing up and Copying the named.conf file
local.cmd(minion, 'cmd.run', ['mv /etc/named.conf /etc/original_named_conf'])
retval_named_conf_primary = local.cmd (minion, 'cp.get_file', [source_named_conf_primary, target_named_conf_primary])

# Copying the zone file
retval_forw_zone = local.cmd (minion, 'cp.get_file', [source_forw_zone_file, target_forw_zone_file])

