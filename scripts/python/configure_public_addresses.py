import os
import sys
from integralstor_gridcell import ctdb


def configure_addresses():
    try:
        ack = ''
        while True:
            os.system('clear')
            iface = 'bond0'
            existing_ips, err = ctdb.get_public_addresses()
            if err:
                raise Exception(err)
            print '\n\nIntegralstor GridCell Public Address configuration'
            print '--------------------------------------------------\n'
            print '\t\t%s' % ack
            print '\nActive public addresses:'
            # print existing_ips
            if not existing_ips:
                print '\t- None'
            else:
                for ip in existing_ips:
                    print '\t%s. %s' % (existing_ips.index(ip) + 1, ip)
            print '\n'
            print 'Actions: '
            print '\t1. Add address(es)'
            print '\t2. Remove address(es)'
            print '\t3. Go back to Login Menu'

            action_choice = ''
            while True:
                # while action_choice = raw_input('Enter number corresponding
                # to the desired action: '):
                action_choice = raw_input(
                    'Enter number corresponding to the desired action: ')
                if action_choice in ['1', '2', '3']:
                    break
                else:
                    print '\tValid entires are 1, 2 or 3.'
                    action_choice = ''
            if action_choice == '3':
                break

            is_done = False
            ip_list = []
            while True:
                if action_choice == '1':
                    print '\nTo add, provide the network addresses with prefix(netmask in CIDR format), each address seperated by comma.'
                    print 'Example: 192.168.1.1/24, 192.168.1.2/24'
                    ip_list = raw_input('\t- ').split(',')
                    ip_list = [inner.strip() for inner in ip_list]
                    print 'Entered address(es):'
                    print '\t- ', ip_list
                    confirm = raw_input('Confirm listed address(es) (y/n)? ')
                    if confirm.lower() != 'y':
                        continue
                    else:
                        ret, err = ctdb.mod_public_addresses(
                            ip_list, action='add')
                        if err:
                            ack = 'Could not add the provided addresses: %s' % err
                        if ret is True:
                            ack = 'Addresses added successfully!'.upper()
                        break
                elif action_choice == '2':
                    print '\nTo remove, provide the index numbers(seperated by comma) of the address(es) from the displayed list'
                    choice_list = raw_input('\t- ').split(',')
                    choice_list = [inner.strip() for inner in choice_list]
                    ip_list_t = [inner.strip() for inner in existing_ips]
                    ip_list_t = [inner.split() for inner in ip_list_t]
                    for ip in ip_list_t:
                        if str(ip_list_t.index(ip) + 1) in choice_list:
                            ip_list.append(ip[0])
                    print 'Selected addresses for removal:'
                    print '\t- ', ip_list
                    confirm = raw_input('Confirm listed address(es) (y/n)? ')
                    if confirm.lower() != 'y':
                        continue
                    else:
                        ret, err = ctdb.mod_public_addresses(
                            ip_list, action='remove')
                        if err:
                            ack = 'Could not remove the provided addresses: %s' % err
                        if ret is True:
                            ack = 'Addresses removed successfully!'.upper()
                        break

    except Exception, e:
        print "Couldn't configure public address: %s" % str(e)
        return -1
    else:
        return 0


if __name__ == '__main__':
    rc = configure_addresses()
    sys.exit(rc)

# vim: tabstop=8 softtabstop=0 expandtab ai shiftwidth=4 smarttab
