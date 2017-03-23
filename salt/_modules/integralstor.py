import pprint
import shutil
import os
import time

from integralstor_utils import manifest_status, config, networking


def disk_info_and_status():

    disks, err = manifest_status.disk_info_and_status()
    return disks


def pool_status():
    pools, err = manifest_status.pool_status()
    return pools


def interface_status():
    int_status, err = manifest_status.interface_status()
    return int_status


def load_avg():
    lavg, err = manifest_status.load_avg()
    return lavg


def mem_info():
    meminfo, err = manifest_status.mem_info()
    return meminfo


def ipmi_status():
    ipmi, err = manifest_status.ipmi_status()
    return ipmi


def status():
    sd, err = manifest_status.status()
    return sd


def configure_minion(*masters):
    try:
        if not masters:
            raise Exception('No masters specified')
        if len(masters) > len(set(masters)):
            raise Exception('Duplicate masters specified')

        platform_root, err = config.get_platform_root()
        if err:
            raise Exception(err)

        f1 = open('%s/defaults/salt/minion_part_1' % platform_root, 'r')
        f2 = open('%s/defaults/salt/minion_part_2' % platform_root, 'r')

        with open('/tmp/minion', 'w') as fw:
            fw.write(f1.read())
            if len(masters) > 1:
                fw.write('master:\n')
                for master in masters:
                    fw.write('  - %s\n' % master)
            else:
                fw.write('master: %s\n' % masters[0])
            fw.write('\n')
            fw.write(f2.read())
        f2.close()
        f1.close()
        shutil.move('/tmp/minion', '/etc/salt/minion')

        # Record the new masters so that they can be used by other scripts like
        # rc.local
        with open('%s/admin_gridcells' % platform_root, 'w') as f:
            for master in masters:
                f.write('%s\n' % master)

        # Flag the node as being a part of the salt grid..
        with open('%s/part_of_grid' % platform_root, 'w') as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S"))

    except Exception, e:
        return False, str(e)
    else:
        return True, None


def configure_ntp_slave(*masters):
    try:
        if not masters:
            raise Exception('No NTP masters specified')

        with open('/tmp/new_ntp_slave.conf', 'w') as f:
            f.write('server  127.127.1.0     # local clock\n')
            f.write('fudge   127.127.1.0 stratum 10\n\n')
            for master in masters:
                f.write('server %s\n' % master)

            f.write('\ndriftfile /etc/ntp/drift\n\n')

            f.write('multicastclient\n')
            f.write('broadcastdelay  0.008\n\n')

            f.write(
                '# Dont serve time or stats to anyone else by default (more secure)\n')
            f.write('restrict default noquery nomodify\n')

            for master in masters:
                f.write(
                    'restrict %s mask 255.255.255.255 nomodify notrap noquery\n' % master)

            f.write('restrict 127.0.0.1\n')
        shutil.move('/tmp/new_ntp_slave.conf', '/etc/ntp.conf')
    except Exception, e:
        return False, str(e)
    else:
        return True, None


def disk_action(**kwargs):
    ret = False
    try:
        if 'action' not in kwargs or kwargs['action'] not in ['disk_blink', 'disk_unblink']:
            raise Exception('Invalid disk action')

        our_hw_platform, err = config.get_hardware_platform()
        if err:
            raise Exception(err)
        if our_hw_platform == 'dell':
            if 'controller' not in kwargs or 'target_id' not in kwargs or 'channel' not in kwargs or 'enclosure_id' not in kwargs:
                raise Exception(
                    'Insufficient information received for the specified action')
            from integralstor_utils.platforms import dell
            err = None
            if kwargs['action'] == 'disk_blink':
                ret, err = dell.blink_unblink_disk(
                    'blink', kwargs['controller'], kwargs['channel'], kwargs['enclosure_id'], kwargs['target_id'])
            elif kwargs['action'] == 'disk_unblink':
                ret, err = dell.blink_unblink_disk(
                    'unblink', kwargs['controller'], kwargs['channel'], kwargs['enclosure_id'], kwargs['target_id'])
            if err:
                raise Exception(err)
        else:
            raise Exception(
                'Unsupported hardware platform for the specified action')
    except Exception, e:
        return ret, str(e)
    else:
        return ret, None


def configure_ntp_master(*external_masters, **kwargs):
    try:
        if 'network' not in kwargs.keys():
            raise Exception('No network specified')
        if 'netmask' not in kwargs.keys():
            raise Exception('No netmask specified')

        with open('/tmp/new_ntp_master.conf', 'w') as f:
            f.write('server  127.127.1.0     # local clock\n')
            f.write('fudge   127.127.1.0 stratum 10\n\n')

            if external_masters:
                for master in external_masters:
                    f.write('server %s\n' % master)

            f.write('\n# Logging & Stats\n')
            f.write('statistics loopstats\n')
            f.write('statsdir /var/log/ntp/\n')
            f.write('filegen peerstats file peers type day link enable\n')
            f.write('filegen loopstats file loops type day link enable\n\n')

            f.write('\ndriftfile /etc/ntp/drift\n\n')
            f.write('broadcastdelay  0.008\n\n')

            f.write(
                '# Dont serve time or stats to anyone else by default (more secure)\n')
            f.write('restrict default noquery nomodify\n')

            if external_masters:
                for master in external_masters:
                    f.write(
                        'restrict %s mask 255.255.255.255 nomodify notrap noquery\n' % master)

            f.write('\n# Allow LAN to query us\n')
            f.write('restrict %s mask %s nomodify notrap\n' %
                    (kwargs['network'], kwargs['netmask']))

            f.write('restrict 127.0.0.1\n')
        shutil.move('/tmp/new_ntp_master.conf', '/etc/ntp.conf')
    except Exception, e:
        return False, str(e)
    else:
        return True, None


def flag_as_admin_gridcell():
    try:
        with open('/etc/salt/grains', 'w') as f:
            f.write('# Generated by the IntegralStor script\n')
            f.write('roles:\n')
            #f.write('  - primary\n')
            f.write('  - master\n')
            f.flush()
        f.close()
    except Exception, e:
        return False, 'Error flagging admin GRIDCell : %s' % str(e)
    else:
        return True, None


def configure_name_servers(*ns_list):
    try:
        if not ns_list:
            raise Exception('No name servers specified')
        ret, err = networking.set_name_servers(ns_list)
        if err:
            raise Exception(err)
    except Exception, e:
        return False, 'Error setting name servers : %s' % str(e)
    else:
        return True, None


if __name__ == '__main__':
    pass
    # print configure_ntp_slave('a.b.c.d', 'e.f.g.h')
    # print configure_ntp_master('0.ntp.org', '1.ntp.org', network='192.168.1.0', netmask='255.255.255.0')
    # print status()
    # print status()
    # print _diskmap()
    #pp = pprint.PrettyPrinter(indent=4)
    # pp.pprint(disk_info_and_status())
    #d = pool_status()
    # pp.pprint(d)
    # pp.pprint(d)
    # print disk_status()
    # pp.pprint(interface_status())
    # print status()
    # print load_avg()
    # print disk_usage()
    # print mem_info()

# vim: tabstop=8 softtabstop=0 expandtab ai shiftwidth=4 smarttab
