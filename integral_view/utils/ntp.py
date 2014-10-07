import re
from django.conf import settings
import command

def get_ntp_servers():

  list = []
  try :
    with open("%s/ntp.conf"%settings.NTP_CONF_PATH, "r") as f:
      lines = f.readlines()
      for line in lines:
        r1 = re.match("[\s]*server[\s]*([\S]+)", line)
        if r1:
          r = r1.groups()
          if len(r) > 0:
            s = r[0]
            if s and s != "127.0.0.1":
              list.append(s)
  except Exception, e:
    pass
  return list

def get_non_server_lines():
  list = []
  try:
    with open("%s/ntp.conf"%settings.NTP_CONF_PATH, "r") as f:
      lines = f.readlines()
      for line in lines:
        r1 = re.match("[\s]*server[\s]*([\S]+)", line)
        if not r1:
          list.append(line)
    return list
  except Exception, e:
    return None

def restart_ntp_service():

  r, rc = command.execute_with_rc("service ntpd restart")
  if rc != 0:
    str = ""
    l = command.get_output_list(r)
    if l:
      str += ",".join(l)
    l = command.get_error_list(r)
    if l:
      str += ",".join(l)
    raise Exception("Error restarting NTP services : %s"%str)
