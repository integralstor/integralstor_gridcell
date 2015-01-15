
import time, os, sys, fcntl, os.path, re

import fractalio
from fractalio import file_processing, common

import logs, mail

alerts_dir = common.get_alerts_dir()


def raise_alert(alert_url, msg):
  url = "http://%s/%s?msg=%s"%(common.get_alerts_url_host, common.get_alerts_url_component(), urllib.quote_plus(msg))
  #print url
  try:
    ur = urllib2.urlopen(url)
    ur.close()
  except urllib2.URLError as e:
    print "Error raising alert : %s"%e
    pass

class AlertsException(Exception):

  msg = None

  def __init__(self, msg):
    self.msg = msg

  def __str__(self):
    return repr(self.msg)

def load_alerts(fname = None):
  #Read the alerts file. If the last line does not havethe dash pattern then place it there so the alerts button can be updated accordingly
  alerts_list = []
  if not fname:
    filename = _get_alerts_file_path()
  else:
    filename = "%s/%s"%(alerts_dir, fname)

  match = None
  with open(filename, "r") as f:
    last_line = None
    for line in file_processing.reversed_lines(f):
    #for line in f:
      if not last_line:
        last_line = line
      if re.match("----------", line):
        continue
      else:
        d = {}
        m = re.search("([0-9]+)\s([\w\W\s]*)", line)
        if m:
          d["time"] = time.strftime("%c", time.localtime(int(m.groups()[0])))
          d["message"] = m.groups()[1]
          alerts_list.append(d)
    if last_line:
      match = re.match("----------", last_line)
  if not match:
    with open(filename, "a") as f:
      fcntl.flock(f, fcntl.LOCK_EX)
      f.write("\n----------")
      fcntl.flock(f, fcntl.LOCK_UN)
      f.close()
  return alerts_list

def raise_alert(msg_list):
  t = int(time.time())
  filename = _get_alerts_file_path()
  with open(filename, "a") as f:
    fcntl.flock(f, fcntl.LOCK_EX)
    for msg in msg_list:
      f.write("\n%-13d %s\n"%(t, msg))
    fcntl.flock(f, fcntl.LOCK_UN)
    f.close()
  try:
    d = mail.load_email_settings()
    if d:
      if d["email_alerts"]:
        ret = mail.send_mail(d["server"], d["port"], d["username"], d["pswd"], d["tls"], d["rcpt_list"], "Alert from Fractal-view", '\n'.join(msg_list))
        if ret:
          with open(filename, "a") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.write("\n%-13d %s\n"%(t, "Error sending email alert %s"%ret))
            fcntl.flock(f, fcntl.LOCK_UN)
            f.close()
  except Exception, e:
    print "Error emailing alert : Could not load email settings : %s"%str(e)
    with open(filename, "a") as f:
      fcntl.flock(f, fcntl.LOCK_EX)
      f.write("\n%-13d %s\n"%(t, "Error loading email config: %s"%str(e)))
      fcntl.flock(f, fcntl.LOCK_UN)
      f.close()

def _get_alerts_file_path():
# Return the alerts file path. Create the alerts directory and file if it does not exist

  if not os.path.exists(alerts_dir):
    try:
      os.mkdir(alerts_dir)
    except OSError:
      return None

  filename = os.path.normpath("%s/alerts.log"%alerts_dir)
  if not os.path.exists(filename):
    mode = "w"
    #Create if it does not exist
    f = open(filename, mode)
    f.close()
  else:
    mode = "a"

  return filename

def new_alerts():

  filename = _get_alerts_file_path()
  last_line = None
  with open(filename) as f:
    for line in f:
      last_line = line
  if not last_line:
    return False
  if re.match("----------", last_line):
    return False
  else:
    return True

def rotate_alerts():
  #Rotate the alerts log file

  logs.rotate_log(alerts_dir, "alerts.log", ["----------"])

def get_log_file_list():
  #Get a list of dicts with each dict having a date and all the rotated log files for that date

  l = logs.get_log_file_list(alerts_dir, "alerts.log")
  nl = logs.generate_display_log_file_list(l, "alerts.log")
  return nl
