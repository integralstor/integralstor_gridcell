
from integralstor_utils import networking, command
import os
import socket
import sys


def display_config():

    try:
        hostname = socket.gethostname()
        if hostname:
            print "Hostname : %s" % hostname
        else:
            print "Hostname : Not set"
        ip_info, err = networking.get_ip_info('bond0')
        if err:
            print 'Error retrieving IP address information : %s' % err
        if ip_info:
            if "ipaddr" in ip_info:
                print "IP Address : %s" % ip_info["ipaddr"]
            else:
                print "IP Address : None"
            if "netmask" in ip_info:
                print "Net mask: %s" % ip_info["netmask"]
            else:
                print "Net mask : None"
            if "default_gateway" in ip_info:
                print "Default gateway: %s" % ip_info["default_gateway"]
            else:
                print "Default gateway : None"
        dns_list, err = networking.get_name_servers()
        if err:
            'Error retrieving name servers : %s' % err
        if dns_list:
            print "DNS lookup servers :",
            print ','.join(dns_list)
        bonding_type, err = networking.get_bonding_type('bond0')
        if err:
            print 'Error retrieving bonding type : %s' % err
        if bonding_type:
            print "NIC Bonding mode : %d" % bonding_type
        jfe, err = networking.is_enabled_jumbo_frames('bond0')
        if err:
            print 'Error retrieving jumbo frames setting'
        else:
            if jfe:
                print "Jumbo frames : enabled"
            else:
                print "Jumbo frames : Not enabled"
    except Exception, e:
        print "Error displaying system configuration : %s" % e
        return -1
    else:
        return 0


if __name__ == '__main__':

    os.system('clear')
    print
    print
    print
    print
    print "GRIDCell Configuration"
    print "----------------------"
    rc = display_config()
    print
    print
    sys.exit(rc)


# vim: tabstop=8 softtabstop=0 expandtab ai shiftwidth=4 smarttab
