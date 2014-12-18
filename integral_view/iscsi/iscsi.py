
import fractalio
from fractalio import db
import json
from django.conf import settings

def load_iscsi_volumes_list(vil):
  #with open("%s/iscsi_volumes.json"%settings.SYSTEM_INFO_DIR, "r") as f:
  #  il = json.load(f)

  il = db.read_multiple_rows("%s/integral_view_config.db"%settings.DB_LOCATION, "select * from iscsi_volumes")
  if not il:
    return None

  iscsi_volumes_list = []
  for i in il:
    current = False
    for v in vil:
      if v["name"] == i["vol_name"]:
        current = True
        break
    if current:
      iscsi_volumes_list.append(i["vol_name"])
  return iscsi_volumes_list

def add_iscsi_volume(vol_name):

  d = db.read_single_row("%s/integral_view_config.db"%settings.DB_LOCATION, "select * from iscsi_volumes where vol_name=\'%s\'"%vol_name)
  if d:
    return
  cl = [("insert into iscsi_volumes(id, vol_name) values (NULL, ?)",(vol_name,))]
  db.execute_iud("%s/integral_view_config.db"%settings.DB_LOCATION, cl)


'''
def save_iscsi_volumes_list(l):
  with open("%s/iscsi_volumes.json"%settings.SYSTEM_INFO_DIR, "w") as f:
    json.dump(l, f, indent=2)
'''

def load_targets_list():
  iscsi_target_list = db.read_multiple_rows("%s/integral_view_config.db"%settings.DB_LOCATION, "select * from iscsi_targets")
  return iscsi_target_list
  
  '''
  with open("%s/iscsi_targets.json"%settings.SYSTEM_INFO_DIR, "r") as f:
    iscsi_target_list = json.load(f)
  return iscsi_target_list
  '''

def save_target(id, cd):

  cl = [("update iscsi_targets set lun_size=?, target_alias=?, auth_method=?, queue_depth=?, auth_group_id=?, init_group_id = ?  where id=?",(cd["lun_size"], cd["target_alias"], cd["auth_method"], cd["queue_depth"], cd["auth_group_id"], cd["init_group_id"], id, ))]
  db.execute_iud("%s/integral_view_config.db"%settings.DB_LOCATION, cl)

  '''
  l = load_targets_list()
  nl = []
  for i in l:
    if i["id"] != id:
      nl.append(i)
    else:
      d = {}
      d["id"] = id
      d["vol_name"] = cd["vol_name"]
      d["target_name"] = cd["target_name"]
      d["lun_size"] = cd["lun_size"]
      d["target_alias"] = cd["target_alias"]
      #d["target_flags"] = cd["target_flags"]
      d["auth_method"] = cd["auth_method"]
      d["queue_depth"] = cd["queue_depth"]
      d["auth_group_id"] = cd["auth_group_id"]
      d["init_group_id"] = cd["init_group_id"]
      nl.append(d)
  save_target_list(nl)
  '''

def load_target_info(index):

  d = db.read_single_row("%s/integral_view_config.db"%settings.DB_LOCATION, "select * from iscsi_targets where id=\'%d\'"%index)
  return d

  '''
  ret = None
  l = load_targets_list()
  for t in l:
    if t["id"] == index:
      return t
  return None
  '''

def create_iscsi_target(vol_name, target_alias, lun_size, auth_method, queue_depth, auth_group_id, init_group_id):

  cl = [("insert into iscsi_targets(id, vol_name, target_name, target_alias, lun_size, auth_method, queue_depth, auth_group_id, init_group_id) values (NULL, ?, ?, ?, ?, ?, ?, ?, ?)",(vol_name, vol_name, target_alias, lun_size, auth_method, queue_depth, auth_group_id, init_group_id, ))]
  db.execute_iud("%s/integral_view_config.db"%settings.DB_LOCATION, cl)

  '''
  l = load_targets_list()
  max_id = 0
  for i in l:
    if i["id"] > max_id:
      max_id = i["id"]
  d = {}
  d["id"] = max_id + 1
  d["vol_name"] = vol_name
  d["target_name"] = target_name
  d["target_alias"] = target_alias
  d["lun_size"] = lun_size
  #d["target_flags"] = target_flags
  d["auth_method"] = auth_method
  d["queue_depth"] = queue_depth
  d["auth_group_id"] = auth_group_id
  d["init_group_id"] = init_group_id
  l.append(d)
  save_target_list(l)
  '''

