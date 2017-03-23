
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
    except Exception, e:
        return False, is_change, "Couldn't sync ctdb files: %s" % str(e)
    else:
        return True, is_change, None


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

            is_pooled, err = gluster_trusted_pools.get_peer_list()
            if is_pooled:
                mounted, err = grid_ops.is_admin_vol_mounted_local()
                if not mounted:
                    for admin_gridcell in admin_gridcells:
                        reachable, err = networking.can_ping(admin_gridcell)
                        if reachable:
                            (ret, rc), err = command.execute_with_rc(
                                'mount -t glusterfs %s:/%s %s' % (admin_gridcell, admin_vol_name, config_dir))
                            if (not err) and (rc == 0):
                                mounted = True
                                sync, is_change, error = sync_ctdb_files()
                                if error:
                                    # It's only a best-effort, it will try next
                                    # minute again.
                                    pass
                                if sync == False:
                                    #raise Exception (err)
                                    pass
                                if sync == True and is_change == True:
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
                                            'Service ctdb error : %s' % err, lg, level='error')

                                """
                # Restart winbind
                out, err = command.get_command_output('service winbind restart', False, True)
		if not err and out:
		  logger.log_or_print('Service winbind: %s'%out, lg, level='debug')
		else:
		  logger.log_or_print('Service winbind error : %s'%err, lg, level='error')
                # Restart smb
                out, err = command.get_command_output('service smb restart', False, True)
		if not err and out:
		  logger.log_or_print('Service smb: %s'%out, lg, level='debug')
		else:
		  logger.log_or_print('Service smb error : %s'%err, lg, level='error')
                """

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
                                break
                            else:
                                str = 'Mount from %s failed.' % admin_gridcell
                                logger.log_or_print(str, lg, level='error')
                    if not mounted:
                        str = 'Failed to mount admin volume!'
                        logger.log_or_print(str, lg, level='critical')
                else:
                    sync, is_change, err = sync_ctdb_files()
                    if err:
                        raise Exception(err)
                    if sync == False:
                        raise Exception(err)
                    if sync == True and is_change == True:
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
                                'Service ctdb error : %s' % err, lg, level='error')

                    logger.log_or_print('Checking services', lg, level='debug')
                    for service in ['nginx', 'ctdb']:
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

                '''
	if mounted:
	  path_dict = {'/etc/krb5.conf':'%s/lock/krb5.conf'%config_dir, '/etc/samba/smb.conf':'%s/lock/smb.conf'%config_dir, '/etc/ctdb/nodes':'%s/lock/smb.conf'%config_dir, '/etc/sysconfig/ctdb':'%s/lock/ctdb'%config_dir}
	  for link, file in path_dict.items():
	    if os.path.islink(link) or os.path.isfile(link):
	      print link, 'exists so removing'
	      os.remove(link)
	    os.symlink(file, link)
	else:
	  raise Exception('Could not mount the admin volume')
	'''
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
