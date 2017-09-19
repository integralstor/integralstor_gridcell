
import os
import socket
import sys
import subprocess
import logging
import shutil
from integralstor_utils import config, networking, command, logger, services_management
from integralstor_gridcell import grid_ops, gluster_trusted_pools


def sync_ctdb_files():
    """
    Syncs CTDB files on the localhost with the mounted admin vol.

    Input:
      ['None']
    Output:
      Returns three variables [ret1,ret2,ret3]:
        ret1 -- True if sync was sucessful, else False
        ret2 -- True if there was a difference, False if they were already in sync
        ret3 -- None if there were no errors/exceptions, 'Error string' otherwise
    """

    is_change = False
    try:
        config_dir, err = config.get_config_dir()
        if err:
            raise Exception(err)

        out, err = command.get_command_output(
            'diff "/etc/sysconfig/ctdb" "%s/lock/ctdb"' % str(config_dir), True, True)
        if err:
            shutil.copyfile('%s/lock/ctdb' %
                            str(config_dir), '/etc/sysconfig/ctdb')
            is_change = True

        out, err = command.get_command_output(
            'diff "/etc/ctdb/nodes" "%s/lock/nodes"' % str(config_dir), True, True)
        if err:
            shutil.copyfile('%s/lock/nodes' %
                            str(config_dir), '/etc/ctdb/nodes')
            is_change = True

        out, err = command.get_command_output(
            'diff "/etc/ctdb/public_addresses" "%s/lock/public_addresses"' % str(config_dir), True, True)
        if err:
            shutil.copyfile('%s/lock/public_addresses' %
                            str(config_dir), '/etc/ctdb/public_addresses')
            is_change = True

        lg, err = logger.get_script_logger(
            'Admin volume mounter: Sync CTDB config files', '/var/log/integralstor/scripts.log', level=logging.DEBUG)
        if is_change == True:
            logger.log_or_print(
                'ctdb related files were synced.', lg, level='info')
            logger.log_or_print(
                'Restarting ctdb.', lg, level='debug')
            out, err = command.get_command_output(
                'service ctdb restart', False, True)
            if not err and out:
                logger.log_or_print(
                    'Service ctdb: %s' % out, lg, level='debug')
            else:
                logger.log_or_print(
                    'Service ctdb error: %s' % err, lg, level='error')
        elif is_change == False:
            logger.log_or_print(
                'ctdb related files are in sync.', lg, level='info')

    except Exception, e:
        return False, is_change, "Couldn't sync ctdb files: %s" % str(e)
    else:
        return True, is_change, None



def assert_admin_vol_mount():
    try:
        # Check if the admin vol mount actually succeded by reading a file from the admin volume
        # Tries 3 times. Bail out if unsuccessfull
        config_dir, err = config.get_config_dir()
        if err:
            raise Exception(err)

        iter = 3
        while (iter):
            iter -= 1
            is_mounted, err = grid_ops.is_admin_vol_mounted_local()
            if err or (is_mounted is False):
                time.sleep(5)
            elif is_mounted is True:
                break
        if iter < 1:
            raise Exception("Admin volume is not mounted!")

    except Exception, e:
        return False, "Couldn't assert mount point access: %s" % str(e)
    else:
        return True, None


