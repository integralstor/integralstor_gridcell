#!/usr/bin/python
import urllib, urllib2, sys, os
from django.conf import settings

path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '%s/../..'%path)
os.environ['DJANGO_SETTINGS_MODULE']='integral_view.settings'

from integral_view.utils import system_info


def raise_alert(alert_url, msg):
  url = "http://%s/raise_alert?msg=%s"%(alert_url, urllib.quote_plus(msg))
  print url
  try:
    ur = urllib2.urlopen(url)
    ur.close()
  except urllib2.URLError as e:
    print "Error raising alert : %s"%e
    pass

import atexit
atexit.register(lock.release_lock, 'poll_for_alerts')

def main():

  if not lock.get_lock('poll_for_alerts'):
      print 'Generate Status : Could not acquire lock. Exiting.'

  alert_url = settings.ALERTS_URL

  '''
  sd = system_info.get_chassis_components_status(settings.PRODUCTION)

  if sd:
    for fan in sd["fans"]:
      if "status" in fan and fan["status"] != "ok":
        if fan["name"] in ["Fan_SYS3_1", "Fan_SYS3_2"]:
          raise_alert(alert_url, 'Power supply fan %s not functioning. View the back panel tab on the \"System status\" screen to get a visual picture of the failure.'%fan["name"])
        else:
          raise_alert(alert_url, 'Fan %s not functioning. View the back panel tab on the \"System status\" screen  to get a visual picture of the failure.'%fan["name"])
    for ps in sd["psus"]:
      if "status" in ps and ps["status"] != "ok":
        raise_alert(alert_url, 'Power supply unit %s not functioning. View the front panel tab on the \"System status\" screen  to get a visual picture of the failure.'%psu["name"])
      if "code" in ps and ps["code"] == '0x09':
        raise_alert(alert_url, 'No input to power supply unit %s. View the front panel tab on the \"System status\" screen to get a visual picture of the failure.'%ps["name"])
  '''

  si = system_info.load_system_config()
  for name, node in si.items():
    print node
    if node["node_status"] != 0:
      if node["node_status"] == -1:
        raise_alert(alert_url, 'Node %s seems to be down. View the \"System status\" screen for more info.'%(name))
      elif node["node_status"] > 0:
        raise_alert(alert_url, 'Node %s seems to be degraded with the following errors : %s.'%(name, ' '.join(node["errors"]))
    if node["cpu_status"]["status"] != "ok":
      raise_alert(alert_url, 'The CPU on node %s has issues. View the \"System status\" screen for more info.'%(name))
    if "ipmi_status" in node:        
      for status_dict in node["ipmi_status"]:
        if status_dict["status"] != "ok":
          raise_alert(alert_url, 'The %s on node %s has issues. The %s shows a value of %s. View the \"System status\" screen for more info.'%(status_dict["component_name"], status_dict["parameter_name"], status_dict["reading"]))
    for n, v in node["disk_status"].items():
      if v["status"] != "PASSED":
        raise_alert(alert_url, 'Disk %s on node %s has issues. View the \"System status\" screen for more info.'%(n, name))

  lock.release_lock('poll_for_alerts')

if __name__ == "__main__":
  main()
