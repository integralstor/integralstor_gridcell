
import re
import pprint
import command

def get_component_info(cline):
  #print cline
  component_dict = {}
  component_list = cline.split()
  #print component_list
  component_dict["name"] = component_list[0]
  component_dict["state"] = component_list[1]
  component_dict["read"] = int(component_list[2])
  component_dict["write"] = int(component_list[3])
  component_dict["cksum"] = int(component_list[4])
  return component_dict

def process_config_section(config_list):
  #Given a list of lines in the config section, return a dict with all the components
  #print "here"
  config_dict = {}
  component_list = []
  replace_list = []
  match_name = False
  match_type = False
  match_replace = False
  match_logs = False
  match_components = False
  for cline in config_list:
    #print "processing %s"%cline
    if cline == "":
      continue
    res1 = re.match('^NAME[\s]*STATE[\s]*READ[\s]*WRITE[\s]*CKSUM', cline.strip())
    if res1:
      #Skip the next line because its just the name
      match_name = True
      continue
    if match_name:
      match_name = False
      #print "matching name for %s"%cline
      match_type = True
      component_dict = get_component_info(cline)
      config_dict["pool_status"] = component_dict
      continue
    if match_logs:
      match_components = False
      logs_dict = get_component_info(cline)
      config_dict["zil_status"] = logs_dict
    if match_type:
      #print "Matching type for %s"%cline
      if "raidz1" in cline:
        config_dict["type"] = "raidz1"
        #print "detected raidz1"
        match_components = True
        match_type = False
        #component_dict = get_component_info(cline)
        config_dict["type"] = "raidz1"
        config_dict["raid_or_mirror_status"] = component_dict
        continue
      elif "raidz2" in cline:
        config_dict["type"] = "raidz2"
        match_components = True
        match_type = False
        config_dict["raid_or_mirror_status"] = component_dict
        continue
      elif "mirror" in cline:
        config_dict["type"] = "mirror"
        match_type = False
        match_components = True
        config_dict["raid_or_mirror_status"] = component_dict
        continue
      else:
        #print "setting to normal"
        #print cline
        config_dict["type"] = "normal"
      match_components = True
      match_type = False
      #match_components = True
    if match_components:
      #print "Getting component info for %s"%cline
      match_type = False
      if "logs" in cline:
        match_logs = True
        continue
      component_dict = get_component_info(cline)
      if "replacing" in cline:
        replace_count = 2
        match_replace = True
        continue
      else:
        if match_replace:
          if replace_count > 0:
            replace_list.append(component_dict)
            replace_count = replace_count - 1
            if replace_count == 0:
              match_replace = False
          else:
            match_replace = False
          continue
      component_list.append(component_dict)
  config_dict["components"] = component_list
  if replace_list:
    config_dict["replacements"] = replace_list
  return config_dict

def get_pool_list():

  cmd = '/sbin/zpool status'
  ret, rc = command.execute_with_rc(cmd)
  if rc != 0:
    return None
  lines = command.get_output_list(ret)
  pool_list = []
  pool_dict = None
  errors_on = False
  scan_on = False
  config_on = False
  config_list = []
  for line in lines:
    #print line
    line = line.strip()
    res = re.match('^pool:\s*([\S]+)', line.strip())
    if res:
      scan_on = False
      if pool_dict != None:
        #New pool started so start processing the config_list and then clear it out
        config_dict = process_config_section(config_list)
        pool_dict["config"] = config_dict
        config_list = []
        pool_list.append(pool_dict)
      pool_dict = {}
      pool_dict["name"] = res.groups()[0]
    res = re.match('^state:\s*([\S]+)', line.strip())
    if res:
      #print "Matched state! %s"%line
      scan_on = False
      if pool_dict != None:
        pool_dict["state"] = res.groups()[0]
      continue
    res = re.match('^errors:\s*([\s\S]+)', line.strip())
    if res:
      #print "Matched errors! %s"%line
      scan_on = False
      config_on = False
      errors_on = True
      if pool_dict != None:
        pool_dict["errors"] = []
        pool_dict["errors"].append(res.groups()[0])
      continue
    res = re.match('^scan:\s*([\s\S]+)', line.strip())
    if res:
      #print "Matched scan! %s"%line
      if pool_dict != None:
        pool_dict["scan"] = []
        pool_dict["scan"].append(res.groups()[0])
        scan_on = True
      continue
    res = re.match('^config:', line.strip())
    if res:
      #print "Matched config! %s"%line
      scan_on = False
      config_on = True
      continue
    if scan_on and pool_dict and "scan" in pool_dict:
      pool_dict["scan"].append(line)
      continue
    if errors_on and pool_dict and "errors" in pool_dict:
      pool_dict["errors"].append(line)
      continue
    if config_on:
      config_list.append(line)
      continue
  if pool_dict:
    if config_list:
      config_dict = process_config_section(config_list)
      pool_dict["config"] = config_dict
    pool_list.append(pool_dict)
  return pool_list
  #print pool_list

def main():
  #with open('zfs.out', 'r') as f:
  #  output = f.readlines()
  pp = pprint.PrettyPrinter(indent=4)
  lis = get_pool_list()
  pp.pprint(lis)

  #for line in output:
  #  print line.strip()

if __name__ == '__main__':
  main()