def delete_target(id):

  db.execute_iud([("%s/integral_view_config.db"%settings.DB_LOCATION, "delete from iscsi_targets where id = \'%d\'"%id,)])

  '''
  l = load_targets_list()
  nl = []
  for i in l:
    if i["id"] != id:
      nl.append(i)
  save_target_list(nl)
  '''

def delete_all_targets():
  db.execute_iud("%s/integral_view_config.db"%settings.DB_LOCATION, [("delete from iscsi_targets",)])

def save_target_list(l):
  with open("%s/iscsi_targets.json"%settings.SYSTEM_INFO_DIR, "w") as f:
    json.dump(l, f, indent=2)

def load_initiators_list():
  iscsi_initiator_list = db.read_multiple_rows("%s/integral_view_config.db"%settings.DB_LOCATION, "select * from iscsi_initiators")
  return iscsi_initiator_list
  '''
  with open("%s/iscsi_initiators.json"%settings.SYSTEM_INFO_DIR, "r") as f:
    iscsi_initiator_list = json.load(f)
  return iscsi_initiator_list
  '''


def load_initiator_info(index):

  d = db.read_single_row("%s/integral_view_config.db"%settings.DB_LOCATION, "select * from iscsi_initiators where id=\'%d\'"%index)
  return d

  '''
  ret = None
  init_list = load_initiators_list()
  for init in init_list:
    if init["id"] == index:
      ret = init
  return ret
  '''

def create_iscsi_initiator(initiators, auth_network, comment):

  d = db.read_single_row("%s/integral_view_config.db"%settings.DB_LOCATION, "select * from iscsi_initiators where auth_network = \'%s\' and initiators=\'%s\'"%(initiators.lower(), auth_network.lower()))
  if d:
    raise Exception("An initiator with the same parameters (with ID %d) already exists"%i["id"])
    return

  cl = [("insert into iscsi_initiators(id, initiators, auth_network, comment) values (NULL, ?, ?, ?)",(initiators.lower(), auth_network.lower(), comment, ))]
  db.execute_iud("%s/integral_view_config.db"%settings.DB_LOCATION, cl)

  '''
  l = load_initiators_list()
  max_id = 0
  for i in l:
    if i["auth_network"].lower() == auth_network and i["initiators"].lower() == initiators:
      raise Exception("An initiator with the same parameters (with ID %d) already exists"%i["id"])
    if i["id"] > max_id:
      max_id = i["id"]
  d = {}
  d["id"] = max_id + 1
  d["initiators"] = initiators
  d["auth_network"] = auth_network
  d["comment"] = comment
  l.append(d)
  save_initiator_list(l)
  '''

def delete_initiator(id):

  db.execute_iud([("%s/integral_view_config.db"%settings.DB_LOCATION, "delete from iscsi_initiators where id = \'%d\'"%id,)])

  '''
  l = load_initiators_list()
  nl = []
  for i in l:
    if i["id"] != id:
      nl.append(i)
  save_initiator_list(nl)
  '''

def delete_all_initiators():
  db.execute_iud("%s/integral_view_config.db"%settings.DB_LOCATION, [("delete from iscsi_initiators",)])

def save_initiator_list(l):
  with open("%s/iscsi_initiators.json"%settings.SYSTEM_INFO_DIR, "w") as f:
    json.dump(l, f, indent=2)

def save_initiator(id, cd):

  cl = [("update iscsi_initiators set initiators=?, auth_network=?, comment=? where id=?",(cd["initiators"].lower(), cd["auth_network"].lower(), cd["comment"], id, ))]
  db.execute_iud("%s/integral_view_config.db"%settings.DB_LOCATION, cl)

  '''
  l = load_initiators_list()
  nl = []
  for i in l:
    if i["id"] != id:
      nl.append(i)
    else:
      d = {}
      d["id"] = id
      d["initiators"] = cd["initiators"]
      d["auth_network"] = cd["auth_network"]
      d["comment"] = cd["comment"]
      nl.append(d)
  save_initiator_list(nl)
  '''

