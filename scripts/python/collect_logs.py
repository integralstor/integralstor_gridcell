import salt.client
import os
import zipfile
import shutil
import socket
from os.path import basename
from integralstor_common import common, command
from integralstor_gridcell import grid_ops

local = salt.client.LocalClient()


def zipdir(path, name):
    ziph = zipfile.ZipFile(name, "w", zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))
    ziph.close()


if __name__ == "__main__":
    try:
        # Path where the zip files from all minions will be collected
        path = "/tmp/gridcell_logs/"
        if not os.path.isdir(path):
            os.mkdir(path)
        if not os.listdir(path) == []:
            shutil.rmtree(path)
            os.mkdir(path)

        minions, err = grid_ops.get_accepted_minions()
        if err:
            raise Exception(err)

        for minion in minions:
            # check if the minion is up or not.
            status = local.cmd(minion, "test.ping")

            if minion in status:
                status = local.cmd(minion, "cp.push", ["/tmp/%s.zip" % minion])
                # If no response from minion, log a message
                if not status[minion]:
                    with open("/tmp/gridcell_logs/%s.log" % minion, "a+") as f:
                        f.write(
                            "Could not get the log file from minion: %s. Check the minion logs for any possible errors." % minion)

            else:
                with open("/tmp/gridcell_logs/%s.log" % minion, "a+") as f:
                    f.write(
                        "Minion %s did not respond. Minion possibly down." % minion)

            log_path = "/var/cache/salt/master/minions/%s/files/tmp/%s.zip" % (
                minion, minion)
            cmd = "cp -rf %s %s" % (log_path, path)
            ret, err = command.execute_with_rc(cmd, True)
            if err:
                raise Exception(err)
        if os.path.isdir(path):
            zipdir(path, "/tmp/gridcell.zip")

    except Exception, e:
        print e

# vim: tabstop=8 softtabstop=0 expandtab ai shiftwidth=4 smarttab
