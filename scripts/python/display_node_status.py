
from integralstor_common import networking, command
import os
import socket
import sys


def display_status():

    try:
        hostname = socket.gethostname()
        status, err = command.get_command_output('service salt-master status')
        if err:
            raise Exception(err)
        print '\n'.join(status)
        status, err = command.get_command_output('service salt-minion status')
        if err:
            raise Exception(err)
        print '\n'.join(status)
        status, err = command.get_command_output('service smb status')
        if err:
            raise Exception(err)
        print '\n'.join(status)
        status, err = command.get_command_output('service winbind status')
        if err:
            raise Exception(err)
        print '\n'.join(status)
        '''
    #Commenting out as we wont support CTDB for this release
    status, err = command.get_command_output('service ctdb status')
    if err:
      raise Exception(err)
    print '\n'.join(status)
    '''
        status, err = command.get_command_output('service glusterd status')
        if err:
            raise Exception(err)
        print '\n'.join(status)
        '''
    #Commenting out as we wont support CTDB for this release
    status, err = command.get_command_output('ctdb status')
    if err:
      raise Exception(err)
    print '\n'.join(status)
    '''
    except Exception, e:
        return False,  "Error displaying GRIDCell status : %s" % e
    else:
        return True, None


if __name__ == '__main__':

    os.system('clear')
    print
    print
    print
    print "GRIDCell status"
    print "---------------"
    rc, err = display_status()
    if err:
        print err
    print
    print
    # sys.exit(rc)


# vim: tabstop=8 softtabstop=0 expandtab ai shiftwidth=4 smarttab
