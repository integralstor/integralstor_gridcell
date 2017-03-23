
import sys
from integralstor_utils import command


def heal_info(vol_name):
    try:
        ret, err = command.get_command_output(
            'gluster volume heal %s info split-brain' % vol_name)
        if err:
            raise Exception(err)
        if ret:
            print '\n'.join(ret)
    except Exception, e:
        return False, 'Error getting heal info : %s' % e
    else:
        return True, None


def heal(vol_name):
    try:
        valid_input = False
        str_to_print = 'Enter the name of the file to heal (with full volume path) : '
        print
        while not valid_input:
            file_name = raw_input(str_to_print)
            if file_name.strip():
                valid_input = True

        print
        print 'Available healing criteria :'
        print '1. Latest modified time'
        print '2. Largest file'
        print '3. Source brick'
        print
        str_to_print = 'Enter the number of the desired healing criteria :'
        method = ''
        valid_input = False
        while not valid_input:
            admin_server_list = []
            input = raw_input(str_to_print)
            try:
                selection = int(input)
                if selection not in [1, 2, 3]:
                    raise Exception('Wrong input')
            except Exception, e:
                print 'Invalid input. Please try again.'
                continue
            if selection == 1:
                method = 'latest-mtime'
            elif selection == 2:
                method = 'bigger-file'
            elif selection == 3:
                method = 'source-brick'
            valid_input = True
        if method:
            brick = None
            # print method
            if method == 'source-brick':
                valid_input = False
                while not valid_input:
                    brick = raw_input(
                        'Enter source brick in <HOSTNAME:BRICKNAME> format : ')
                    if brick:
                        components = brick.split(':')
                        if len(components) == 2:
                            valid_input = True
                            break
                    print 'Invalid brick. Please try again.\n'
                cmd = 'gluster volume heal %s split-brain source-brick %s %s' % (
                    vol_name, brick, file_name)
            else:
                cmd = 'gluster volume heal %s split-brain %s %s' % (
                    vol_name, method, file_name)
                print cmd

            ret, err = command.get_command_output(cmd)
            # print 'a', ret, err
            if err:
                raise Exception(err)
            if ret:
                print '\n'.join(ret)
    except Exception, e:
        return False, 'Error healing volume : %s' % e
    else:
        return True, None


def main():
    try:
        if len(sys.argv) != 3:
            print 'Usage : python self_heal.py <vol_name> [info|heal]'
            sys.exit(0)
        vol_name = sys.argv[1]
        if sys.argv[2] == 'info':
            ret, err = heal_info(vol_name)
            if err:
                raise Exception(err)
        elif sys.argv[2] == 'heal':
            ret, err = heal(vol_name)
            if err:
                raise Exception(err)
    except Exception, e:
        print e
        sys.exit(-1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()

# vim: tabstop=8 softtabstop=0 expandtab ai shiftwidth=4 smarttab
