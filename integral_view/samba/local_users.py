from django.conf import settings

import sys, os, pwd, crypt

'''
sys.path.insert(0, '/opt/fractal/gluster_admin')
sys.path.insert(0, '/home/bkrram/fractal/gluster_admin')
os.environ['DJANGO_SETTINGS_MODULE'] = 'gluster_admin.settings'
'''
path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '%s/../..'%path)
os.environ['DJANGO_SETTINGS_MODULE']='integral_view.settings'

from integral_view.utils import command

def create_local_user(userid, name, pswd):

  #First check if samba user exists. if so kick out
  ul = get_samba_users()
  if userid in ul:
    raise Exception("Error creating user. The user \"%s\" already exists. "%userid)

  # Now check if system user exists. If not create..
  create_system_user = False
  try:
    pwd.getpwnam(userid)
  except KeyError:
    create_system_user = True

  if create_system_user:
    enc_pswd = crypt.crypt(pswd, "28")
    ret, rc = command.execute_with_rc(r'useradd -p %s -c fractal_user_%s %s'%(enc_pswd, name, userid))
    if rc != 0:
      raise Exception("Error creating system user. Return code : %d. "%rc)

  # Now all set to create samba user
  ret, rc = command.execute_with_conf_and_rc(r'/usr/local/samba/bin/pdbedit  -d 1 -t -a  -u %s -f %s'%(userid, name), "%s\n%s"%(pswd, pswd))
  if rc != 0:
    #print command.get_error_list(ret)
    raise Exception("Error creating user. Return code : %d. "%rc)
  ul = command.get_output_list(ret)
  print ul


def delete_local_user(userid):

  #First check if samba user exists. if so kick out
  ul = get_samba_users()
  if userid not in ul:
    raise Exception("Error deleting user. The user \"%s\" does not exist. "%userid)

  # Now check if system user exists. If so and is created by fractal then delete..
  delete_system_user = False
  try:
    d = pwd.getpwnam(userid)
    name = d[4]
    if name.find("fractal_user") == 0:
      delete_system_user = True
  except KeyError:
    pass

  if delete_system_user:
    print "Deleting user %s from the system"%userid
    ret, rc = command.execute_with_rc(r'userdel %s'%userid)
    if rc != 0:
      raise Exception("Error deleting user from the underlying system. Return code : %d. "%rc)
    print "Deleted user %s from the system"%userid

  print "Deleting user %s from the storage system"%userid
  ret, rc = command.execute_with_rc(r'/usr/local/samba/bin/pdbedit -d 1 -x %s'%userid)
  if rc != 0:
    raise Exception("Error deleting user from the storage system. Return code : %d. "%rc)
  print "Deleted user %s from the storage system"%userid


def get_samba_users():
  ret, rc = command.execute_with_rc(r'/usr/local/samba/bin/pdbedit  -d 1 -L ')
  if rc != 0:
    print ret
    #print command.get_error_list(ret)
    raise Exception("Error reading current users. Return code : %d. "%rc)
  l = command.get_output_list(ret)
  ul = []
  for u in l:
    user = u.split(':')[0]
    ul.append(user)
  return ul

def change_password(userid, pswd):
  ret, rc = command.execute_with_conf_and_rc(r'smbpasswd -s %s'%(userid), "%s\n%s"%(pswd, pswd))
  if rc != 0:
    print ret
    #print command.get_error_list(ret)
    raise Exception("Error changing password. Return code : %d. "%rc)
  ul = command.get_output_list(ret)
  print ul

def get_local_users():

  ret, rc = command.execute_with_rc("/usr/local/samba/bin/pdbedit -d 1 -L")

  if rc != 0:
    raise "Error retrieving user list. Return code : %d"%rc

  ul = command.get_output_list(ret)
  user_list = []
  for u in ul:
    l = u.split(':')
    if l:
      d = {}
      d["userid"] = l[0]
      if len(l) > 1:
        d["name"] = l[2]
      user_list.append(d)
  return user_list

def main():
  #change_password("bkrram", "ram1")
  delete_local_user("ram2")
  print get_samba_users()

if __name__ == "__main__":
  main()
