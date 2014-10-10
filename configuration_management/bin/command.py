import os
import subprocess



def execute(command = None):
  """ Given a command specified in the parameter, it spawns a subprocess to execute it and returns the output" and errors"""

  output, err = '', ''
  ret = ('', '')


  if not command:
    return None

  comm_list = command.split()
    
  try:
    proc = subprocess.Popen(comm_list, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    ret = proc.communicate()

  except Exception as ex:
    ret[1] = str(ex)

  return ret

def execute_with_conf(command = None):
  """ Given a command specified in the parameter, it spawns a subprocess to execute it and returns the output" and errors.
  The difference between this and execute() is that is used for commands that require a y/n confirmation."""

  output, err = '', ''
  ret = ('', '')

  if not command:
    return None

  comm_list = command.split()
    
  try:
    proc = subprocess.Popen(comm_list, stdin=subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    proc.stdin.write('y\n')
    ret = proc.communicate()

  except Exception as ex:
    ret[1] = str(ex)

  return ret

def get_command_output(command):
  """ A wrapper around execute to return the output of a command only if there is no error."""

  #print 'Executing : '+command
  t1 = execute(command)

  el = get_error_list(t1)
  if el:
    print 'Errors' 
    for i in el:
      print i
    return None

  print 'Output' 
  ol = get_output_list(t1)
  return ol


def get_error_list(tup):
  """ Given the tuple returned by execute(), it returns the error list"""
  err_list = []
  if tup and tup[1]:
    for line in tup[1].splitlines():
      err_list.append(line)
  return err_list

def get_conf_error_list(tup):
  """ Given the tuple returned by execute_with_conf(), it returns the error list. 
  Requires a kudge because we need to ignore the first line which may be the prompt from the command"""

  err_list = []
  # kludge!!
  first_line = True
  if tup and tup[1]:
    for line in tup[1].splitlines():
      if not first_line:
        err_list.append(line)
      first_line = False
  return err_list

def get_output_list(tup):
  """ Given the tuple returned by execute(), it returns the output list"""
  output_list = []
  if tup and tup[0]:
    for line in tup[0].splitlines():
      output_list.append(line)
  return output_list


def get_conf_output_list(tup):
  """ Given the tuple returned by execute_with_conf(), it returns the output list. 
  Requires a kudge because we need to ignore the first line which may be the prompt from the command"""
  output_list = []
  first_line = True
  if tup and tup[0]:
    for line in tup[0].splitlines():
        if first_line:
          index = line.find(r'(y/n)')
          output_list.append(line[index+5:])
          #output_list.append(line)
          first_line = False
        else:
          output_list.append(line)
  return output_list



def main():
  #c = 'python a.py'
  c = 'ipmitool raw 0x30 0x7d'	
  print 'Executing : '+c
  t1 = execute_with_conf(c)

  el = get_error_list(t1)
  if el:
    print 'Errors' 
    for i in el:
      print i

  print 'Output' 
  ol = get_output_list(t1)
  if ol:
    for i in ol:
      print i

if __name__ == "__main__":
  main()

    