def save_auth_access_group_list(l):
  with open("%s/iscsi_auth_access_group.json"%settings.SYSTEM_INFO_DIR, "w") as f:
    json.dump(l, f, indent=2)

def load_auth_access_group_list():

  iscsi_auth_access_group_list = db.read_multiple_rows("%s/integral_view_config.db"%settings.DB_LOCATION, "select * from iscsi_auth_access_groups")
  return iscsi_auth_access_group_list

  '''
  with open("%s/iscsi_auth_access_group.json"%settings.SYSTEM_INFO_DIR, "r") as f:
    iscsi_auth_access_group_list = json.load(f)
  '''


def save_auth_access_users_list(l):
  with open("%s/iscsi_auth_access_users.json"%settings.SYSTEM_INFO_DIR, "w") as f:
    json.dump(l, f, indent=2)
  generate_auth_conf()

def load_auth_access_users_list():
  iscsi_auth_access_users_list = db.read_multiple_rows("%s/integral_view_config.db"%settings.DB_LOCATION, "select * from iscsi_auth_access_users")
  return iscsi_auth_access_users_list
  '''
  with open("%s/iscsi_auth_access_users.json"%settings.SYSTEM_INFO_DIR, "r") as f:
    iscsi_auth_access_users_list = json.load(f)
  '''

def load_auth_access_users_info(auth_access_group_id):

  l = db.read_multiple_rows("%s/integral_view_config.db"%settings.DB_LOCATION, "select * from iscsi_auth_access_users where auth_access_group_id = \'%d\'"%auth_access_group_id)
  return l

  '''
  ret = None
  l = []
  aa_list = load_auth_access_users_list()
  for aa in aa_list:
    if aa["auth_access_group_id"] == auth_access_group_id:
      l.append(aa)
  '''

def load_auth_access_user_info(user_id):

  d = db.read_single_row("%s/integral_view_config.db"%settings.DB_LOCATION, "select * from iscsi_auth_access_users where id = \'%d\'"%user_id)
  return d

  '''
  ret = None
  l = []
  aa_list = load_auth_access_users_list()
  for aa in aa_list:
    if aa["user_id"] == user_id:
      return aa
  return None
  '''

def create_auth_access_group():

  cl = [("insert into iscsi_auth_access_groups(id) values (NULL)",)]
  rowid = db.execute_iud("%s/integral_view_config.db"%settings.DB_LOCATION, cl, True)
  cl = [("update iscsi_auth_access_groups set name=\'AuthGroup%d\' where rowid = \'%d\'"%(rowid, rowid),)]
  db.execute_iud("%s/integral_view_config.db"%settings.DB_LOCATION, cl)
  return rowid

  '''
  l = load_auth_access_group_list()
  max_id = 0
  for i in l:
    if i["id"] > max_id:
      max_id = i["id"]
  d = {}
  d["id"] = max_id + 1
  d["name"] = "AuthGroup%d"%(max_id+1)
  l.append(d)
  save_auth_access_group_list(l)
  return max_id + 1
  '''

def create_auth_access_user(auth_access_group_id, user, secret):

  d = db.read_single_row("%s/integral_view_config.db"%settings.DB_LOCATION, "select * from iscsi_auth_access_users where auth_access_group_id = \'%d\' and user = \'%s\'"%(auth_access_group_id, user))
  if d:
    raise Exception("A user set with the same username exists for this authorized access group")
    return

  cl = [("insert into iscsi_auth_access_users(id, auth_access_group_id, user, secret) values (NULL, \'%d\', \'%s\', \'%s\')"%(auth_access_group_id, user, secret),)]
  rowid = db.execute_iud("%s/integral_view_config.db"%settings.DB_LOCATION, cl, True)

  '''
  l = load_auth_access_users_list()
  max_user_id = 0
  for i in l:
    if i["auth_access_group_id"] == auth_access_group_id and i["user"] == user:
      if "peer_user" in i and i["peer_user"] == peer_user:
        raise Exception("A user set with the same user and peer user exists for this authorized access group")
      if i["user_id"] > max_user_id:
        max_user_id = i["user_id"]

  d = {}
  d["auth_access_group_id"] = auth_access_group_id
  d["user_id"] = max_user_id + 1
  d["user"] = user
  d["peer_user"] = peer_user
  d["secret"] = secret
  d["peer_secret"] = peer_secret
  l.append(d)
  save_auth_access_users_list(l)
  '''

