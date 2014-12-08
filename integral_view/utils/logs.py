
import time, os, tempfile, shutil, glob


def _get_rotate_file_name(dir, file_name):
  #Returns to filename to which this one should be copied to

  try: 
    path  = os.path.normpath("%s/%s"%(dir, file_name))
  except Exception, e:
    raise Exception("Specified directory/file does not exist : %s"%str(e))

  if not os.path.exists(path):
    raise Exception("Specified directory/file does not exist : %s"%str(e))

  t = time.localtime()
  i = 1
  done = False

  while not done:
    #fn = "%s_%s_%d"%(file_name, time.strftime("%Y_%m_%d", t), i )
    fn = "%s_%d"%(file_name, int(time.time()) )
    path  = os.path.normpath("%s/%s"%(dir, fn))
    if not os.path.exists(path):
      done = True
    else:
      i = i+1

  return fn


def rotate_log(dir, file_name, initialize_list):
  #Given a directory and any file_name, copies out the current file to a rotated name and reinitialises the current file with the strings from initialize_list.

  fn = _get_rotate_file_name(dir, file_name)

  f = tempfile.NamedTemporaryFile(dir=dir)
  if initialize_list:
    for line in initialize_list:
      f.write(line)
    f.flush()

  dest_path  = os.path.normpath("%s/%s"%(dir, file_name))
  ffn = os.path.normpath("%s/%s"%(dir, fn))
  #First backup orig file
  shutil.copy(dest_path, ffn)
  #Now reinitialize the file
  shutil.copy(f.name, dest_path)
  f.close()
  return 0

def get_log_file_list(dir, file_name):

  path  = os.path.normpath("%s/%s"%(dir, file_name))
  list = os.listdir(dir)
  l = []
  if list:
    for f in list:
      if f == file_name:
        pass
      else:
        l.append(f)
  #list = glob.glob("%s_*"%path)
  l.sort(reverse=True)
  return l

def generate_display_log_file_list(l, file_name):
  # Given a list of all files, generate a list of dicts - each dict will have the display date and a list of file names for that date

  if not l:
    return None
  nl = []
  temp_dict = None
  temp_list = None
  if l:
    date_dict = {}
    for f in l:
      dt = f[len("%s_"%file_name):]
      s = time.strftime("%d %B %Y", time.localtime(float(dt)))
      if s in date_dict:
        td = {}
        td["file_name"] = f
        td["time"] =  time.strftime("%I:%M %p", time.localtime(float(dt)))
        temp_list.append(td)
      else:
        date_dict[s] = f
        if temp_dict:
          nl.append(temp_dict)
        temp_dict = {}
        temp_dict["date"] = s
        temp_list = []
        temp_dict["files"] = temp_list
        td = {}
        td["file_name"] = f
        td["time"] =  time.strftime("%I:%M %p", time.localtime(float(dt)))
        temp_list.append(td)
    #Now append the last temp_dict
    nl.append(temp_dict)
  return nl
  
  
def main():
  #rotate_log("/home/bkrram/Documents/software/fractal/gluster_admin/gluster_admin/devel/alerts", "alerts.log", ["----------"])
  #rotate_log("/home/bkrram/Documents/software/fractal/gluster_admin/gluster_admin/devel/audit_trail", "audit.log", None) 
  print get_log_file_list("/home/bkrram/Documents/software/fractal/gluster_admin/gluster_admin/devel/audit_trail", "audit.log") 

if __name__ == "__main__":
  main()
