
from integralstor_common import networking, command
import os, socket, sys


def display_status():

  try :
    hostname = socket.gethostname()
    if hostname and hostname in ['fractalio-pri', 'fractalio-sec']:
      print "DNS service status :"
      (r, rc), err = command.execute_with_rc('service named status')
      if err:
        raise Exception(err)
      l, err = command.get_output_list(r)
      if err:
        raise Exception(err)
      if l:
        print '\n'.join(l)
      else:
        l, err = command.get_error_list(r)
        if err:
          raise Exception(err)
        if l:
          print '\n'.join(l)
      print "Salt master service status :"
      (r, rc), err = command.execute_with_rc('service salt-master status')
      if err:
        raise Exception(err)
      l, err = command.get_output_list(r)
      if err:
        raise Exception(err)
      if l:
        print '\n'.join(l)
      else:
        l, err = command.get_error_list(r)
        if err:
          raise Exception(err)
        if l:
          print '\n'.join(l)
    print "Salt minion service status :",
    (r, rc), err = command.execute_with_rc('service salt-minion status')
    if err:
      raise Exception(err)
    l, err = command.get_output_list(r)
    if err:
      raise Exception(err)
    if l:
      print '\n'.join(l)
    else:
      l, err = command.get_error_list(r)
      if err:
        raise Exception(err)
      print l
      if l:
        print '\n'.join(l)
    print "Samba service status :",
    (r, rc), err = command.execute_with_rc('service smb status')
    if err:
      raise Exception(err)
    l, err = command.get_output_list(r)
    if err:
      raise Exception(err)
    if l:
      print '\n'.join(l)
    else:
      l, err = command.get_error_list(r)
      if err:
        raise Exception(err)
      if l:
        print '\n'.join(l)
    print "Winbind service status :",
    (r, rc), err = command.execute_with_rc('service winbind status')
    if err:
      raise Exception(err)
    l, err = command.get_output_list(r)
    if err:
      raise Exception(err)
    if l:
      print '\n'.join(l)
    else:
      l, err = command.get_error_list(r)
      if err:
        raise Exception(err)
      if l:
        print '\n'.join(l)
    print "CTDB service status :",
    (r, rc), err = command.execute_with_rc('service ctdb status')
    if err:
      raise Exception(err)
    l, err = command.get_output_list(r)
    if err:
      raise Exception(err)
    if l:
      print '\n'.join(l)
    else:
      l, err = command.get_error_list(r)
      if err:
        raise Exception(err)
      if l:
        print '\n'.join(l)
    print "Gluster service status :",
    (r, rc), err = command.execute_with_rc('service glusterd status')
    if err:
      raise Exception(err)
    l, err = command.get_output_list(r)
    if err:
      raise Exception(err)
    if l:
      print '\n'.join(l)
    else:
      l, err = command.get_error_list(r)
      if err:
        raise Exception(err)
      if l:
        print '\n'.join(l)
    print
    print "GRIDCell CTDB status :"
    (r, rc), err = command.execute_with_rc('ctdb status')
    if err:
      raise Exception(err)
    l, err = command.get_output_list(r)
    if err:
      raise Exception(err)
    if l:
      print '\n'.join(l)
    else:
      l, err = command.get_error_list(r)
      if err:
        raise Exception(err)
      if l:
        print '\n'.join(l)
  except Exception, e:
    return False,  "Error displaying GRIDCell status : %s"%e
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
  #sys.exit(rc)