def delete_auth_access_group(id):

  cl = [("delete from iscsi_auth_access_groups where id = \'%d\'"%id,), ("delete from iscsi_auth_access_users where auth_access_group_id = \'%d\'"%id,)]
  db.execute_iud("%s/integral_view_config.db"%settings.DB_LOCATION, cl)

  '''
  l = load_auth_access_group_list()
  nl = []
  for i in l:
    if i["id"] != id:
      nl.append(i)
  save_auth_access_group_list(nl)
  l = load_auth_access_users_list()
  nl = []
  for i in l:
    if i["auth_access_group_id"] != id:
      nl.append(i)
  save_auth_access_users_list(nl)
  '''

def delete_all_auth_access_groups():
  db.execute_iud("%s/integral_view_config.db"%settings.DB_LOCATION, [("delete from iscsi_auth_access_groups",)])

def delete_auth_access_user(user_id):

  cl = [("delete from iscsi_auth_access_users where id = \'%d\'"%user_id,)]
  db.execute_iud("%s/integral_view_config.db"%settings.DB_LOCATION, cl)

  '''
  l = load_auth_access_users_list()
  nl = []
  for i in l:
    if i["user_id"] != user_id:
      nl.append(i)
  save_auth_access_users_list(nl)
  '''
  
def delete_all_auth_access_users():
  db.execute_iud("%s/integral_view_config.db"%settings.DB_LOCATION, [("delete from iscsi_auth_access_users",)])

def save_auth_access_user(auth_access_group_id, user_id, user, secret):

  d = db.read_single_row("%s/integral_view_config.db"%settings.DB_LOCATION, "select * from iscsi_auth_access_users where auth_access_group_id = \'%d\' and user = \'%s\'"%(auth_access_group_id, user))
  if d:
    raise Exception("A user set with the same username exists for this authorized access group")
    return

  cl = [("update iscsi_auth_access_users set user=\'%s\', secret=\'%s\' where id = \'%d\'"%(user, secret, user_id), )]
  db.execute_iud("%s/integral_view_config.db"%settings.DB_LOCATION, cl)

  '''
  l = load_auth_access_users_list()
  nl = []
  for i in l:
    if i["user_id"] != user_id:
      print "appending as is"
      nl.append(i)
    else:
      print "changing and appending"
      d = {}
      d["user_id"] = user_id
      d["auth_access_group_id"] = i["auth_access_group_id"]
      d["user"] = user
      d["peer_user"] = peer_user
      d["secret"] = secret
      d["peer_secret"] = peer_secret
      nl.append(d)
  save_auth_access_users_list(nl)
  '''
  
def load_global_target_conf():
  igt  = db.read_single_row("%s/integral_view_config.db"%settings.DB_LOCATION, "select * from iscsi_global_target_conf where id = \'1\'")
  return igt

  '''
  with open("%s/iscsi_target_global_config.json"%settings.SYSTEM_INFO_DIR, "r") as f:
    igt = json.load(f)
  return igt
  '''

def reset_global_target_conf():
  cl = [("update iscsi_global_target_conf set discovery_auth_method=?, io_timeout=?, nop_in_interval=?, max_sessions=?, max_connections=?, max_presend_r2t=?, max_outstanding_r2t=?, first_burst_length=?, max_burst_length=?, max_receive_data_segment_length=?, default_time_to_wait=?, default_time_to_retain=? where id='1'",(None, 30, 20, 16, 8,32,16,65536,262144,262144,2,60,))]
  db.execute_iud("%s/integral_view_config.db"%settings.DB_LOCATION, cl)

