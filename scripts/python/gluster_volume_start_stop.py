
import sys
from integralstor_common import common, command

def volume_start_stop(vol_name, operation):
  try:
    cmd = 'gluster volume %s %s'%(operation, vol_name)
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
      #print 'a', ret, err
      if err:
        raise Exception(err)
    if lines:
      print '\n'.join(lines)
  except Exception, e:
    return False, 'Error performing volume %s : %s'%(operation, e)
  else:
    return True, None

def main():
  try:
    if len(sys.argv) != 3:
      print 'Usage : python gluster_volume_start_stop.py <vol_name> [start|stop]'
      sys.exit(0)
    vol_name = sys.argv[1]
    ret, err = volume_start_stop(vol_name, sys.argv[2])
    if err:
      raise Exception(err)
  except Exception, e:
    print e
    sys.exit(-1)
  else:
    sys.exit(0)

if __name__ == '__main__':
  main()
