#!/usr/bin/python
import urllib, urllib2, sys, os, time

from integralstor_common import alerts, lock  
from integralstor_gridcell import gluster_volumes

import atexit
atexit.register(lock.release_lock, 'gluster_commands')
atexit.register(lock.release_lock, 'gridcell_poll_for_alerts')

def check_quotas():
  alert_list = []
  try:
    vil, err = gluster_volumes.get_complete_volume_info_all()
    if err:
      raise Exception(err)
    if vil:
      for v in vil:
        if "quotas" in v:
          for dir, quota in v['quotas'].items():
            if v["quotas"][dir]["hard_limit_exceeded"].lower() == "yes":
              if dir == '/':
                alert_list.append("Exceeded hard quota limit of %s for volume %s. All writes will be disabled. "%(v['quotas'][dir]['limit'], v['name']))
              else:
                alert_list.append("Exceeded hard quota limit of %s for directory %s in volume %s. All writes will be disabled. "%(v['quotas'][dir]['limit'], dir, v['name']))
            elif v["quotas"][dir]["soft_limit_exceeded"].lower() == "yes":
              if dir == '/':
                alert_list.append("Exceeded soft quota limit %s of %s quota for volume %s. Current usage is %s"%(v['quotas']['/']['soft_limit'], v['quotas']['/']['limit'], v['name'], v['quotas']['/']['size']))
              else:
                alert_list.append("Exceeded soft quota limit %s of %s quota for directory %s in volume %s. Current usage is %s"%(v['quotas'][dir]['soft_limit'], v['quotas'][dir]['limit'], dir, v['name'], v['quotas'][dir]['size']))
  except Exception, e:
    return None, 'Error checking volume quota status : %s'%str(e)
  else:
    return alert_list, None


def main():
  try :
    lck, err = lock.get_lock('gridcell_poll_for_alerts')
    if err:
      raise Exception(err)

    if not lck:
        print 'Poll for alerts : Could not acquire alerts lock. Exiting.'
        sys.exit(-1)

    gluster_lck, err = lock.get_lock('gluster_commands')
    if err:
      raise Exception(err)

    if not gluster_lck:
        print 'Poll for alerts : Could not acquire gluster lock. Exiting.'
        sys.exit(-1)

    alerts_list, err = check_quotas()
    if err:
      print "Error getting quota information : %s"%err

    if alerts_list:
      print alerts_list
      alerts.raise_alert(alerts_list, 'IntegralStor GRIDCell quota limit exceeded')
    else:
      print 'No alerts to raise'

    ret, err = lock.release_lock('gluster_commands')
    if err:
      raise Exception(err)

    ret, err = lock.release_lock('gridcell_poll_for_alerts')
    if err:
      raise Exception(err)
  except Exception, e:
    print "Error generating gluster alerts : %s ! Exiting."%e
    sys.exit(-1)
  else:
    sys.exit(0)

if __name__ == "__main__":
  main()
