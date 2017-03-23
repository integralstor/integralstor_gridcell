
import sys
from integralstor_utils import config, command, lock
from integralstor_gridcell import gluster_volumes

import atexit
atexit.register(lock.release_lock, 'gluster_commands')


def volume_start_stop(vol_name, operation):
    try:
        cmd = 'gluster volume %s %s' % (operation, vol_name)
        print cmd

        if operation == 'stop':
            (ret, rc), err = command.execute_with_conf_and_rc(cmd)
            if rc == 0:
                lines, er = command.get_output_list(ret)
                if er:
                    raise Exception(er)
            else:
                err = ''
                tl, er = command.get_output_list(ret)
                if er:
                    raise Exception(er)
                if tl:
                    err = ''.join(tl)
                tl, er = command.get_error_list(ret)
                if er:
                    raise Exception(er)
                if tl:
                    err = err + ''.join(tl)
                raise Exception(err)
        else:
            lines, err = command.get_command_output(cmd)
            # print 'a', ret, err
            if err:
                raise Exception(err)
        if lines:
            print '\n'.join(lines)
    except Exception, e:
        return False, 'Error performing volume %s : %s' % (operation, e)
    else:
        return True, None


def main():
    try:
        if len(sys.argv) < 2:
            print 'Usage : python gluster_volume_start_stop.py [start|stop|restart_all] <vol_name>'
            sys.exit(0)
        if sys.argv[1] not in ['start', 'stop', 'restart_all']:
            print 'Usage : python gluster_volume_start_stop.py [start|stop|restart_all] <vol_name>'
            sys.exit(0)
        if sys.argv[1] in ['start', 'stop'] and (len(sys.argv) != 3):
            print 'Usage : python gluster_volume_start_stop.py [start|stop|restart_all] <vol_name>'
            sys.exit(0)

        gluster_lck, err = lock.get_lock('gluster_commands')
        if err:
            raise Exception(err)

        if sys.argv[1] == 'restart_all':
            ret, err = gluster_volumes.restart_all_volumes()
            if err:
                raise Exception(err)
            sys.exit(0)
        else:
            vol_name = sys.argv[2]
            ret, err = volume_start_stop(vol_name, sys.argv[1])
            if err:
                raise Exception(err)
    except Exception, e:
        print e
        sys.exit(-1)
    else:
        sys.exit(0)
    finally:
        lock.release_lock('gluster_commands')


if __name__ == '__main__':
    main()

# vim: tabstop=8 softtabstop=0 expandtab ai shiftwidth=4 smarttab
