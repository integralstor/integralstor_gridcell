import salt.client
import salt.wheel

import sys
from integralstor_utils import config


def clear_minions():
    try:
        master, err = config.get_salt_master_config()
        if err:
            raise Exception(err)
        opts = salt.config.master_config(master)
        wheel = salt.wheel.Wheel(opts)
        keys = wheel.call_func('key.list_all')
        minions = keys['minions']
        minion_list = []
        if minions:
            print "The following GRIDCells are currently connected :"
            for i, minion in enumerate(minions):
                print "%d. %s" % (i + 1, minion)
            done = False
            while not done:
                node_list_str = raw_input(
                    "Select the GRIDCells that you would like to remove (Enter a comma separated list of the numbers) :")
                if node_list_str:
                    node_list = node_list_str.split(',')
                    if node_list:
                        error = False
                        for node_num_str in node_list:
                            try:
                                node_num = int(node_num_str)
                            except Exception, e:
                                print "Please enter only a comma separated list of numbers"
                                error = True
                                break
                        if not error:
                            done = True
                        if done:
                            for node_num in node_list:
                                # minion_list.append(minions[int(node_num)-1])
                                print "Removing GRIDCell %s" % minions[int(node_num) - 1]
                                wheel.call_func('key.delete', match=(
                                    '%s' % minions[int(node_num) - 1]))
                else:
                    print "Please enter a comma separated list of numbers"
            # print 'selected minions : ', minion_list
        else:
            print "No connected GRIDCells detected."
    except Exception, e:
        print "Error clearing minions%s" % e
        return -1
    else:
        return 0


if __name__ == '__main__':
    rc = clear_minions()
    sys.exit(rc)

# vim: tabstop=8 softtabstop=0 expandtab ai shiftwidth=4 smarttab
