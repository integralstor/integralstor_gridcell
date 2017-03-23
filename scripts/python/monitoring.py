
import socket
import sys
from time import strftime
from integralstor_gridcell import grid_ops, dns
from integralstor_utils import networking, command, disks


def check_salt_status(print_to_stdout=True, separator='\n'):
    ret_list = []
    try:
        if print_to_stdout:
            ret_list.append(
                'IntegralStor Monitoring agents and processes status')

        out, err = command.get_command_output(
            'service salt-master status', False)
        if err:
            raise Exception(err)
        ret_list.append('Monitoring service master status : %s' %
                        ','.join(out))

        out, err = command.get_command_output(
            'service salt-minion status', False)
        if err:
            raise Exception(err)
        ret_list.append('Monitoring service agent status : %s' % ','.join(out))

        keys, err = grid_ops.get_all_salt_keys()
        if err:
            raise Exception(err)
        if keys:
            ret_list.append(
                separator + 'Admin agents that are part of the grid : ')
            ret_list.append(separator.join(keys['minions']))
            ret_list.append(
                separator + 'Admin agents that are pending to be accepted into grid : ')
            ret_list.append(separator.join(keys['minions_pre']))
        results, err = grid_ops.salt_ping_all()
        if err:
            raise Exception(err)
        if results:
            ret_list.append(separator + 'Admin agent reachability :')
            for minion, result in results.items():
                if result:
                    st = 'Reachable'
                else:
                    st = '**Not reachable**'
                ret_list.append('%s : %s' % (minion, st))
        if print_to_stdout:
            print separator.join(ret_list)

    except Exception, e:
        return None, 'Error checking admin service status : %s' % str(e)
    else:
        return ret_list, None


def check_network_ping_status(print_to_stdout=True, separator='\n'):
    ret_list = []
    try:
        if print_to_stdout:
            ret_list.append('Network connectivity status : ')
        known_hosts, err = dns.get_known_hosts()
        if err:
            raise Exception(err)
        if known_hosts:
            for ip, hn in known_hosts.items():
                reachable, err = networking.can_ping(hn)
                if not reachable:
                    status = '**Not reachable**'
                else:
                    status = 'Reachable'
                ret_list.append('%s (%s) : %s' % (hn, ip, status))
        if print_to_stdout:
            print separator.join(ret_list)
    except Exception, e:
        return None, 'Error checking network connectivity status : %s' % str(e)
    else:
        return ret_list, None


def check_admin_vol_started(print_to_stdout=True, separator='\n'):
    ret_list = []
    try:
        if print_to_stdout:
            ret_list.append('Admin volume status : ')
        out, err = command.get_command_output(
            'gluster volume info integralstor_admin_vol | grep Status', shell=True)
        if err:
            raise Exception(err)
        ret_list.append(out[0])
        if print_to_stdout:
            print separator.join(ret_list)
    except Exception, e:
        return None, 'Error checking admin volume status: %s' % str(e)
    else:
        return ret_list, None


def check_admin_vol_mountpoint(print_to_stdout=True, separator='\n'):
    ret_list = []
    try:
        ret, err = grid_ops.check_admin_volume_mountpoint()
        if err:
            raise Exception(err)
        if ret:
            status = 'Admin voume mountpoint status : accessible'
        else:
            status = 'Admin voume mountpoint status : not accessible'
        ret_list.append(status)
        if print_to_stdout:
            print separator.join(ret_list)
    except Exception, e:
        return None, 'Error checking admin volume mountpoint status: %s' % str(e)
    else:
        return ret_list, None


def check_admin_vol_status(print_to_stdout=True, separator='\n'):
    ret_list = []
    try:
        if print_to_stdout:
            ret_list.append('Admin volume process status : ')
        out, err = command.get_command_output(
            'gluster volume status integralstor_admin_vol ')
        if err:
            raise Exception(err)
        ret_list.extend(out)
        if print_to_stdout:
            print separator.join(ret_list)
    except Exception, e:
        return None, 'Error checking admin volume process status: %s' % str(e)
    else:
        return ret_list, None


def check_gluster_peer_status(print_to_stdout=True, separator='\n'):
    ret_list = []
    try:
        if print_to_stdout:
            ret_list.append('Distributed storage pool status : ')
        out, err = command.get_command_output('gluster peer status')
        if err:
            raise Exception(err)
        ret_list.extend(out)
        if print_to_stdout:
            print separator.join(ret_list)
    except Exception, e:
        return None, 'Error checking admin volume process status: %s' % str(e)
    else:
        return ret_list, None


