
import sys
import logging
from integralstor_utils import command, logger
from integralstor_gridcell import grid_ops


def salt_start():
    lg = None
    try:
        lg, err = logger.get_script_logger(
            'Conditional salt start completed', '/var/log/integralstor/scripts.log', level=logging.DEBUG)

        logger.log_or_print(
            'Conditional salt start initiated.', lg, level='info')
        pog, err = grid_ops.is_part_of_grid()
        logger.log_or_print('Part of grid : %s' % pog, lg, level='info')
        if err:
            raise Exception(err)
        if not pog:
            logger.log_or_print('Starting salt services.', lg, level='info')
            out, err = command.get_command_output(
                'service salt-minion start', False)
            if err:
                raise Exception(err)
            out, err = command.get_command_output(
                'service salt-master start', False)
            if err:
                raise Exception(err)
        else:
            logger.log_or_print(
                'Not starting salt services as I am part of the grid.', lg, level='info')
    except Exception, e:
        str = 'Error doing a conditional salt start : %s' % e
        logger.log_or_print(str, lg, level='critical')
        return False, str
    else:
        logger.log_or_print(
            'Conditional salt start completed.', lg, level='info')
        return True, None


if __name__ == '__main__':
    ret, err = salt_start()
    if not ret:
        sys.exit(-1)
    else:
        sys.exit(0)

# vim: tabstop=8 softtabstop=0 expandtab ai shiftwidth=4 smarttab