def save_global_target_conf(cd):
  igt  = db.read_single_row("%s/integral_view_config.db"%settings.DB_LOCATION, "select * from iscsi_global_target_conf where id = \'1\'")
  if not igt:
    cl = [("insert into iscsi_global_target_conf(id, base_name, discovery_auth_method, discovery_auth_group, io_timeout, nop_in_interval, max_sessions, max_connections, max_presend_r2t, max_outstanding_r2t, first_burst_length, max_burst_length, max_receive_data_segment_length, default_time_to_wait, default_time_to_retain) values (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",(cd["base_name"], cd["discovery_auth_method"], cd["discovery_auth_group"], cd["io_timeout"], cd["nop_in_interval"], cd["max_sessions"], cd["max_connections"],cd["max_presend_r2t"],cd["max_outstanding_r2t"],cd["first_burst_length"],cd["max_burst_length"],cd["max_receive_data_segment_length"],cd["default_time_to_wait"],cd["default_time_to_retain"],))]
  else:
    cl = [("update iscsi_global_target_conf set base_name=?, discovery_auth_method=?, discovery_auth_group=?, io_timeout=?, nop_in_interval=?, max_sessions=?, max_connections=?, max_presend_r2t=?, max_outstanding_r2t=?, first_burst_length=?, max_burst_length=?, max_receive_data_segment_length=?, default_time_to_wait=?, default_time_to_retain=? where id='1'",(cd["base_name"], cd["discovery_auth_method"], cd["discovery_auth_group"], cd["io_timeout"], cd["nop_in_interval"], cd["max_sessions"], cd["max_connections"],cd["max_presend_r2t"],cd["max_outstanding_r2t"],cd["first_burst_length"],cd["max_burst_length"],cd["max_receive_data_segment_length"],cd["default_time_to_wait"],cd["default_time_to_retain"],))]
  db.execute_iud("%s/integral_view_config.db"%settings.DB_LOCATION, cl)

  '''
  d = {}
  #d["base_name"]  = cd["base_name"]
  d["discovery_auth_method"]  = cd["discovery_auth_method"]
  d["discovery_auth_group"]  = cd["discovery_auth_group"]
  d["base_name"]  = cd["base_name"]
  d["io_timeout"] = cd["io_timeout"]
  d["nop_in_interval"] = cd["nop_in_interval"]
  d["max_sessions"] = cd["max_sessions"]
  d["max_connections"] = cd["max_connections"]
  d["max_presend_r2t"] = cd["max_presend_r2t"]
  d["max_outstanding_r2t"] = cd["max_outstanding_r2t"]
  d["first_burst_length"] = cd["first_burst_length"]
  d["max_burst_length"] = cd["max_burst_length"]
  d["max_receive_data_segment_length"] = cd["max_receive_data_segment_length"]
  d["default_time_to_wait"] = cd["default_time_to_wait"]
  d["default_time_to_retain"] = cd["default_time_to_retain"]
  '''
  '''
  d["enable_luc"] = cd["enable_luc"]
  if d["enable_luc"]:
    d["controller_ip_addr"] = cd["controller_ip_addr"]
    d["controller_tcp_port"] = cd["controller_tcp_port"]
    d["controller_auth_netmask"] = cd["controller_auth_netmask"]
  d["controller_auth_method"] = cd["controller_auth_method"]
  d["controller_auth_group"] = cd["controller_auth_group"]
  '''

  '''
  with open("%s/iscsi_target_global_config.json"%settings.SYSTEM_INFO_DIR, "w") as f:
    json.dump(d, f, indent=2)
  '''