def mount_and_configure():
    lg = None
    try:
        lg, err = logger.get_script_logger(
            'Admin volume mounter', '/var/log/integralstor/scripts.log', level=logging.DEBUG)

        logger.log_or_print(
            'Admin volume mounter initiated.', lg, level='info')

        pog, err = grid_ops.is_part_of_grid()
        if err:
            raise Exception(err)

        # If the localhost is part of the gridcell, proceed
        if pog:
            logger.log_or_print('Checking glusterd service', lg, level='debug')
            service = 'glusterd'
            status, err = services_management.get_service_status([service])
            if err:
                raise Exception(err)
            logger.log_or_print('Service %s status is %s' % (
                service, status['status_code']), lg, level='debug')
            if status['status_code'] != 0:
                logger.log_or_print(
                    'Service %s not started so restarting' % service, lg, level='error')
                out, err = command.get_command_output(
                    'service %s restart' % service, False, True)
                if not err and out:
                    logger.log_or_print('Service %s: %s' %
                                        (service, out), lg, level='debug')
                else:
                    logger.log_or_print('Service %s error : %s' % (
                        service, err), lg, level='error')

            admin_vol_name, err = config.get_admin_vol_name()
            if err:
                raise Exception(err)

            # Get the config dir - the mount point.
            config_dir, err = config.get_config_dir()
            if err:
                raise Exception(err)

            ag, err = grid_ops.is_admin_gridcell()
            if err:
                raise Exception(err)

            admin_gridcells, err = grid_ops.get_admin_gridcells()
            if err:
                raise Exception(err)

            is_pooled = False
            peer_list, err = gluster_trusted_pools.get_peer_list()
            if peer_list:
                is_pooled = True

            is_mounted = False
            # mount only if the localhost is pooled
            if is_pooled:
                is_mounted, err = grid_ops.is_admin_vol_mounted_local()
                if not is_mounted:
                    str = 'Admin volume is not mounted. Will attempt to mount now.' 
                    logger.log_or_print(str, lg, level='error')

                    # Try to mount
                    (ret, rc), err = command.execute_with_rc(
                        'mount -t glusterfs localhost:/%s %s' % (admin_vol_name, config_dir))
                    if err:
                        str = 'Mount from localhost failed.' 
                        logger.log_or_print(str, lg, level='error')
                    elif (not err) and (rc == 0):
                        is_access, err = assert_admin_vol_mount()
                        if err:
                            raise Exception(err)

                        sync, is_change, error = sync_ctdb_files()
                        if error:
                            # It's only a best-effort, it will try next
                            # minute again.
                            pass
                        if sync == False:
                            #raise Exception (err)
                            pass

                        # Restart nginx
                        out, err = command.get_command_output(
                            'service nginx restart', False, True)
                        if not err and out:
                            logger.log_or_print(
                                'Service nginx: %s' % out, lg, level='debug')
                        else:
                            logger.log_or_print(
                                'Service nginx error : %s' % err, lg, level='error')
                        # Restart uwsgi
                        out, err = command.get_command_output(
                            'service uwsgi restart', False, True)
                        if not err and out:
                            logger.log_or_print(
                                'Service uwsgi: %s' % out, lg, level='debug')
                        else:
                            logger.log_or_print(
                                'Service uwsgi error : %s' % err, lg, level='error')

                        if ag:
                            # Restart salt-master
                            out, err = command.get_command_output(
                                'service salt-master restart', False, True)
                            if not err and out:
                                logger.log_or_print(
                                    'Service salt-master: %s' % out, lg, level='debug')
                            else:
                                logger.log_or_print(
                                    'Service salt-master error : %s' % err, lg, level='error')
                            # Restart salt-minion
                        out, err = command.get_command_output(
                            'service salt-minion restart', False, True)
                        if not err and out:
                            logger.log_or_print(
                                'Service salt-minion: %s' % out, lg, level='debug')
                        else:
                            logger.log_or_print(
                                'Service salt-minion error : %s' % err, lg, level='error')

                    str = 'Admin vol is mounted'
                    logger.log_or_print(str, lg, level='info')

                # Admin volume is mounted, perform required checks
                else:
                    sync, is_change, err = sync_ctdb_files()
                    if err:
                        raise Exception(err)
                    if sync == False:
                        raise Exception(err)

                    logger.log_or_print('Checking services', lg, level='debug')
                    service_list = ['nginx','ctdb','salt-minion']
                    if ag:
                        service_list.append('salt-master')

                    for service in service_list:
                        status, err = services_management.get_service_status([
                                                                             service])
                        if err:
                            raise Exception(err)
                        logger.log_or_print('Service %s status is %s' % (
                            service, status['status_code']), lg, level='debug')
                        if status['status_code'] != 0:
                            logger.log_or_print(
                                'Service %s is not active, restarting' % service, lg, level='error')
                            out, err = command.get_command_output(
                                'service %s restart' % service, False, True)
                            if not err and out:
                                logger.log_or_print('Service %s: %s' % (
                                    service, out), lg, level='debug')
                            else:
                                logger.log_or_print('Service %s error : %s' % (
                                    service, err), lg, level='error')

                    # UWSGI service config not complete so need to check
                    # against the actual process name
                    (ret, rc), err = command.execute_with_rc(
                        'pidof uwsgi', shell=True)
                    if rc != 0:
                        logger.log_or_print(
                            'Service uwsgi is not active, restarting', lg, level='error')
                        out, err = command.get_command_output(
                            'service uwsgi restart', False, True)
                        if not err and out:
                            logger.log_or_print(
                                'Service uwsgi: %s' % out, lg, level='debug')
                        else:
                            logger.log_or_print(
                                'Service uwsgi error : %s' % err, lg, level='error')

                    str = 'Admin volume is already mounted'
                    logger.log_or_print(str, lg, level='info')

    except Exception, e:
        st = 'Error mounting admin volume : %s' % e
        logger.log_or_print(st, lg, level='critical')
        return False, st
    else:
        str = 'Admin volume mounter completed.'
        logger.log_or_print(str, lg, level='info')
        return True, None


def main():
    ret, err = mount_and_configure()
    print ret, err
    if err:
        print err
        sys.exit(-1)


if __name__ == '__main__':
    main()

# vim: tabstop=8 softtabstop=0 expandtab ai shiftwidth=4 smarttab
