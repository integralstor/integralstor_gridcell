
import smtplib, json, email.utils, sqlite3, sys, os
from email.mime.text import MIMEText
from django.conf import settings

path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '%s/../..'%path)
#sys.path.insert(0, '/opt/fractal/gluster_admin')
#sys.path.insert(0, '/home/bkrram/Documents/software/Django-1.4.3/code/gluster_admin')

os.environ['DJANGO_SETTINGS_MODULE'] = 'integral_view.settings'


def load_email_settings():
  conn = None
  d = None
  try :
    conn = sqlite3.connect("%s/integral_view_config.db"%settings.DB_LOCATION)
    #conn = sqlite3.connect("/home/bkrram/Documents/software/Django-1.4.3/code/gluster_admin/gluster_admin/devel/db/integral_view_config.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("select * from email_config where id = 1")
    r = cur.fetchone()
    if not r:
      return None
    d = {}
    for key in r.keys():
      d[key] = r[key]
  finally:
    if conn:
      conn.close()
    return d

def save_email_settings(d):

  conn = None
  try :
    conn = sqlite3.connect("%s/integral_view_config.db"%settings.DB_LOCATION)
    #conn = sqlite3.connect("/home/bkrram/Documents/software/Django-1.4.3/code/gluster_admin/gluster_admin/devel/db/integral_view_config.db")
    cur = conn.cursor()
    cur.execute("select * from email_config")
    d1 = cur.fetchone()
    if d1:
      #Config exists so update
      cur.execute("update email_config set server=?, port=?, username=?, pswd=?, tls=?, email_alerts=?, rcpt_list=? where id = ?", (d["server"], d["port"], d["username"], d["pswd"], d["tls"], d["email_alerts"], d["rcpt_list"], 1,))
    else:
      #No config exists so insert
      cur.execute("insert into email_config (server, port, username, pswd, tls, email_alerts, rcpt_list, id) values (?,?,?,?,?,?,?,?)", (d["server"], d["port"], d["username"], d["pswd"], d["tls"], d["email_alerts"], d["rcpt_list"],1, ))
      cur.close()
    conn.commit()
  finally:
    if conn:
      conn.close()

def delete_email_settings():
  conn = None
  try :
    conn = sqlite3.connect("%s/integral_view_config.db"%settings.DB_LOCATION)
    #conn = sqlite3.connect("/home/bkrram/Documents/software/Django-1.4.3/code/gluster_admin/gluster_admin/devel/db/integral_view_config.db")
    cur = conn.cursor()
    cur.execute("delete from  email_config ")
    conn.commit()
  finally:
    if conn:
      conn.close()

def send_mail(server, port, username, pswd, tls, rcpt_list, header, body):

  msg = MIMEText(body)
  msg.set_unixfrom('FractalView Alerting System')
  if ',' in rcpt_list:
    emails = rcpt_list.split(',')
  else:
    emails = rcpt_list.split(' ')
  to = ','.join(emails)
  msg['From'] = email.utils.formataddr(('IntegralView alerting system', "%s@%s"%(username, server)))
  msg['Subject'] = header
  print "Sending msg with header \'%s\' and body\' %s\' to %s"%(header, body, emails)

  ms = None
  try:
    print "Opening connection to %s %d"%(server.strip(), port)
    ms = smtplib.SMTP(server, port)
    print "Opened connection"
    ms.set_debuglevel(True)
    ms.ehlo()
    if tls:
      if ms.has_extn('STARTTLS'):
        ms.starttls()
        ms.ehlo()
    ms.login(username, pswd)
    ms.sendmail('%s@%s'%(username, server), emails, msg.as_string())
  except Exception, e:
    print "Error %s"%str(e)
    return str(e)
  finally:
    if ms:
      ms.quit()
  return None

def main():
  #print "deleting"
  #d = delete_email_settings()
  #d = load_email_settings()
  #print d
  #print "creating"
  #save_email_settings({"server":"new", "port":22, "username":"newuser", "pswd":"newpass", "tls":True, "email_alerts":False, "rcpt_list":"1@1.com, 2@2.com"})
  #print "created"
  #d = load_email_settings()
  #print d
  #if d["tls"]:
  #  print "tls true"
  #if d["email_alerts"]:
  #  print "email_alerts true"
  #print "updating"
  #save_email_settings({"server":"new1", "port":23, "username":"newuser1", "pswd":"newpass1", "tls":False, "email_alerts":True, "rcpt_list":"11@1.com, 12@2.com"})
  #print "updated"
  #d = load_email_settings()
  #print d
  #if d["tls"]:
  #  print "tls true"
  #if d["email_alerts"]:
  #  print "email_alerts true"
  #print "deleting"
  #d = delete_email_settings()
  #d = load_email_settings()
  #print d
  #send_mail("testhdr", "testbdy")
  pass

if __name__== "__main__":
    main()

