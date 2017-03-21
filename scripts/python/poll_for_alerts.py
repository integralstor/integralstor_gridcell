#!/usr/bin/python
import sys
import time
import socket
import logging

from integralstor_common import common, alerts, lock, command, zfs, networking, logger
from integralstor_gridcell import system_info, gluster_volumes, grid_ops

import atexit
atexit.register(lock.release_lock, 'poll_for_alerts')
atexit.register(lock.release_lock, 'gluster_commands')


def check_quotas():
    alert_list = []
    try:
        vil, err = gluster_volumes.get_complete_volume_info_all()
        if err:
            raise Exception(err)
        if vil:
            for v in vil:
                if "quotas" in v:
                    # print v['quotas']
                    for dir, quota in v['quotas'].items():
                        if v["quotas"][dir]["hl_exceeded"].lower() == "yes":
                            if dir == '/':
                                alert_list.append("Exceeded hard quota limit of %s for volume %s. All writes will be disabled. " % (
                                    v['quotas'][dir]['hard_limit_human_readable'], v['name']))
                            else:
                                alert_list.append("Exceeded hard quota limit of %s for directory %s in volume %s. All writes will be disabled. " % (
                                    v['quotas'][dir]['hard_limit_human_readable'], dir, v['name']))
                        elif v["quotas"][dir]["sl_exceeded"].lower() == "yes":
                            if dir == '/':
                                alert_list.append("Exceeded soft quota limit %s of %s quota for volume %s. Current usage is %s" % (
                                    v['quotas']['/']['soft_limit_percent'], v['quotas']['/']['hard_limit_human_readable'], v['name'], v['quotas']['/']['used_space_human_readable']))
                            else:
                                alert_list.append("Exceeded soft quota limit %s of %s quota for directory %s in volume %s. Current usage is %s" % (
                                    v['quotas'][dir]['soft_limit_percent'], v['quotas'][dir]['hard_limit_human_readable'], dir, v['name'], v['quotas'][dir]['used_space_human_readable']))
    except Exception, e:
        return None, 'Error checking volume quota status : %s' % str(e)
    else:
        return alert_list, None


def check_for_gridcell_errors(si):
    alerts_list = []
    try:
        platform, err = common.get_platform()
        if err:
            raise Exception(err)

        alerts_list = []

        # print si.keys()
        salt_connectivity, err = grid_ops.check_salt_connectivity(
            None, si.keys())
        if err:
            raise Exception(err)
        # print salt_connectivity

        for node_name, node in si.items():
            msg = 'GRIDCell  %s :  ' % node_name
            alerts = False
            res, err = networking.can_ping(node_name)
            if err:
                raise Exception(err)
            if not res:
                alerts = True
                msg += 'Cannot ping GRIDCell. '
            if node_name not in salt_connectivity or not salt_connectivity[node_name]:
                msg += 'Cannot contact admin agent on GRIDCell. '
            if 'errors' in node and node['errors']:
                alerts = True
                msg += '. '.join(node['errors'])

            if alerts:
                alerts_list.append(msg)

    except Exception, e:
        return None, 'Error polling for alerts : %s' % e
    else:
        return alerts_list, None


def main():
    lg = None
    try:
        lg, err = logger.get_script_logger(
            'Poll for alerts', '/var/log/integralstor/scripts.log', level=logging.DEBUG)

        logger.log_or_print('Poll for alerts initiated.', lg, level='info')

        lck, err = lock.get_lock('poll_for_alerts')
        if err:
            raise Exception(err)
        if not lck:
            raise Exception('Could not acquire lock. Exiting.')

        active, err = grid_ops.is_active_admin_gridcell()
        if err:
            raise Exception(err)

        if not active:
            logger.log_or_print(
                'Not active admin GRIDCell so exiting.', lg, level='info')
            sys.exit(0)

        gluster_lck, err = lock.get_lock('gluster_commands')
        if err:
            raise Exception(err)

        si, err = system_info.load_system_config()
        if err:
            raise Exception(err)

        if not si:
            raise Exception('Could not load system information')

        alerts_list = []

        alerts_list, err = check_quotas()
        if err:
            raise Exception("Error getting quota information : %s" % err)

        lock.release_lock('gluster_commands')

        common_alerts, err = check_for_gridcell_errors(si)
        if err:
            raise Exception(err)

        alerts_list.extend(common_alerts)

        if alerts_list:
            alerts.raise_alert(alerts_list)
            str = ' | '.join(alerts_list)
            logger.log_or_print(str, lg, level='info')
        else:
            logger.log_or_print('No alerts to raise', lg, level='info')

        lock.release_lock('poll_for_alerts')
    except Exception, e:
        str = 'Error running poll for alerts  : %s' % e
        logger.log_or_print(str, lg, level='critical')
        sys.exit(-1)
    else:
        logger.log_or_print('Poll for alerts completed.', lg, level='info')
        sys.exit(0)


if __name__ == "__main__":
    main()


# vim: tabstop=8 softtabstop=0 expandtab ai shiftwidth=4 smarttab
