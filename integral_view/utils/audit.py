
import time, os, os.path, re, urllib, urllib2

from django.conf import settings
import fractalio
from fractalio import file_processing

import common, logs

class AuditException(Exception):

  msg = None

  def __init__(self, msg):
    self.msg = msg

  def __str__(self):
    return repr(self.msg)

def batch_audit(audit_url, audit_action, audit_str):
  if not audit_url:
    raise Exception("No Audit URL provided")
  audit_url = "%s/internal_audit/"%audit_url
  data = urllib.urlencode({'who' : 'batch',
                          'audit_action':audit_action,
                         'audit_str'  : audit_str})
  try :
    content = urllib2.urlopen(url=audit_url, data=data).read()
  except Exception, e:
    print ("Error printing audit action %s, audit string %s"%(audit_action, audit_str))


def audit(audit_action, audit_str, ip):

  audit_file = _get_audit_file_path()
  t = int(time.time())
  d = {}
  d["time"] = t
  d["audit_str"] = audit_str
  d["audit_action"] = audit_action
  with open(audit_file, "a") as f:
    f.write("%-13d %-16s %-25s %-45s\n"%(t, ip, audit_action, audit_str))
    f.flush()
  f.close()
  return True

def get_lines(file_name = None):
  #Return all the lines from the audit file as a list of dictionaries
  al = []
  if not file_name:
    fname = _get_audit_file_path()
  else:
    try:
      dir = settings.AUDIT_TRAIL_DIR
    except Exception:
      dir = os.path.abspath('./audit_trail')

    fname = os.path.normpath("%s/%s"%(dir, file_name))
    if not os.path.exists(fname):
      raise Exception("Specified file does not exist")

  if not fname:
    raise AuditException("Could not get audit file name.")
  if fname:
    try:
      with open(fname, "r") as f:
        for line in file_processing.reversed_lines(f):
          d = _parse_audit_line(line)
          al.append(d)
    except Exception, e:
      raise AuditException("Error processing audit file : %s"%str(e))
  return al

def _get_audit_file_path():
# Return the audit file path. Create the audit directory and file if it does not exist
  try:
    audit_dir = settings.AUDIT_TRAIL_DIR
  except Exception:
    audit_dir = os.path.abspath('./audit_trail')

  if not os.path.exists(audit_dir):
    try:
      os.mkdir(audit_dir)
    except OSError:
      return None

  audit_file = os.path.normpath("%s/audit.log"%audit_dir)
  if not os.path.exists(audit_file):
    mode = "w"
    #Create if it does not exist
    f = open(audit_file, mode)
    f.close()
  else:
    mode = "a"

  return audit_file


def _parse_audit_line(str):

  action_dict = { "create_volume":"Volume creation",
                  "expand_volume":"Volume expansion", 
                  "vol_start":"Volume start", 
                  "set_vol_options":"Set volume option", 
                  "vol_stop":"Volume stop", 
                  "vol_rebalance_start":"Start volume rebalance", 
                  "rebalance_start":"Start volume rebalance", 
                  "vol_rebalance_stop":"Stop volume rebalance", 
                  "volume_heal_full":"Volume data heal", 
                  "log_rotate":"Rotate volume log", 
                  "replace_node":"Replace node", 
                  "add_storage":"Add storage", 
                  "add_brick":"Add volume node", 
                  "remove_brick_start":"Remove volume node", 
                  "remove_brick_commit":"Remove volume node commit", 
                  "replace_brick_commit":"Replace volume node", 
                  "remove_storage":"Remove storage", 
                  "modify_user":"Modify Samba user", 
                  "create_user":"Create user", 
                  "modify_share":"Modify a share", 
                  "delete_share":"Delete a share", 
                  "modify_admin_password":"Modify admin password", 
                  "create_share":"Create a share", 
                  "modify_samba_server_security":"Modify Samba server security settings", 
                  "modify_samba_settings":"Modify share authentication settings", 
                  "modify_samba_server_basic":"Modify Samba server basic settings"
                }
  m = re.match("([\d]+)[\s]+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)[\s]+([a-zA-Z_]+)[\s]+(.*)", str)
  d = None
  if m:
    t = m.groups()
    if len(t) == 4:
      d = {}
      d["time"] = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(int(t[0])))
      d["ip"] = t[1]
      d["action_str"] = t[3]
      if t[2] in action_dict:
        d["action"] = action_dict[t[2]]
      else:
        d["action"] = "Unknown"

  return d

def rotate_audit_trail():
  #Rotate the audit trail log file

  try:
    dir = settings.AUDIT_TRAIL_DIR
  except Exception:
    dir = os.path.abspath('./alerts')
  
  logs.rotate_log(dir, "audit.log", None)

def get_log_file_list():
  #Get a list of dicts with each dict having a date and all the rotated log files for that date

  try:
    dir = settings.AUDIT_TRAIL_DIR
  except Exception:
    dir = os.path.abspath('./alerts')
  
  l = logs.get_log_file_list(dir, "audit.log")
  nl = logs.generate_display_log_file_list(l, "audit.log")
  return nl


if __name__ == "__main__":
  print audit("cralkjlkjte_vlume", "ldkfladkjldakf Created volume test1", "192.2.34.123")
#  with open("./audit_trail/audit.log") as f:
#    for line in f:
#      print _parse_audit_line(line)
