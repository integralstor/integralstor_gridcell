import zipfile, os, zlib, glob, socket, shutil, sys, logging
from os.path import basename

from integralstor_common import common, logger
from integralstor_gridcell import grid_ops

def get_patterns(log_dir):
  patterns = {}
  try:
    with open('%s/log_backup_patterns'%log_dir, 'r') as f:
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
    return None, 'Error retrieving log patters : %s'%str(e)
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

    zf = zipfile.ZipFile('/tmp/gridcell_logs_tmp.zip', 'w', zipfile.ZIP_DEFLATED)
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
    if not os.path.exists('%s/logs_backup/gridcells'%log_dir):
      os.makedirs('%s/logs_backup/gridcells'%log_dir)
    shutil.copy('/tmp/gridcell_logs_tmp.zip', '%s/logs_backup/gridcells/%s.zip'%(log_dir, hn))
    shutil.move('/tmp/gridcell_logs_tmp.zip', '/tmp/gridcell_logs.zip')
  except Exception, e:
    print e
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
    zf = zipfile.ZipFile('/tmp/grid_logs_tmp.zip', 'w', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk('%s/logs_backup/gridcells'%log_dir):
      for file in files:
        #print file
        zf.write(os.path.join(root, file), file)
    zf.close()
    if not os.path.exists('%s/logs_backup/grid'%log_dir):
      os.makedirs('%s/logs_backup/grid'%log_dir)
    shutil.copy('/tmp/grid_logs_tmp.zip', '%s/logs_backup/grid/grid_logs.zip'%log_dir)
    shutil.move('/tmp/grid_logs_tmp.zip', '/tmp/grid_logs.zip')
  except Exception, e:
    return False, 'Error zipping GRID logs : %s'%str(e)
  else:
    return True, None
  finally:
    if zf:
      zf.close()

def main():
  lg = None
  action = 'Log backup'
  try:
    lg, err = logger.get_script_logger('Log backup', '/var/log/integralstor/scripts.log', level = logging.DEBUG)

    if len(sys.argv) != 2 or sys.argv[1].strip() not in ['backup_gridcell_logs','backup_grid_logs']:
      raise Exception('Usage: python log_backup.py [backup_gridcell_logs|backup_grid_logs]')


    if sys.argv[1].strip() == 'backup_gridcell_logs':
      action = 'GRIDCell Log backup'
    else:
      action = 'Grid Log backup'

    str = '%s initiated.'%action
    logger.log_or_print(str, lg, level='info')

    if sys.argv[1].strip() == 'backup_gridcell_logs':
      ret, err = zip_gridcell_logs()
    else:
      active, err = grid_ops.is_active_admin_gridcell()
      if err:
        raise Exception(err)

      if not active:
        logger.log_or_print('Not active admin GRIDCell so exiting.', lg, level='info')
        sys.exit(0)
      ret, err = zip_grid_logs()
    if err:
      raise Exception(err)
  except Exception, e:
    st =  'Error backing up logs: %s'%e
    logger.log_or_print(st, lg, level='critical')
    sys.exit(-1)
  else:
    str = '%s completed.'%action
    logger.log_or_print(str, lg, level='info')
    sys.exit(0)

if __name__ == '__main__':
  print main()
