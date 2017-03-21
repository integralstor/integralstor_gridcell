import os
import socket
import re
import sys
import shutil
from integralstor_common import networking, command, common
import salt.client


def configure_minion():

    try:
        os.system('clear')
        minion_opts = salt.config.minion_config('/etc/salt/minion')
        masters = []
        if minion_opts and 'master' in minion_opts:
            masters = minion_opts['master']

        masters_list = []
        if type(masters) is not list:
            masters_list.append(masters)
        else:
            masters_list = masters

        print '\n\n\nBootstrap admin agent\n'
        print '----------------------\n\n\n'
        config_changed = False
        str_to_print = 'Enter the IP address of the initial Admin GRIDCell : '

        valid_input = False
        ip = None
        while not valid_input:
            input = raw_input(str_to_print)
            if input:
                vi, err = networking.validate_ip(input.strip())
                if err:
                    raise Exception(err)
                if vi:
                    ip = input.strip()
                    valid_input = True
                else:
                    print "Invalid value. Please try again."
            else:
                print "Invalid value. Please try again."
            print

        print "Final confirmation"
        print "------------------"

        print
        print "You have entered : %s" % input
        print

        str_to_print = 'Commit the above changes? (y/n) :'

        commit = 'n'
        valid_input = False
        while not valid_input:
            input = raw_input(str_to_print)
            if input:
                if input.lower() in ['y', 'n']:
                    valid_input = True
                    commit = input.lower()
            if not valid_input:
                print "Invalid value. Please try again."
        print

        if commit == 'y':
            print "Committing changes!"
        else:
            print "Discarding changes!"

        if commit == 'y':
            platform_root, err = common.get_platform_root()
            if err:
                raise Exception(err)

            f1 = open('%s/defaults/salt/minion_part_1' % platform_root, 'r')
            f2 = open('%s/defaults/salt/minion_part_2' % platform_root, 'r')
            with open('/tmp/minion', 'w') as fw:
                fw.write(f1.read())
                fw.write('master: %s\n' % ip)
                fw.write('\n')
                fw.write(f2.read())
            f2.close()
            f1.close()
            shutil.move('/tmp/minion', '/etc/salt/minion')
            print
            print 'Restarting admin agent service'
            (r, rc), err = command.execute_with_rc(
                'service salt-minion restart')
            if err:
                raise Exception(err)
            if rc == 0:
                print "Admin agent (salt minion) service restarted succesfully."
            else:
                raise Exception(
                    "Error restarting admin agent (salt minion) services.")

    except Exception, e:
        print "Error configuring network settings : %s" % e
        return -1
    else:
        return 0


if __name__ == '__main__':

    rc = configure_minion()
    sys.exit(rc)


# vim: tabstop=8 softtabstop=0 expandtab ai shiftwidth=4 smarttab
