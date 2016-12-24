
import sys
from integralstor_common import common, command

def heal_info(vol_name):
  try:
    ret, err = command.get_command_output('gluster volume heal %s info split-brain'%vol_name)
    if err:
      raise Exception(err)
    if ret:
      print '\n'.join(ret)
  except Exception, e:
    return False, 'Error getting heal info : %s'%e
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
    print
    str_to_print = 'Enter the number of the desired healing criteria :'
    method = ''
    valid_input = False
    while not valid_input:
      admin_server_list = []
      input = raw_input(str_to_print)
      try:
        selection = int(input)
        if selection not in [1,2]:
          raise Exception('Wrong input')
      except Exception, e:
        print 'Invalid input. Please try again.'
        continue
      if selection == 1:
        method = 'latest-mtime'
      elif selection == 2:
        method = 'bigger-file' 
      valid_input = True
    if method:
      #print method
      cmd = 'gluster volume heal %s split-brain %s %s'%(vol_name, method, file_name)
      print cmd

      ret, err = command.get_command_output(cmd)
      #print 'a', ret, err
      if err:
        raise Exception(err)
      if ret:
        print '\n'.join(ret)
  except Exception, e:
    return False, 'Error healing volume : %s'%e
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
