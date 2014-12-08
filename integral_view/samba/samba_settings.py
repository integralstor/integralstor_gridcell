
import json,sqlite3

from integral_view.utils import command, db
import local_users

from django.conf import settings

def change_auth_method(security):

  cl = []
  cl.append(["update samba_global_common set security='%s' where id=1"%security])
  cl.append(["delete from samba_valid_users"])
  db.execute_iud(cl)

def load_auth_settings():
  d = None
  conn = None
  try :
    d = db.read_single_row("select * from samba_global_common where id=1")
    if d and d["security"] == "ads":
      d1 = db.read_single_row("select * from samba_global_ad where id=1")
      if d1:
        d.update(d1)
  finally:
    return d

def save_auth_settings(d):

  cmd_list = []
  cmd = ["update samba_global_common set workgroup=?, netbios_name=?, security=?, include_homes_section=? where id = ?", (d["workgroup"], d["netbios_name"], d["security"], True, 1,)]
  cmd_list.append(cmd)
  if d["security"] == "ads":
    d1 = db.read_single_row("select * from samba_global_ad")
    if d1:
      cmd = ["update samba_global_ad set realm=?, password_server=?, ad_schema_mode=?, id_map_min=?, id_map_max=?,  where id = ?", (d["realm"], d["password_server"], d["ad_schema_mode"], d["id_map_min"], d["id_map_max"], 1,)]
      cmd_list.append(cmd)
    else:
      print "in 2"
      cmd = ["insert into samba_global_ad (realm, password_server, ad_schema_mode, id_map_min, id_map_max, id) values(?,?,?,?,?,?)", (d["realm"], d["password_server"], d["ad_schema_mode"], d["id_map_min"], d["id_map_max"], 1,)]
      cmd_list.append(cmd)
  #print "updating "
  db.execute_iud(cmd_list)
  #print "updated "

def delete_auth_settings():
  conn = None
  try :
    conn = sqlite3.connect("%s/integral_view_config.db"%settings.DB_LOCATION)
    cur = conn.cursor()
    cur.execute("delete from samba_auth ")
    cur.close()
    conn.commit()
  finally:
    if conn:
      conn.close()

def load_shares_list():
  l = []
  conn = None
  try :
    conn = sqlite3.connect("%s/integral_view_config.db"%settings.DB_LOCATION)
    #conn = sqlite3.connect("/home/bkrram/Documents/software/Django-1.4.3/code/gluster_admin/gluster_admin/devel/db/integral_view_config.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("select * from samba_shares")
    rows = cur.fetchall()
    if not rows:
      return None
    for row in rows:
      d = {}
      for key in row.keys():
        d[key] = row[key]
      l.append(d)
    return l
  finally:
    if conn:
      conn.close()

def load_share_info(mode, index):
  d = None
  conn = None
  try :
    conn = sqlite3.connect("%s/integral_view_config.db"%settings.DB_LOCATION)
    #conn = sqlite3.connect("/home/bkrram/Documents/software/Django-1.4.3/code/gluster_admin/gluster_admin/devel/db/integral_view_config.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if mode == "by_id":
      cur.execute("select * from samba_shares where share_id = %s"%index)
    else:
      cur.execute("select * from samba_shares where name = %s"%index)
    r = cur.fetchone()
    if not r:
      return None
    d = {}
    for key in r.keys():
      d[key] = r[key]
    return d
  finally:
    if conn:
      conn.close()






def delete_share(share_id):

  conn = None
  try :
    conn = sqlite3.connect("%s/integral_view_config.db"%settings.DB_LOCATION)
    #conn = sqlite3.connect("/home/bkrram/Documents/software/Django-1.4.3/code/gluster_admin/gluster_admin/devel/db/integral_view_config.db")
    cur = conn.cursor()
    cur.execute("delete from samba_shares where share_id=?", (share_id, ))
    cur.execute("delete from samba_valid_users where share_id=?", (share_id, ))
    cur.close()
    conn.commit()
  finally:
    if conn:
      conn.close()

def delete_all_shares():
  conn = None
  try :
    conn = sqlite3.connect("%s/integral_view_config.db"%settings.DB_LOCATION)
    #conn = sqlite3.connect("/home/bkrram/Documents/software/Django-1.4.3/code/gluster_admin/gluster_admin/devel/db/integral_view_config.db")
    cur = conn.cursor()
    cur.execute("delete from samba_shares ")
    cur.execute("delete from samba_valid_users ")
    cur.close()
    conn.commit()
  finally:
    if conn:
      conn.close()



def save_share(share_id, name, comment, guest_ok, read_only, path, browseable, users, groups, vol):

  conn = None
  try :
    conn = sqlite3.connect("%s/integral_view_config.db"%settings.DB_LOCATION)
    cur = conn.cursor()
    cur.execute("update samba_shares set comment=?, read_only=?, guest_ok=?, browseable=? where share_id=?", (comment, read_only, guest_ok, browseable,share_id, ))
    cur.execute("delete from samba_valid_users where share_id=?", (share_id, ))
    
    if not guest_ok:
      if users:
        for user in users:
          cur.execute("insert into samba_valid_users (id, share_id, grp, name) values (NULL,?,?,?)", (share_id, False, user,))
      if groups:
        for group in groups:
          cur.execute("insert into samba_valid_users (id, share_id, grp, name) values (NULL,?,?,?)", (share_id, True, group,))
    cur.close()
    conn.commit()
  finally:
    if conn:
      conn.close()