def check_zfs_pool_status(print_to_stdout=True, separator='\n'):
    ret_list = []
    try:
        if print_to_stdout:
            ret_list.append('Underlying GRIDCell ZFS storage pool status : ')
        out, err = command.get_command_output('zpool status')
        if err:
            raise Exception(err)
        ret_list.extend(out)
        if print_to_stdout:
            print separator.join(ret_list)
    except Exception, e:
        return None, 'Error checking underlying GRIDCell ZFS storage pool status: %s' % str(e)
    else:
        return ret_list, None


def check_ipmi(print_to_stdout=True, separator='\n'):
    ret_list = []
    try:
        if print_to_stdout:
            ret_list.append('Underlying hardware status : ')
        out, err = command.get_command_output('ipmitool sdr')
        if err:
            raise Exception(err)
        ret_list.extend(out)
        if print_to_stdout:
            print separator.join(ret_list)
    except Exception, e:
        return None, 'Error checking hardware status: %s' % str(e)
    else:
        return ret_list, None


def check_disks_status(print_to_stdout=True, separator='\n'):
    ret_list = []
    try:
        if print_to_stdout:
            ret_list.append('Underlying hard drives status : ')
        all_disks, err = disks.get_disk_info_all()
        if err:
            raise Exception(err)
        if all_disks:
            for serial_num, info in all_disks.items():
                ret_list.append('Serial number : %s, capacity : %s, Status : %s' % (
                    serial_num, info['capacity'], info['status']))
        if print_to_stdout:
            print separator.join(ret_list)
    except Exception, e:
        return None, 'Error checking hardware status: %s' % str(e)
    else:
        return ret_list, None


def check_windows_processes_status(print_to_stdout=True, separator='\n'):
    ret_list = []
    try:
        if print_to_stdout:
            ret_list.append('GRIDCell windows access processes status: ')
        out, err = command.get_command_output('service smb status', False)
        if err:
            raise Exception(err)
        ret_list.append('Windows (SMB) process status : %s' % ', '.join(out))
        out, err = command.get_command_output('service winbind status', False)
        if err:
            raise Exception(err)
        ret_list.append('Windows (winbind) process status : %s' %
                        ', '.join(out))
        out, err = command.get_command_output('service ntpd status', False)
        if err:
            raise Exception(err)
        ret_list.append('Time sync (NTP) process status : %s' % ', '.join(out))
        '''
    Commenting out as we wont use CTDB for this release
    out, err = command.get_command_output('service ctdb status', False)
    if err:
      raise Exception(err)
    ret_list.append('Clustered windows access (CTDB) process status : %s'%', '.join(out))
    '''
        if print_to_stdout:
            print separator.join(ret_list)
    except Exception, e:
        return None, 'Error checking windows access process status: %s' % str(e)
    else:
        return ret_list, None


def check_ctdb_status(print_to_stdout=True, separator='\n'):
    ret_list = []
    try:
        out, err = command.get_command_output('ctdb status', False)
        if err:
            raise Exception(err)
        if print_to_stdout:
            ret_list.append('Clustered windows (CTDB) status of GRIDCells: ')
        ret_list.extend(out)
        if print_to_stdout:
            print separator.join(ret_list)
    except Exception, e:
        return None, 'Error checking clustered windows access status: %s' % str(e)
    else:
        return ret_list, None


def check_integralview_processes_status(print_to_stdout=True, separator='\n'):
    ret_list = []
    try:
        if print_to_stdout:
            ret_list.append('GRIDCell IntegralView processes status: ')
        out, err = command.get_command_output('service nginx status', False)
        if err:
            raise Exception(err)
        ret_list.append('Web server (NGINX) status : %s' % ', '.join(out))
        out, err = command.get_command_output('service uwsgi status', False)
        if err:
            raise Exception(err)
        ret_list.append(
            'Web application server (uwsgi) status : %s' % ', '.join(out))
        if print_to_stdout:
            print separator.join(ret_list)
    except Exception, e:
        return None, 'Error checking IntegralView  process status: %s' % str(e)
    else:
        return ret_list, None


