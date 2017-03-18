import salt.client
import os
import zipfile
import shutil
import socket
from os.path import basename
from integralstor_common import common, command

# Files go in the format of , path where the file exists, and the regex to match for the files
#files = ["/var/log/*message*","/var/log/*boot.log*","/var/log/nginx/*error.log*","/var/log/*smblog.vfs*","/var/log/*log.ctdb*","/var/log/*dmesg*"]
files = ["/var/log/*message*", "/var/log/*boot.log*",
         "/var/log/nginx/*error.log*", "/var/log/*smblog.vfs*", "/var/log/*dmesg*"]

folders = ["/var/log/glusterfs", "/var/log/samba",
           "/var/log/integralstor", "/var/log/salt", "/var/spool/mail"]

master_logs = [common.get_log_folder_path()[0]]


def get_logs(hostname=socket.getfqdn()):
    try:
        for logs in files:
            cmd = "cp -rf %s /tmp/logs" % logs
            ret, err = command.execute_with_rc(cmd, True)
            if err:
                raise Exception(err)
        for folder in folders:
            cmd = "cp -rf %s /tmp/logs" % folder
            ret, err = command.execute_with_rc(cmd, True)
            if err:
                raise Exception(err)
        if ("gridcell-pri" in hostname) or ("gridcell-sec" in hostname):
            for folder in master_logs:
                cmd = "cp -rf %s /tmp/logs" % folder
                ret, err = command.execute_with_rc(cmd, True)
                if err:
                    raise Exception(err)

    except Exception, e:
        return False, e
    else:
        return True, None


def zip_my_logs(hostname):
    try:
        log_path = "/tmp/logs/"
        status, err = get_logs()
        if os.path.isdir(log_path):
            zipdir(log_path, "/tmp/%s.zip" % hostname)
        else:
            with open("/tmp/logs/%s.zip" % hostname, "w") as f:
                f.write("Unable to get log file in path : %s" % log_path)
    except Exception, e:
        return False, e
    else:
        return True, None


def zipdir(path, name):
    ziph = zipfile.ZipFile(name, "w", zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(path):
        for file in files:
            #  The actual log files are being zipped
            # Making the zip keep the folder structure same instead of the
            # whole pth
            if "files" in root:
                basepath = root.split("files")[1]
                ziph.write(os.path.join(root, file),
                           os.path.join(basepath, file))
            else:
                ziph.write(os.path.join(root, file))
    ziph.close()


if __name__ == "__main__":
    try:
        hostname = socket.getfqdn()
        if os.path.isfile("/tmp/%s.zip" % hostname):
            os.remove("/tmp/%s.zip" % hostname)
         # Path where all the logs files will be collected
        path = "/tmp/logs/"
        # Cleanup the path to collect new log files
        if not os.path.isdir(path):
            os.mkdir(path)
        if not os.listdir(path) == []:
            shutil.rmtree(path)
            os.mkdir(path)
        status, err = zip_my_logs(hostname)
        if err:
            raise Exception(e)
        zipdir(path, "/tmp/%s.zip" % hostname)
    except Exception, e:
        print e

# vim: tabstop=8 softtabstop=0 expandtab ai shiftwidth=4 smarttab
