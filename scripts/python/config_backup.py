import zipfile
import os
import zlib
import glob
import socket
import shutil
import sys
import logging
from os.path import basename

from integralstor_common import common, logger


def zip_gridcell_gluster_config():
    zf = None
    try:
        hn = socket.getfqdn()
        config_dir, err = common.get_config_dir()
        if err:
            raise Exception(err)

        zf = zipfile.ZipFile('/tmp/gluster_config_%s.zip' %
                             hn, 'w', zipfile.ZIP_DEFLATED)
        for root, dirs, files in os.walk('/var/lib/glusterd'):
            for file in files:
                # print file
                zf.write(os.path.join(root, file))
        zf.close()
        if not os.path.exists('%s/config_backup/gridcells/' % config_dir):
            os.makedirs('%s/config_backup/gridcells/' % config_dir)
        shutil.move('/tmp/gluster_config_%s.zip' %
                    hn, '%s/config_backup/gridcells/%s.zip' % (config_dir, hn))
    except Exception, e:
        return False, 'Error zipping GRIDCell gluster configuration : %s' % str(e)
    else:
        return True, None
    finally:
        if zf:
            zf.close()


def zip_grid_gluster_config():
    zf = None
    try:
        config_dir, err = common.get_config_dir()
        if err:
            raise Exception(err)
        zf = zipfile.ZipFile('/tmp/grid_gluster_config.zip',
                             'w', zipfile.ZIP_DEFLATED)
        for root, dirs, files in os.walk('%s/config_backup/gridcells' % config_dir):
            for file in files:
                # print file
                zf.write(os.path.join(root, file), file)
        zf.close()
        if not os.path.exists('%s/config_backup/grid' % log_dir):
            os.makedirs('%s/config_backup/grid' % log_dir)
        shutil.move('/tmp/grid_gluster_config.zip',
                    '%s/config_backup/grid/gluster_config.zip' % log_dir)
    except Exception, e:
        return False, 'Error zipping GRID gluster config : %s' % str(e)
    else:
        return True, None
    finally:
        if zf:
            zf.close()


def main():
    lg = None
    action = 'Config backup'
    try:
        lg, err = logger.get_script_logger(
            'Config backup', '/var/log/integralstor/scripts.log', level=logging.DEBUG)

        if len(sys.argv) != 2 or sys.argv[1].strip() not in ['backup_gridcell_config', 'backup_grid_config']:
            raise Exception(
                'Usage: python config_backup.py [backup_gridcell_config|backup_grid_config]')

        if sys.argv[1].strip() == 'backup_gridcell_config':
            action = 'GRIDCell config backup'
        else:
            action = 'Grid config backup'
        str = '%s initiated.' % action
        logger.log_or_print(str, lg, level='info')

        if sys.argv[1].strip() == 'backup_gridcell_config':
            ret, err = zip_gridcell_gluster_config()
        else:
            ret, err = zip_grid_gluster_config()
        if err:
            raise Exception(err)
    except Exception, e:
        st = 'Error backing up config: %s' % e
        logger.log_or_print(st, lg, level='critical')
        sys.exit(-1)
    else:
        str = '%s completed.' % action
        logger.log_or_print(str, lg, level='info')
        sys.exit(0)


if __name__ == '__main__':
    print main()

# vim: tabstop=8 softtabstop=0 expandtab ai shiftwidth=4 smarttab