def check_gluster_processes_status(print_to_stdout=True, separator='\n'):
    ret_list = []
    try:
        if print_to_stdout:
            ret_list.append('GRIDCell distributed storage processes status: ')
        out, err = command.get_command_output('service glusterd status', False)
        if err:
            raise Exception(err)
        ret_list.append(
            'Distributed storage service (glusterd)  daemon status : %s' % ', '.join(out))
        out, err = command.get_command_output(
            'service glusterfsd status', False)
        if err:
            raise Exception(err)
        ret_list.append(
            'Distributed storage file service (glusterfsd)  status : %s' % ', '.join(out))
        if print_to_stdout:
            print separator.join(ret_list)
    except Exception, e:
        return None, 'Error checking windows access process status: %s' % str(e)
    else:
        return ret_list, None


def get_hosts_entries(print_to_stdout=True, separator='\n'):
    ret_list = []
    try:
        if print_to_stdout:
            ret_list.append('GRIDCell known hosts : ')
        entries, err = dns.get_known_hosts()
        if err:
            raise Exception(err)
        if entries:
            ret_list.append('%-40s %-16s' % ('Hostname', 'IP address'))
            ret_list.append(
                '-----------------------------------------------------------')
            for ip, hn in entries.items():
                ret_list.append('%-40s %-16s' % (hn, ip))
        if print_to_stdout:
            print separator.join(ret_list)
    except Exception, e:
        return None, 'Error checking IntegralView  process status: %s' % str(e)
    else:
        return ret_list, None


def generate_status_file():
    try:
        me = socket.getfqdn()
        with open('/tmp/gridcell_status.html', 'w') as f:
            # with
            # open('/opt/integralstor/integralstor_gridcell/integral_view/static/test.html',
            # 'w') as f:
            f.write('<html>\n')
            f.write('<head>\n')
            f.write('<title>IntegralSTOR GRIDCell status</title>\n')
            f.write(' <link rel="icon" href="/static/images/favicon.ico">\n')
            f.write(
                '<link rel="stylesheet" href="/static/bootstrap/css/bootstrap.css" type="text/css" />\n')
            f.write(
                '<link rel="stylesheet" href="/static/bootstrap/css/bootstrap-responsive.min.css"/>\n')
            f.write(
                '<link rel="stylesheet" type="text/css" href="/static/css/AdminLTE.css">\n')
            f.write(
                '<link rel="stylesheet" type="text/css" href="/static/css/skin-purple.css">\n')
            f.write(
                '<link rel="stylesheet" type="text/css" href="/static/css/fractalio.css">\n')
            f.write('</head>\n')
            f.write('<body style="margin:10px">\n')
            f.write('<h2>GRIDCell hardware status for %s. </h2>\n' % me)
            time = strftime("%c")
            f.write('(Status generated on %s)\n' % (time))
            f.write('<hr>\n')
            f.write('<h4>Hardware status</h4>\n')
            rl, err = check_ipmi(False, '<br/>')
            if rl:
                f.write('<br/>\n'.join(rl))
            f.write('<hr>\n')
            f.write('<h4>Hard drives status</h4>\n')
            rl, err = check_disks_status(False, '<br/>')
            if rl:
                f.write('<br/>\n'.join(rl))
            f.write('<hr>\n')
            f.write('<h2>GRIDCell storage status for %s</h2>\n' % me)
            f.write('<h4>Underlying ZFS storage status on this GRIDCell</h4>\n')
            rl, err = check_zfs_pool_status(False, '<br/>')
            if rl:
                f.write('<br/>\n'.join(rl))
            f.write('<hr>\n')
            f.write('<h4>Windows processes status on this GRIDCell</h4>\n')
            rl, err = check_windows_processes_status(False, '<br/>')
            if rl:
                f.write('<br/>\n'.join(rl))
            f.write('<hr>\n')
            f.write('<h4>Clusterd storage process status on this GRIDCell</h4>\n')
            rl, err = check_gluster_processes_status(False, '<br/>')
            if rl:
                f.write('<br/>\n'.join(rl))
            f.write('<hr>\n')

            f.write('<h2>Overall cluster status</h2>\n')
            f.write('<h4>Network connectivity status of known GRIDCells</h4>\n')
            rl, err = check_network_ping_status(False, '<br/>')
            if rl:
                f.write('<br/>\n'.join(rl))
            f.write('<hr>\n')
            f.write('<h4>Hostname resolution of known GRIDCells</h4>\n')
            rl, err = get_hosts_entries(False, '<br/>')
            if rl:
                f.write('<br/>\n'.join(rl))
            f.write('<hr>\n')
            f.write('<h4>Clustered storage status of known GRIDCells</h4>\n')
            rl, err = check_gluster_peer_status(False, '<br/>')
            if rl:
                f.write('<br/>\n'.join(rl))
            '''
      Commenting out as we wont use CTDB for this release
      f.write( '<hr>\n')
      f.write( '<h4>Clustered Windows access status of known GRIDCells</h4>\n')
      rl, err = check_ctdb_status(False, '<br/>')
      if rl:
        f.write('<br/>\n'.join(rl))
      f.write( '<hr>\n')
      '''

            f.write('<h2>IntegralView status</h2>\n')
            f.write('<h4>Admin agent status of known GRIDCells</h4>\n')
            rl, err = check_salt_status(False, '<br/>')
            if rl:
                f.write('<br/>\n'.join(rl))
            f.write('<hr>\n')
            f.write('<h4>IntegralView processes status of this GRIDCell</h4>\n')
            rl, err = check_integralview_processes_status(False, '<br/>')
            if rl:
                f.write('<br/>\n'.join(rl))
            f.write('<hr>\n')
            f.write('<h4>Admin volume status </h4>\n')
            rl, err = check_admin_vol_started(False, '<br/>')
            if rl:
                f.write('<br/>\n'.join(rl))
            f.write('<hr>\n')
            f.write('<h4>Admin volume mountpoint status </h4>\n')
            rl, err = check_admin_vol_mountpoint(False, '<br/>')
            if rl:
                f.write('<br/>\n'.join(rl))
            f.write('<hr>\n')
            f.write('<h4>Admin volume processes status on all admin GRIDCells</h4>\n')
            rl, err = check_admin_vol_status(False, '<br/>')
            if rl:
                f.write('<br/>\n'.join(rl))
            f.write('<hr>\n')
            f.write('</body>\n')
            f.write('</html>\n')
    except Exception, e:
        return False, 'Error generating status file : %s' % str(e)
    else:
        return True, None