def create_share(name, comment, guest_ok, read_only, path, display_path, browseable, users, groups, vol):

  d = load_auth_settings()
  if not d:
    raise Exception("Authentication settings not set. Please set authentication settings before creating shares.")
  shl = load_shares_list()
  if shl:
    for sh in shl:
      if sh["name"] == name :
        raise Exception("A share with that name already exists")

  conn = None
  try :
    conn = sqlite3.connect("%s/integral_view_config.db"%settings.DB_LOCATION)
    #conn = sqlite3.connect("/home/bkrram/Documents/software/Django-1.4.3/code/gluster_admin/gluster_admin/devel/db/integral_view_config.db")
    cur = conn.cursor()
    cur.execute("insert into samba_shares (name, vol, path, display_path, comment, read_only, guest_ok, browseable, share_id) values (?,?, ?,?,?,?,?,?,NULL)", (name, vol, path, display_path, comment, read_only, guest_ok, browseable,))
    share_id = cur.lastrowid
    if not guest_ok:
      if users:
        for user in users:
          cur.execute("insert into samba_valid_users (id, share_id, grp, name) values (NULL,?,?,?)", (share_id, False, user,))
      if groups:
        for group in groups:
          cur.execute("insert into samba_valid_users (id, share_id, grp, name) values (NULL,?,?,?)", (share_id, True, group,))
    cur.close()
    conn.commit()
  finally:
    if conn:
      conn.close()


def _generate_global_section(f, d):
  f.write("; This file has been programatically generated by the fractal view system. Do not modify it manually!\n\n")
  f.write("[global]\n")
  f.write("  server string = Fractal-io File server\n")
  f.write("  log file = /var/log/smblog.vfs\n")
  f.write("  log level=5\n")
  f.write("  load printers = no\n")
  f.write("  idmap config *:backend = tdb\n")
  f.write("  workgroup = %s\n"%d["workgroup"].upper())
  f.write("  netbios name = %s\n"%d["netbios_name"].upper())
  if d["security"] == "ads":
    f.write("  security = ADS\n")
    f.write("  preferred master = no\n")
    f.write("  encrypt passwords = yes\n")
    f.write("  winbind enum users  = yes\n")
    f.write("  winbind enum groups = yes\n")
    f.write("  winbind use default domain = yes\n")
    f.write("  winbind nested groups = yes\n")
    f.write("  winbind separator = +\n")
    f.write("  local master = no\n")
    f.write("  domain master = no\n")
    f.write("  wins proxy = no\n")
    f.write("  dns proxy = no\n")
    f.write("  idmap config *:range = %d-%d \n"%(id_map_max+1, id_map_max+10001))
    f.write("  winbind nss info = rfc2307\n")
    f.write("  winbind trusted domains only = no\n")
    f.write("  winbind refresh tickets = yes\n")
    f.write("  map untrusted to domain = Yes\n")
    f.write("  realm = %s\n"%realm.upper())
    f.write("  idmap config %s:default = yes\n"%d["workgroup"].upper())
    f.write("  idmap config %s:backend = ad\n"%d["workgroup"].upper())
    f.write("  idmap config %s:schema_mode = %s\n"%(d["workgroup"].upper(), d["ad_schema_mode"]))
    f.write("  idmap config %s:range = %d-%d\n"%(d["workgroup"].upper(), d["id_map_min"], d["id_map_max"]))
    f.write("  idmap config %s:base_rid = 0\n"%d["workgroup"].upper())
  return


def _generate_share_section(f, share_name, vol_name, workgroup, path, read_only, browseable, guest_ok, user_list, group_list, comment, auth_method):
  f.write("\n[%s]\n"%share_name)
  if comment:
    f.write("  comment = %s\n"%comment)
  f.write("  vfs objects = glusterfs\n")
  f.write("  glusterfs:volfile_server = localhost\n")
  f.write("  glusterfs:volume = %s\n"%vol_name)
  f.write("  path = %s\n"%path)
  f.write("  create mask = 0660\n")
  f.write("  directory mask = 0770\n")
  if read_only:
    t = "yes"
  else:
    t = "no"
  f.write("  read only = %s\n"%t)
  if user_list or group_list:
    s = "  valid users = "
    for user in user_list:
      if auth_method and auth_method == "users":
        s += " %s "%(user)
      else:
        s += " %s+%s "%(workgroup, user)
    for group in group_list:
      if auth_method and auth_method == "users":
        s += " %s "%(group)
      else:
        s += " @%s+%s "%(workgroup, group)
    s += "\n"
    f.write(s)

  if browseable:
    t = "yes"
  else:
    t = "no"
  f.write("  browseable = %s\n"%t)
  if guest_ok:
    f.write("  guest ok = yes\n")
    #f.write("  guest account = %s\n"%guest_account)
    
  return

