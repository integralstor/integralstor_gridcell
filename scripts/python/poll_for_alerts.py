#!/usr/bin/python
import urllib, urllib2, sys, os
import salt.client

import fractalio
from fractalio import common, system_info, alerts, lock, lcd_display

production = common.is_production()

import atexit
atexit.register(lock.release_lock, 'poll_for_alerts')

def main():

  if not lock.get_lock('poll_for_alerts'):
      print 'Generate Status : Could not acquire lock. Exiting.'
      sys.exit(-1)

  try :
    si = system_info.load_system_config()
  except Exception, e:
    print "Error loading system config! Exiting."
    sys.exit(-1)

  try :
    alert_list = []
  
    client = salt.client.LocalClient()
    for node_name, node in si.items():
  
      # Check node status
      if "node_status" in node:
        if node["node_status"] != 0:
          if node["node_status"] < 0:
            alert_list.append("GRIDCell %s seems to be down."%node_name)
  
      # Check disks status
      err_pos = []
      s = ""
      if "disks" in node:
        disks = node["disks"]
        for sn, disk in disks.items():
          if disk["status"] != 'PASSED':
            alert_list.append("Disk with serial number %s on GRIDCell %s has problems."%(sn, node_name))
            err_pos.append(disk["position"])
      if err_pos:
        i = 1
        while i < 5:
          if i in err_pos:
            s += "Err"
          else:
            s += "Ok"
          if i < 4:
            s += ' '
          i += 1
        s1 =  '/opt/fractalio/scripts/python/lcdmsg.py "Disk error slots" "%s"'%s
        r1 = client.cmd(node_name, 'cmd.run', [s1])
      else:
        r1 = client.cmd(node_name, 'cmd.run', ['/opt/fractalio/bin/nodetype.sh'])
  
    
  
      # Check ipmi status
      if "ipmi_status" in node:
        status_list = node["ipmi_status"]
        for status_item in status_list:
          if status_item["status"] != 'ok':
            m = "The %s of the %s on GRIDCell %s is reporting errors" %(status_item["parameter_name"], status_item["component_name"], node_name)
            if "reading" in status_item:
              m += " with a reading of %s."%status_item["reading"]
            alert_list.append(m)
  
      # Check interface status
      if "interfaces" in node:
        interfaces = node["interfaces"]
        for if_name, interface in interfaces.items():
          if interface["status"] != 'up':
            alert_list.append("The network interface %s  on GRIDCell %s has problems."%(if_name, node_name))
  
      # Check zfs pool status
      if "pools" in node:
        pools = node["pools"]
        for pool in pools:
          pool_name = pool["name"]
          if pool["state"] != 'ONLINE':
            alert_list.append( "The ZFS pool %s on GRIDCell %s has issues. Pool state is %s"%(pool_name, node_name, pool["state"]))
          if "raid_or_mirror_status" in pool["config"]:
            if pool["config"]["raid_or_mirror_status"]["state"] != 'ONLINE':
              alert_list.append( "The RAIDZ status ZFS pool %s on GRIDCell %s has issues. The RAIDZ state is %s"%(pool_name, node_name, pool["config"]["raid_or_mirror_status"]["state"]))
          if "components" in pool["config"]:
            for component in pool["config"]["components"]:
              if component["state"] != 'ONLINE':
                alert_list.append( "The component %s in the ZFS pool %s on GRIDCell %s has issues. Component state is %s"%(component["name"], pool_name, node_name, component["state"]))
  
      # Check load average
      if "load_avg" in node:
        if node["load_avg"]["5_min"] > node["load_avg"]["cpu_cores"]:
          alert_list.append("The 5 minute load average on GRIDCell %s has been high with a value of %.2f."%(node_name, node["load_avg"]["5_min"]))
        if node["load_avg"]["15_min"] > node["load_avg"]["cpu_cores"]:
          alert_list.append("The 15 minute load average on GRIDCell %s has been high with a value of %.2f."%(node_name, node["load_avg"]["15_min"]))
  
    #print alert_list
    if alert_list:
      alerts.raise_alert(alert_list)
    lock.release_lock('poll_for_alerts')
  except Exception, e:
    print "Error generating alerts : %s ! Exiting."%e
    sys.exit(-1)
  else:
    sys.exit(0)

if __name__ == "__main__":
  main()


'''
    print node
    if node["node_status"] != 0:
      if node["node_status"] == -1:
        alerts.raise_alert(alert_url, 'GRIDCell %s seems to be down. View the \"System status\" screen for more info.'%(name))
      elif node["node_status"] > 0:
        raise_alert(alert_url, 'Node %s seems to be degraded with the following errors : %s.'%(name, ' '.join(node["errors"])))
    if node["cpu_status"]["status"] != "ok":
      alerts.raise_alert(alert_url, 'The CPU on GRIDCell %s has issues. View the \"System status\" screen for more info.'%(name))
    if "ipmi_status" in node:        
      for status_dict in node["ipmi_status"]:
        if status_dict["status"] != "ok":
          alerts.raise_alert(alert_url, 'The %s on GRIDCell %s has issues. The %s shows a value of %s. View the \"System status\" screen for more info.'%(status_dict["component_name"], status_dict["parameter_name"], status_dict["reading"]))
    for n, v in node["disk_status"].items():
      if v["status"] != "PASSED":
        alerts.raise_alert(alert_url, 'Disk %s on GRIDCell %s has issues. View the \"System status\" screen for more info.'%(n, name))
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