def main():
    err = None
    if len(sys.argv) != 2:
        # Commenting out as we wont use CTDB for this release
        # print 'Usage: python monitoring.py
        # <salt|ping|admin_vol_mountpoint|admin_vol_started|admin_vol_status|zfs|ipmi|disks|windows_processes|ctdb|gluster_peer_status|integralview_processes|gluster_processes|dns|generate_status_file>'
        print 'Usage: python monitoring.py <salt|ping|admin_vol_mountpoint|admin_vol_started|admin_vol_status|zfs|ipmi|disks|windows_processes|gluster_peer_status|integralview_processes|gluster_processes|dns|generate_status_file>'
        sys.exit(0)
    if sys.argv[1] == 'salt':
        ret, err = check_salt_status()
    elif sys.argv[1] == 'ping':
        ret, err = check_network_ping_status()
    elif sys.argv[1] == 'admin_vol_mountpoint':
        ret, err = check_admin_vol_mountpoint()
    elif sys.argv[1] == 'admin_vol_started':
        ret, err = check_admin_vol_started()
    elif sys.argv[1] == 'admin_vol_status':
        ret, err = check_admin_vol_status()
    elif sys.argv[1] == 'zfs':
        ret, err = check_zfs_pool_status()
    elif sys.argv[1] == 'disks':
        ret, err = check_disks_status()
    elif sys.argv[1] == 'windows_processes':
        ret, err = check_windows_processes_status()
    elif sys.argv[1] == 'gluster_peer_status':
        ret, err = check_gluster_peer_status()
    elif sys.argv[1] == 'integralview_processes':
        ret, err = check_integralview_processes_status()
    elif sys.argv[1] == 'gluster_processes':
        ret, err = check_gluster_processes_status()
    elif sys.argv[1] == 'dns':
        ret, err = get_hosts_entries()
    elif sys.argv[1] == 'generate_status_file':
        ret, err = generate_status_file()
    elif sys.argv[1] == 'ipmi':
        ret, err = check_ipmi()
    '''
  Commenting out as we wont use CTDB for this release
  elif sys.argv[1] == 'ctdb':
    ret, err = check_ctdb_status()
  '''
    if err:
        print 'Error processing request : %s' % err
        sys.exit(-1)


if __name__ == '__main__':
    main()

# vim: tabstop=8 softtabstop=0 expandtab ai shiftwidth=4 smarttab