def generate_global(fh, dict):
  fh.write ("# This is programmatically generated \"istgt.conf\" file. \n")
  fh.write ("\n\n[Global] \n")
  fh.write ("  Comment \"Global section\" \n")
  fh.write ("\n")
  fh.write ("  # node name (not include optional part) \n")
  fh.write ("  NodeBase \"%s\" \n"%dict["base_name"])
  fh.write ("\n")
  fh.write ("  # files \n")
  fh.write ("  PidFile /var/run/istgt.pid \n")
  fh.write ("  AuthFile /usr/local/etc/istgt/auth.conf \n")
  fh.write ("\n")
  fh.write ("  # directories \n")
  fh.write ("  # for removable media (virtual DVD / Virtual Tape) \n")
  fh.write ("  MediaDirectory /var/istgt \n")
  fh.write ("\n")
  fh.write ("  # syslog facility \n")
  fh.write ("  LogFacility \"local7\" \n")
  fh.write ("\n")
  fh.write ("  # socket I/O timeout sec. (polling is infinity) \n")
  fh.write ("  Timeout %d \n"%dict["io_timeout"])
  fh.write ("\n")
  fh.write ("  # NOPIN sending interval sec. \n")
  fh.write ("  NopInInterval %d \n"%dict["nop_in_interval"])
  fh.write ("\n")
  fh.write ("  # authentication information for discovery session \n")
  fh.write ("  DiscoveryAuthMethod %s\n"%dict["discovery_auth_method"])
  fh.write ("\n")
  fh.write ("  # DiscoveryAuthGroup %s\n"%dict["discovery_auth_group"])
  fh.write ("  # reserved maximum connections and sessions \n")
  fh.write ("  # NOTE: iSCSI boot is 2 or more sessions required \n")
  fh.write ("  MaxSessions %d \n"%dict["max_sessions"])
  fh.write ("  MaxConnections %d \n"%dict["max_connections"])
  fh.write ("\n")
  fh.write ("  # maximum number of sending R2T in each connection \n")
  fh.write ("  # actual number is limited to QueueDepth and MaxCmdSN and ExpCmdSN \n")
  fh.write ("  # 0=disabled, 1-256 =improves large writing \n")
  fh.write ("  MaxR2T %d \n"%dict["max_presend_r2t"])
  fh.write ("\n")
  fh.write ("  # iSCSI initial parameters negotiate with initiators \n")
  fh.write ("  # NOTE: incorrect values might crash \n")
  fh.write ("  MaxOutstandingR2T %d \n"%dict["max_outstanding_r2t"])
  fh.write ("  DefaultTime2Wait %d \n"%dict["default_time_to_wait"])
  fh.write ("  DefaultTime2Retain %d \n"%dict["default_time_to_retain"])
  fh.write ("  FirstBurstLength %d \n"%dict["first_burst_length"])
  fh.write ("  MaxBurstLength %d \n"%dict["max_burst_length"])
  fh.write ("  MaxRecvDataSegmentLength %d\n"%dict["max_receive_data_segment_length"])
  fh.write ("\n")
  fh.write ("  #NOTE: not supported \n")
  fh.write ("  InitalR2T Yes \n")
  fh.write ("  ImmediateData Yes \n")
  fh.write ("  DataPDUInOrder Yes \n")
  fh.write ("  DataSequenceInOrder Yes \n")
  fh.write ("  ErrorRecoveryLevel 0 \n")
  return

def generate_unit_control(fh):
  fh.write ("\n\n[UnitControl] \n")
  fh.write ("  Comment \"Internal Logical Unit Controller \" \n")
  fh.write ("\n")
  fh.write ("  #AuthMethod Auto \n")
  fh.write ("  AuthMethod None\n")
  #fh.write ("  AuthGroup AuthGroup10000 \n")
  fh.write ("\n")
  fh.write ("  # this portal is only used as controller (by istgtcontrol) \n")
  fh.write ("  # if it's not necessary, no portal is valid \n")
  #fh.write ("  #Portal UC1 [::1]:3261 \n")
  fh.write ("  Portal UC1 *:3261 \n")
  fh.write ("\n")
  fh.write ("  # accept IP mask \n")
  fh.write ("  #Netmask [::1] \n")
  fh.write ("  Netmask 127.0.0.1 \n")
  return

def generate_portal(fh):
  fh.write ("\n\n# You should set IPs in /etc/rc.conf for physical I/F \n")
  fh.write ("[PortalGroup1] \n")
  #fh.write ("  Comment \"%s\"\n" % dict["comment"])
  fh.write ("  Portal DA1 *:3260\n" )
  #fh.close ()
  return


def generate_initiator(fh, dict):
  fh.write ("\n\n[InitiatorGroup%d] \n"%dict["id"])
  fh.write ("  Comment \"%s\" \n" % dict["comment"])
  fh.write ("  InitiatorName \"%s\" \n" %dict["initiators"] )
  fh.write ("  Netmask %s \n" % (dict["auth_network"]))
  #fh.close ()
  return


  