def generate_smb_conf():
  d = load_auth_settings()
  with open("%s/smb.conf"%settings.SMB_CONF_PATH, "w+") as f:
    _generate_global_section(f, d)
    shl = load_shares_list()
    if shl:
      for share in shl:
        ul = []
        gl = []
        if not share["guest_ok"]:
          vul = load_valid_users_list(share["share_id"])
          if vul:
            for vu in vul:
              if vu["grp"]:
                gl.append(vu["name"])
              else:
                ul.append(vu["name"])
        _generate_share_section(f, share["name"], share["vol"], d["workgroup"], share["path"], share["read_only"], share["browseable"], share["guest_ok"], ul, gl, share["comment"], d["security"])
  f.close()


def generate_krb5_conf():
  d = load_auth_settings()
  with open("%s/krb5.conf"%settings.KRB5_PATH, "w") as f:
    f.write("; This file has been programatically generated by the fractal view system. Do not modify it manually!\n\n")
    f.write("[logging]\n")
    f.write("  default = FILE:/var/log/krb5libs.log\n")
    f.write("  kdc = FILE:/var/log/krb5kdc.log\n")
    f.write("  admin_server = FILE:/var/log/kadmind.log\n")

    f.write("\n[libdefaults]\n")
    f.write("  default_realm = %s\n"%d["realm"].upper())
    f.write("\n[realms]\n")
    f.write("    %s = {\n"%d["realm"].upper())
    f.write("    kdc = %s\n"%d["password_server"])
    f.write("    admin_server = %s\n"%d["password_server"])
    f.write("  }\n")
    f.write("\n[domain_realm]\n")
    f.write("  .%s = %s\n"%(d["realm"].lower(), d["realm"].upper()))
    f.write("  %s = %s\n"%(d["realm"].lower(), d["realm"].upper()))

  f.close()

def kinit(user, pswd, realm):
  c = command.execute_with_conf_and_rc("kinit %s@%s"%(user, realm), pswd+"\n")
  o = command.get_output_list(c[0])
  print "output = "
  print o
  e = command.get_error_list(c[0])
  print "error = "
  print e
  if c[1] != 0:
    err = ""
    if o:
      err += " ".join(o)
      err += ". "
    if e:
      err += " ".join(e)
    raise Exception("kinit failed : %s"%err)
  print "return code"
  print c[1]
  return

def net_ads_join(user, pswd, password_server):
  c = command.execute_with_rc("net ads join -S %s  -U %s%%%s"%(password_server, user, pswd))
  o = command.get_output_list(c[0])
  print "output = "
  print o
  e = command.get_error_list(c[0])
  #print "error = "
  #print e
  if c[1] != 0:
    err = ""
    if o:
      err += " ".join(o)
      err += ". "
    if e:
      err += " ".join(e)
    raise Exception("net ads join failed : %s."%err)
  return

def _get_user_or_group_list(type):
  d = load_auth_settings()
  if not d:
    raise Exception("Unspecified authentication method. Could not retrieve users")
  elif d["security"] == "users":
    if type and type == "users":
      l = local_users.get_local_users()
      if l:
        rl = []
        for ld in l:
          rl.append(ld["userid"])
        return rl
      else:
        return None
    else:
      return None
  elif d["security"] == "ads":
    if type and type == "users":
      return _get_ad_users_or_groups("users")
    elif type and type == "groups":
      return _get_ad_users_or_groups("groups")
  else:
    raise Exception("Unsupported authentication method. Could not retrieve users")

def get_user_list():
  return _get_user_or_group_list("users")

def get_group_list():
  return _get_user_or_group_list("groups")

def load_valid_users_list(share_id):
  l = []
  conn = None
  try :
    conn = sqlite3.connect("%s/integral_view_config.db"%settings.DB_LOCATION)
    #conn = sqlite3.connect("/home/bkrram/Documents/software/Django-1.4.3/code/gluster_admin/gluster_admin/devel/db/integral_view_config.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("select * from samba_valid_users where share_id = %s"%share_id)
    rows = cur.fetchall()
    if not rows:
      return None
    for row in rows:
      d = {}
      for key in row.keys():
        d[key] = row[key]
      l.append(d)
    return l
  finally:
    if conn:
      conn.close()


def _get_ad_users_or_groups(type):
  if type and type=="users":
    c = command.execute_with_rc("/usr/local/samba/bin/wbinfo -u ")
  elif type and type=="groups":
    c = command.execute_with_rc("/usr/local/samba/bin/wbinfo -g ")
  else:
    raise Exception("Unknown type specified to retrieve AD users or groups.")

  o = command.get_output_list(c[0])
  #print "wbinfo output = "
  #print o
  e = command.get_error_list(c[0])
  #print "error = "
  #print e
  if c[1] != 0:
    err = ""
    if o:
      err += " ".join(o)
      err += ". "
    if e:
      err += " ".join(e)
    raise Exception("Error getting AD users: %s."%err)
  else:
    return o

  


def main():
  generate_krb5_conf()

if __name__ == "__main__":
  main()
