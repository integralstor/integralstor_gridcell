
import json, os

import fractalio
from fractalio import common

batch_dir = common.get_batch_files_path()


def load_all_files():
  files = os.listdir(os.path.normpath("%s"%batch_dir))
  list = []
  for file in files:
    with open(os.path.normpath("%s/%s"%(batch_dir, file))) as f:
      print "%s/%s"%(batch_dir, file)
      d = json.load(f)
      list.append(d)
  return list

def load_specific_file(filename):

  # Return the json contents of the filename as the data structure
  f = None
  try:
    f = open(os.path.normpath("%s/%s"%(batch_dir, filename)))
  except IOError:
    pass
  if f:
    d = json.load(f)

  return d


'''
class BatchException(Exception):

  msg = None

  def __init__(self, msg):
    self.msg = msg

  def __str__(self):
    return repr(self.msg)
'''