def generate_logical_unit(fh, id, vol_name, target_name, init_group_id, auth_method, auth_group_id, queue_depth, target_alias, lun_size):
  fh.write ("\n\n[LogicalUnit%d]\n"%id)
  #fh.write ("  Comment \"%s\" \n" %comment)
  fh.write ("\n")
  fh.write ("  #full specified iqn (same as below) \n")
  fh.write ("  #TargetName iqn.2014-15.in.fractalio.istgt:%s \n"%vol_name)
  fh.write ("  #short specified non iqn (will add NodeBase) \n")
  fh.write ("  TargetName %s \n"%target_name)
  fh.write ("  TargetAlias \"%s\" \n" %target_alias)
  fh.write ("\n")
  fh.write ("  # use initiators in tag1 via portals in tag1 \n")
  fh.write ("  Mapping PortalGroup1 InitiatorGroup%s \n"%init_group_id)
  fh.write ("\n")
  
  fh.write ("  #accept both CHAP and None \n")
  fh.write ("  AuthMethod %s \n"%auth_method)
  fh.write ("  AuthGroup AuthGroup%s\n"%auth_group_id) 
  fh.write ("  UnitType GFAPI \n")
  fh.write ("  UnitOnline Yes \n")
  fh.write ("\n")
  
  fh.write ("  #Use\n")
  fh.write ("  UseDigest Auto\n")
  #fh.write ("  UnitType Disk\n")
  fh.write ("\n")
  
  fh.write ("  # SCSI INQUIRY - Vendor(8) Product(16) Revision(4) Serial(16)\n")
  fh.write ("  #UnitInquiry \"FreeBSD\" \"iSCSI Disk\" \"0123\" \"10000001\" \n")
  fh.write ("  #Queuing 0=disabled, 1-255=enabled with specified depth. \n")
  fh.write ("  QueueDepth %d \n"%queue_depth)
  fh.write ("\n")
  
  fh.write ("  #override global setting if need \n")
  fh.write ("  #MaxOutstandingR2T 16 \n")
  fh.write ("  #DefaultTime2Wait 2 \n")
  fh.write ("  #DefaultTime2Retain 60 \n")
  fh.write ("  #FirstBurstLength 262144 \n")
  fh.write ("  #MaxBurstLength 1048576 \n")
  fh.write ("  #MaxRecvDataSegmentLength 262144 \n")
  fh.write ("  #InitialR2T Yes \n")
  fh.write ("  #ImmediateData Yes \n")
  fh.write ("  #DataPDUInOrder Yes \n")
  fh.write ("  #DataSequenceInOrder Yes \n")
  fh.write ("  #ErrorRecoveryLevel 0\n")
  fh.write ("\n")
  
  fh.write ("  #Logical Volume for this unit on LUN0 \n")
  fh.write ("  #for file extent \n")
  fh.write ("\n")
  
  fh.write ("  LUN0 Storage %s %sMB \n" % (vol_name, lun_size) )
  return


def generate_istgt_conf():

  with open("istgt.conf", "w") as fh:

    d = load_global_target_conf()
    generate_global(fh, d)
    generate_unit_control(fh)
    generate_portal(fh)
    il = load_initiators_list()
    for i in il:
      generate_initiator(fh, i)
    tl = load_targets_list()
    for t in tl:
      generate_logical_unit(fh, t["id"], t["vol_name"],  t["target_name"], t["init_group_id"], t["auth_method"], t["auth_group_id"], t["queue_depth"], t["target_alias"], t["lun_size"])

  fh.close()

def generate_auth_conf():
  gl = load_auth_access_group_list()
  with open("auth.conf", "w") as fh:
    if gl:
      for g in gl:
        ul = load_auth_access_users_info(g["id"])
        print len(ul)
        if len(ul) == 0:
          continue
        fh.write ("\n\n[%s] \n"%g["name"])
        for u in ul:
          fh.write ("  Auth \"%s\" \"%s\"  \n" % (u["user"], u["secret"]))
          '''
          if u["peer_user"]:
            fh.write ("  Auth \"%s\" \"%s\" \\ \n" % (u["user"], u["secret"]))
            fh.write ("        \"%s\" \"%s\"  \n" %(u["peer_user"], u["peer_secret"]))
          else:
            fh.write ("  Auth \"%s\" \"%s\"  \n" % (u["user"], u["secret"]))
          '''
  fh.close ()
  return
