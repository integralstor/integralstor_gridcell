import zipfile, os, zlib, glob, socket, shutil, sys
from os.path import basename

from integralstor_common import common

def get_patterns(log_dir):
  patterns = {}
  try:
    with open('%s/patterns'%log_dir, 'r') as f:
      lines = f.readlines()
    if lines:
      for line in lines:
        comps = line.split()
        if comps and len(comps) == 2 and comps[0].strip() in ['files', 'directories']:
          type = comps[0].strip()
          if type not in patterns.keys():
            patterns[type] = []
          patterns[type].append(comps[1].strip())
  except Exception, e:
    None, 'Error retrieving log patters : %s'%str(e)
  else:
    return patterns, None

def zip_gridcell_logs():
  zf = None
  try:
    hn = socket.getfqdn()
    log_dir, err = common.get_log_folder_path()
    if err:
      raise Exception(err)
    patterns, err = get_patterns(log_dir)
    if err:
      raise Exception(err)

    zf = zipfile.ZipFile('/tmp/%s.zip'%hn, 'w', zipfile.ZIP_DEFLATED)
    if 'directories' in patterns.keys():
      for pattern in patterns['directories']:
        dirs = glob.glob(pattern)
        for dir in dirs:
          for root, dirs, files in os.walk(dir):
            for file in files:
              #print file
              zf.write(os.path.join(root, file))
    if 'files' in patterns.keys():
      for pattern in patterns['files']:
        files =  glob.glob(pattern)
        for file in files:
          #print file
          zf.write(file)
    zf.close()
    shutil.move('/tmp/%s.zip'%hn, '%s/logs_backup/gridcells/%s.zip'%(log_dir, hn))
  except Exception, e:
    return False, 'Error zipping GRIDCell logs : %s'%str(e)
  else:
    return True, None
  finally:
    if zf:
      zf.close()

def zip_grid_logs():
  zf = None
  try:
    log_dir, err = common.get_log_folder_path()
    if err:
      raise Exception(err)
    zf = zipfile.ZipFile('/tmp/grid_logs.zip', 'w', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk('%s/logs_backup/gridcells'%log_dir):
      for file in files:
        #print file
        zf.write(os.path.join(root, file), file)
    zf.close()
    shutil.move('/tmp/grid_logs.zip', '%s/logs_backup/grid/grid_logs.zip'%log_dir)
  except Exception, e:
    return False, 'Error zipping GRID logs : %s'%str(e)
  else:
    return True, None
  finally:
    if zf:
      zf.close()

def main():
  try:
    if len(sys.argv) != 2 or sys.argv[1].strip() not in ['backup_gridcell_logs','backup_grid_logs']:
      print 'Usage: python log_backup.py [backup_gridcell_logs|backup_grid_logs]'
      sys.exit(-1)
    if sys.argv[1].strip() == 'backup_gridcell_logs':
      ret, err = zip_gridcell_logs()
    else:
      ret, err = zip_grid_logs()
    if err:
      raise Exception(err)
  except Exception, e:
    print 'Error processing request : %s'%str(e)
    sys.exit(-1)
  else:
    sys.exit(0)

if __name__ == '__main__':
  print main()
