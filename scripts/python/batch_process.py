#!/usr/bin/python

import json, time, re, os, tempfile, shutil, sys 
from xml.etree import ElementTree

import fractalio
from fractalio import command, xml_parse, common, audit, lock

production = common.is_production()
batch_files_path = common.get_batch_files_path()
devel_files_path = common.get_devel_files_path()


def get_heal_count(cmd, type):
#Gets the number of files healed so far
  rl = []
  if not production:
    fn = "%s/heal_info.txt"%devel_files_path
    with open(fn, "r") as f:
      lines = f.readlines()
      #print lines
  else:
    try:
      r = None
      if type :
          cmd = cmd + " " + type
      r = command.execute(cmd)
      lines = []
      if r:
        lines = command.get_output_list(r)
    except Exception, e:
      return rl

  if lines:
    for line in lines:
      m = re.search("Number of entries:[\s]*([\d]+)", line)
      #print m
      if m:
        found = True
        #print line
        try:
         count = int(m.groups()[0])
        except Exception, e:
          return rl
          continue
        rl.append(count)
  #print rl
  return rl


def process_batch(d, file):
  #Process each batch file

  if not d:
    err = "Error: No JSON info in %s/%s"%(batch_files_path, file)
    return -1, err

  if not d["process"] in ["replace_sled", "volume_rebalance", "factory_defaults_reset"]:
    err = "Error! Unknown process in %s/%s"%(batch_files_path, file)
    return -1, err

  if not "start_time" in d:
    #Update when this process was started
    d["start_time"] =  time.strftime("%a %b %d %H:%M:%S %Y", time.localtime())

  if d["status"] != "In progress":
    d["status"] = "In progress"

  #ADD CODE HERE TO MOVE IT TO COMPLETED DIR IF STATUS IS COMPLETE

  #Not committed so process the file
  for cd in d["command_list"]:

    #Remove old err_msg because we are reprocessing
    cd.pop("err_msg", None)

    #Status codes explanation - 
    # 3 - complete
    # 0 - not yet run
    # 1 - in progress
    # -1 - error executing command

    if cd["status_code"] == 3:
      # Completed so skip to next command
      continue

    #Else failed or not done so do it 

    if cd["type"] == "volume_heal_full":
      #No XML output so do some dirty text processing.
      if production:
        try:
          r = None
          r = command.execute(cd["command"])
          lines = []
          if r:
            lines = command.get_output_list(r)
          else:
            cd["status_code"] = -1
            cd["err_msg"] = "Error executing volume heal command"
            # Stop executing more commands!
            break
        except Exception, e:
          cd["status_code"] = -1
          cd["err_msg"] = "Error executing volume heal command"
          # Stop executing more commands!
          break
      else:
        fn = "/opt/fractalio/devel/files/heal_full.txt"
        with open(fn, "r") as f:
          lines = f.readlines()

      #Now start processing output of command
      if lines:
        for line in lines:
          m = re.search("Launching Heal operation on volume [a-zA-Z_\-]* has been successful", line)
          #print m
          if m:
            #Successfully executed
            audit.audit(cd["type"], cd["desc"], 'Batch job')
            cd["status_code"] = 3
            break
        if cd["status_code"] != 3:
          # Stop executing more commands!
          cd["status_code"] = -1
          cd["err_msg"] = "Error executing volume heal. Got : %s"%line
          break
      else:
        #No output from command execution so flag error
        cd["status_code"] = -1
        cd["err_msg"] = "Volume heal did not seem to kick off properly. Please make sure the volume is started."
        # Stop executing more commands!
        break

    elif cd["type"] == "brick_delete":
      #Need to execute a shell command to remotely delete a brick.
      ret, rc = command.execute_with_rc(cd["command"])
      if rc == 0:
        cd["status_code"] = 3
      else:
        cd["status_code"] = -1
        cd["err_msg"] = "Error deleting the volume brick : %s %s"%(ret[0], ret[1])

    elif cd["type"] == "volume_heal_info":
      #No XML output so do some dirty text processing.
      l = get_heal_count(cd["command"], None)
      if l:
        total = 0
        for n in l:
          total += n
        cd["files_remaining"] = total
        if total > 0:
          cd["status_code"] = 1
        else:
          cd["status_code"] = 3

        l = get_heal_count(cd["command"], "healed")
        if l:
          total = 0
          for n in l:
            total += n
          cd["files_healed"] = total
        l = get_heal_count(cd["command"], "failed")
        if l:
          total = 0
          for n in l:
            total += n
          cd["files_failed"] = total
      else:
        # No heal count returned so dont know what happened - flag error
        cd["err_msg"] = "Could not get heal count"
        cd["status_code"] = -1

            
    else:
      #Commands that have valid XML outputs
      if not production:
        if cd["type"] == "add_brick":
          fn = "%s/add_brick.xml"%devel_files_path
        elif cd["type"] == "remove_brick_start":
          fn = "%s/remove_brick_start.xml"%devel_files_path
        elif cd["type"] == "remove_brick_status":
          fn = "%s/remove_brick_status.xml"%devel_files_path
        elif cd["type"] == "remove_brick_commit":
          fn = "%s/remove_brick_commit.xml"%devel_files_path
        elif cd["type"] == "rebalance_start":
          fn = "%s/rebalance_start.xml"%devel_files_path
        elif cd["type"] == "rebalance_status":
          fn = "%s/rebalance_status.xml"%devel_files_path
        elif cd["type"] == "replace_brick_commit":
          fn = "%s/replace_brick_commit.xml"%devel_files_path
        with open(fn, 'rt') as tf:
            tree = ElementTree.parse(tf)
      else:
        temp = tempfile.TemporaryFile()
        try:
          #print cd["command"]
          r = command.execute(cd["command"])
          #print r
          if r:
            #print "command = %s"%cd["command"]
            l = command.get_output_list(r)
            for line in l:
              temp.write(line)
            temp.seek(0)
            tree = ElementTree.parse(temp)
          else:
            cd["err_msg"] = "Error executing %s"%cd["command"]
            cd["status_code"] = -1
            print "error executing command = %s"%cd["command"]
        finally:
          temp.close()

      op_status = {}

      #Mark it as in progress
      cd["status_code"] = 1

      try :
        root = tree.getroot()
        op_status = xml_parse.get_op_status(root)
      except Exception, e:
        print "Error parsing xml output from %s"%cd["command"]
        print e
        cd["err_msg"] = "Error parsing xml output from %s"%cd["type"]
        cd["status_code"] = -1
        break

      if not op_status:
        cd["status_code"] = -1
        cd["err_msg"] = "Could not get status of command %s"%cd["command"]
        break
      if (not "op_ret" in op_status) or (not "op_errno" in op_status):
        cd["status_code"] = -1
        cd["err_msg"] = "Could not get opStatus or opErrno of command %s"%cd["command"]
        break
      if op_status["op_ret"] != 0 :
        cd["status_code"] = -1
        cd["err_msg"] = "Error executing %s. Returned op_ret %d. op_errno %d. op_errstr %s"%(cd["command"], op_status["op_ret"], op_status["op_errno"], op_status["op_errstr"])
        break

      # Come here only if successful

      if cd["type"] in ["add_brick", "remove_brick_start", "rebalance_start", "volume_heal_full"]:
        #One off command so
        #All ok so mark status as successful so it is not rerun
        audit.audit(cd["type"], cd["desc"], 'Batch job')
        cd["status_code"] = 3
        continue

      #Continue only for commands that need to be polled for status

      done = True
      if cd["type"] in ["remove_brick_status", "rebalance_status"]:

        if cd["type"] == "remove_brick_status":
          rootStr = "volRemoveBrick"
        else:
          rootStr = "volRebalance"

        nodes = tree.findall(".//%s/node"%rootStr)

        if nodes:
          for node in nodes:
            status = int(xml_parse.get_text(node, "status"))
            if status == 1:
              done = False
  
        node = tree.find(".//%s/aggregate"%rootStr)
  
        try :
          cd["files"] = int(xml_parse.get_text(node, "files"))
          cd["size"] = int(xml_parse.get_text(node, "size"))
        except Exception, e:
          #Trying to get only info so ok to fail
          pass

        # If the nodes signal done then confirm that the aggregate also says so - Quirk with gluster xml output
        if done:
          if node:
            try:
              status = int(xml_parse.get_text(node, "status"))
              if status == 1:
                done = False
            except Exception, e:
              pass

      if done:
        # Actually done so flag the command as having completed
        cd["status_code"] = 3
    if cd["status_code"] != 3:
      # Not done successfully so do not proceed to next command
      break

  completed = True
  for cd in d["command_list"]:
    if cd["status_code"] != 3:
      completed = False
      break

  if completed:
    d["status"] = "Completed" 

  #Write the updated json to a temp file and copy to prevent possible race read/write conditions?

  with open(os.path.normpath("%s/tmp_%s"%(batch_files_path, file)), "w+") as f1:
    #print 'writing json'
    json.dump(d, f1, indent=2)
    f1.flush()
    f1.close()
  shutil.move(os.path.normpath("%s/tmp_%s"%(batch_files_path, file)), os.path.normpath("%s/%s"%(batch_files_path, file)))

  
import atexit
atexit.register(lock.release_lock, 'batch_process')

def main():
  try :
    if not lock.get_lock('batch_process'):
      print 'Generate Status : Could not acquire lock. Exiting.'

    fl = os.listdir(os.path.normpath(batch_files_path))
    if fl:
      for file in fl:
        if not file.startswith("bp_"):
          #unknown file type so ignore
          continue
        else:
          with open(os.path.normpath("%s/%s"%(batch_files_path,file)), "r") as f:
            try :
              d = json.load(f)
              process_batch(d, file)
            except Exception, e:
              print "Error loading json content for %s/%s : %s"%(batch_files_path, file, e)
              continue
            finally:
              f.close()
    lock.release_lock('batch_process')
  except Exception, e:
    print "Error processing batch files : %s"%e
    sys.exit(-1)
  else:
    sys.exit(0)

if __name__ == '__main__':
  main()
