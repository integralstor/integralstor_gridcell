import os, sys

def get_lock(name):

  pid = str(os.getpid())
  pidfile = '/tmp/fractalio_%s_lock.pid'%name
  if os.path.isfile(pidfile):
    return False
  else:
    file(pidfile, 'w').write(pid)
  return True

def release_lock(name):
  pidfile = '/tmp/fractalio_%s_lock.pid'%name
  try:
    os.unlink(pidfile)
  except Exception, e:
    pass
  return 0
