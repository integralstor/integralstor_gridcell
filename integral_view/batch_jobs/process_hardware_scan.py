import json, time, re, os, tempfile, shutil, sys 
from xml.etree import ElementTree


path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '%s/../..'%path)
os.environ['DJANGO_SETTINGS_MODULE']='integral_view.settings'

'''
if len(sys.argv) < 2:
  raise Exception("No settings.py path provided!")
sys.path.insert(0, sys.argv[1])
os.environ['DJANGO_SETTINGS_MODULE']='gluster_admin.settings'
import settings
'''

BASEPATH = settings.BATCH_COMMANDS_DIR
production = settings.PRODUCTION
from integral_view.utils import command, xml_parse, audit


def main():
  fl = os.listdir(os.path.normpath("%s/in_process"%BASEPATH))
  for fname in fl:
    print file
    if not fname.startswith("hs_"):
      #unknown file type so ignore
      continue
    else:
      with open(os.path.normpath("%s/in_process/%s"%(BASEPATH, fname)), "r") as f:
        try :
          d = json.load(f)
        except Exception, e:
          print "Error loading json content for %s/in_process/%s"%(BASEPATH, fname)
          print str(e)
          continue
        finally:
          f.close()
      if d["status"] != "Completed":
        process_hs(d, fname)

def process_hs(d, file):
  #Process each batch file
  print "processing %s"%file

  if not d:
    err = "Error: No JSON info in %s/in_process/%s"%(BASEPATH, file)
    return -1, err

  if d["process"] != "hardware_scan":
    err = "Error! Unknown process in %s/in_process/%s"%(BASEPATH, file)
    return -1, err

  if not "start_time" in d:
    #Update when this process was started
    d["start_time"] =  time.strftime("%a %b %d %H:%M:%S %Y", time.localtime())

  if d["status"] != "In progress":
    d["status"] = "In progress"

  update_batch_status(file, d)

  #ADD CODE HERE TO MOVE IT TO COMPLETED DIR IF STATUS IS COMPLETE

  #Not committed so process the file
  cmd = d["command"]
  ret, rc = command.execute_with_rc(cmd)
  if rc != 0:
    d["status"] = "Failed with error code %d"%rc
  else:
    d["status"] = "Completed"

  update_batch_status(file, d)

def update_batch_status(file, d):
  with open(os.path.normpath("%s/in_process/tmp_%s"%(BASEPATH, file)), "w+") as f1:
    json.dump(d, f1, indent=2)
    f1.flush()
    f1.close()
  shutil.move(os.path.normpath("%s/in_process/tmp_%s"%(BASEPATH, file)), os.path.normpath("%s/in_process/%s"%(BASEPATH, file)))


if __name__ == "__main__":
  main()
