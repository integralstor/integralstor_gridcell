#!/usr/bin/python

import json, time, re, os, tempfile, shutil, sys 
from xml.etree import ElementTree

from integralstor_common import command,common, audit, lock

from integralstor_gridcell import xml_parse



def get_heal_count(cmd, type):
  #Gets the number of files healed so far
  rl = []
  try:
    batch_files_path, err = common.get_batch_files_path()
    if err:
      raise Exception(err)
    devel_files_path, err = common.get_devel_files_path()
    r = None
    if type :
        cmd = cmd + " " + type
    r, err = command.execute(cmd)
    if err:
      raise Exception(err)
    lines = []
    if r:
      lines, err = command.get_output_list(r)
      if err:
        raise Exception(err)

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
  except Exception, e:
    return None, 'Error getting heal count : %s'%str(e)
  else:
    return rl, None


def process_batch(d, file):
  #Process each batch file

  try:
    print file
    batch_files_path, err = common.get_batch_files_path()
    if err:
      raise Exception(err)
    devel_files_path, err = common.get_devel_files_path()
    if not d:
      raise Exception("Error: No JSON info in %s/%s"%(batch_files_path, file))
  
    #if not d["process"] in ["replace_sled", "volume_rebalance", "factory_defaults_reset"]:
    #  raise Exception("Error! Unknown process in %s/%s"%(batch_files_path, file))
  
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
        try:
          r = None
          r, err = command.execute(cd["command"])
          if err:
            raise Exception(err)
          lines = []
          if r:
            lines, err = command.get_output_list(r)
            if err:
              raise Exception(err)
          else:
            raise Exception('')
  
          #Now start processing output of command
          if lines:
            for line in lines:
              m = re.search("Launching Heal operation on volume [a-zA-Z_\-]* has been successful", line)
              #print m
              if m:
                #Successfully executed
                ret, err = audit.audit(cd["type"], cd["desc"], 'Batch job')
                cd["status_code"] = 3
                break
            if cd["status_code"] != 3:
              # Stop executing more commands!
              raise Exception("Got : %s"%line)
          else:
            #No output from command execution so flag error
            raise Exception("Volume heal did not seem to kick off properly. Please make sure the volume is started.")
        except Exception, e:
          cd["status_code"] = -1
          cd["err_msg"] = "Error executing volume heal command : %s"%str(e)
          # Stop executing more commands!
          break
  
      elif cd["type"] == "brick_delete":
        #Need to execute a shell command to remotely delete a brick.
        try:
          (ret, rc), err = command.execute_with_rc(cd["command"])
          if rc == 0:
            cd["status_code"] = 3
          else:
            raise Exception("Error deleting the volume brick : %s %s"%(ret[0], ret[1]))
        except Exception, e:
          cd["status_code"] = -1
          cd["err_msg"] = "Error executing brick delete command : %s"%str(e)
          # Stop executing more commands!
          break
  
      elif cd["type"] == "volume_heal_info":
        try:
          #No XML output so do some dirty text processing.
          l, err = get_heal_count(cd["command"], None)
          if err:
            raise Exception(err)
          if l:
            total = 0
            for n in l:
              total += n
            cd["files_remaining"] = total
            if total > 0:
              cd["status_code"] = 1
            else:
              cd["status_code"] = 3
    
            l, err = get_heal_count(cd["command"], "healed")
            if err:
              raise Exception(err)
            if l:
              total = 0
              for n in l:
                total += n
              cd["files_healed"] = total
            l, err = get_heal_count(cd["command"], "failed")
            if err:
              raise Exception(err)
            if l:
              total = 0
              for n in l:
                total += n
              cd["files_failed"] = total
          else:
            # No heal count returned so dont know what happened - flag error
            raise Exception("Could not get heal count")
        except Exception, e:
          cd["status_code"] = -1
          cd["err_msg"] = "Error executing volume heal info command : %s"%str(e)
          # Stop executing more commands!
          break
  
            
      else:
        #Commands that have valid XML outputs
        temp = tempfile.TemporaryFile()
        try:
          print cd["command"]
          r, err = command.execute(cd["command"])
          if err:
            raise Exception("Error executing %s"%cd["command"])
          #print r
          if r:
            #print "command = %s"%cd["command"]
            l, err = command.get_output_list(r)
            if err:
              raise Exception(err)
            for line in l:
              temp.write(line)
            temp.seek(0)
            tree = ElementTree.parse(temp)
          else:
            raise Exception("Error executing %s"%cd["command"])
  
          op_status = {}
  
          #Mark it as in progress
          cd["status_code"] = 1
  
          root = tree.getroot()
          op_status, err = xml_parse.get_op_status(root)
          if err:
            raise Exception("Error parsing xml output from %s : %s"%(cd["type"]), err)
  
          if not op_status:
            raise Exception("Could not get status of command %s"%cd["command"])
          if (not "op_ret" in op_status) or (not "op_errno" in op_status):
            raise Exception("Could not get opStatus or opErrno of command %s"%cd["command"])
          if op_status["op_ret"] != 0 :
            raise Exception("Error executing %s. Returned op_ret %d. op_errno %d. op_errstr %s"%(cd["command"], op_status["op_ret"], op_status["op_errno"], op_status["op_errstr"]))
    
          # Come here only if successful
    
          if cd["type"] in ["add_brick", "remove_brick_start", "rebalance_start", "volume_heal_full"]:
            #One off command so
            #All ok so mark status as successful so it is not rerun
            ret, err = audit.audit(cd["type"], cd["desc"], 'Batch job')
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
                status_str, err = xml_parse.get_text(node, "status")
                if err:
                  raise Exception(err)
                status = int(status_str)
                if status == 1:
                  done = False
      
            node = tree.find(".//%s/aggregate"%rootStr)
      
            try :
              ret, err = xml_parse.get_text(node, "files")
              cd["files"] = int(ret)
              ret, err = xml_parse.get_text(node, "size")
              cd["size"] = int(ret)
            except Exception, e:
              #Trying to get only info so ok to fail
              pass
  
            # If the nodes signal done then confirm that the aggregate also says so - Quirk with gluster xml output
            if done:
              if node:
                try:
                  ret, err = xml_parse.get_text(node, "status")
                  status = int(ret)
                  if status == 1:
                    done = False
                except Exception, e:
                  pass
    
          if done:
            # Actually done so flag the command as having completed
            cd["status_code"] = 3
  
  
        except Exception, e:
          cd["status_code"] = -1
          cd["err_msg"] = "Error processing command : %s"%str(e)
          break
        finally:
          temp.close()

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

  except Exception, e:
    return False, 'Error processing batch : %s'%str(e)
  else:
    return True, None
  
import atexit
atexit.register(lock.release_lock, 'batch_process')

def main():
  try :
    batch_files_path, err = common.get_batch_files_path()
    if err:
      raise Exception(err)
    devel_files_path, err = common.get_devel_files_path()
    ret, err = lock.get_lock('batch_process')
    if err:
      raise Exception(err)
    if not ret:
      print 'Generate Status : Could not acquire lock. Exiting.'

    fl = os.listdir(os.path.normpath(batch_files_path))
    if fl:
      for file in fl:
        if not file.startswith("bp_"):
          #unknown file type so ignore
          continue
        else:
          with open(os.path.normpath("%s/%s"%(batch_files_path,file)), "r") as f:
            d = json.load(f)
            ret, err = process_batch(d, file)
            if err:
              print "Error loading json content for %s/%s : %s"%(batch_files_path, file, err)
              continue
    ret, err = lock.release_lock('batch_process')
    if err:
      raise Exception(err)
  except Exception, e:
    print "Error processing batch files : %s"%e
    sys.exit(-1)
  else:
    sys.exit(0)

if __name__ == '__main__':
  main()
