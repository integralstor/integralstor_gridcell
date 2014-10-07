
import time, os, json, os.path, re, sys

path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '%s/../..'%path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'integral_view.settings'
#sys.path.insert(0, '/opt/fractal/gluster_admin')
#sys.path.insert(0, '/home/bkrram/Documents/software/Django-1.4.3/code/gluster_admin')
from django.conf import settings

class BatchException(Exception):

  msg = None

  def __init__(self, msg):
    self.msg = msg

  def __str__(self):
    return repr(self.msg)

def load_all_files(type):
  #Used to load all the info from all the files of type type (either "start" or "process")
  try: 
    batch_dir = settings.BATCH_COMMANDS_DIR
  except:
    batch_dir = "."
  files = os.listdir(os.path.normpath("%s/%s"%(batch_dir,type)))
  list = []
  for file in files:
    with open(os.path.normpath("%s/%s/%s"%(batch_dir, type, file))) as f:
      print "%s/%s/%s"%(batch_dir, type, file)
      d = json.load(f)
      list.append(d)
  return list

def load_specific_file(filename):

  # Return the json contents of the filename as the data structure
  try:
    batch_dir = settings.BATCH_COMMANDS_DIR
  except:
    batch_dir = "."
  f = None
  try:
    f = open(os.path.normpath("%s/in_process/%s"%(batch_dir, filename)))
  except IOError:
    pass
  if f:
    d = json.load(f)

  return d
