
import socket
import time

from django.conf import settings
import django
import django.template

import integral_view
from integral_view.forms import trusted_pool_setup_forms, gridcell_management_forms
from integral_view.utils import iv_logging

import integralstor_gridcell
from integralstor_gridcell import gluster_volumes, system_info, grid_ops, gluster_trusted_pools
from integralstor_utils import audit, lock, config, scheduler_utils

import salt.client


def view_gridcells(request):
    return_dict = {}
    try:
        return_dict['base_template'] = "gridcell_base.html"
        return_dict["page_title"] = 'View GRIDCells'
        return_dict['tab'] = 'gridcell_list_tab'
        return_dict["error"] = 'Error loading GRIDCells information'

        gluster_lck, err = lock.get_lock('gluster_commands')
        if err:
            raise Exception(err)

        if not gluster_lck:
            raise Exception(
                'This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')

        if 'ack' in request.GET:
            if request.REQUEST['ack'] == 'added_to_storage_pool':
                return_dict['ack_message'] = 'Successfully added GRIDCell to the storage pool'
            elif request.REQUEST['ack'] == 'removed_from_grid':
                return_dict['ack_message'] = 'Successfully removed GRIDCell from the grid.'
            elif request.REQUEST['ack'] == 'replaced_gridcell':
                return_dict['ack_message'] = 'A GRIDCell replacement batch process has been scheduled. Please view the "Batch processes" screen to check the status'

        # Get the system info dict.
        si, err = system_info.load_system_config()
        if err:
            raise Exception(err)
        if not si:
            raise Exception('Could not obtain system information')
        return_dict['system_info'] = si

        # Get the list of gridcells that can be removed from the storage pool.
        # Can be removed if its not the local node(we need it to be part of the
        # pool to run integralview!), its not the primary or secondary and if
        # it is part of the storage pool and does not have any volumes.
        rnl = []
        anl = []

        admin_gridcells, err = grid_ops.get_admin_gridcells()
        if err:
            raise Exception(err)
        return_dict['admin_gridcells'] = admin_gridcells

        for hostname in si.keys():
            ret, err = gluster_trusted_pools.can_remove_gridcell_from_storage_pool(
                hostname, admin_gridcells, si)
            if err:
                raise Exception(err)
            if ret:
                rnl.append(hostname)
            ret, err = gluster_trusted_pools.can_add_gridcell_to_storage_pool(
                hostname, si)
            if err:
                raise Exception(err)
            if ret:
                anl.append(hostname)
        return_dict['gluster_addable_gridcells'] = anl
        return_dict['gluster_removable_gridcells'] = rnl

        # Get the list of gridcells that have not yet been pulled into salt
        pending_minions, err = grid_ops.get_pending_minions()
        if err:
            raise Exception(err)
        if pending_minions:
            return_dict['pending_minions'] = pending_minions

        return django.shortcuts.render_to_response('view_gridcells.html', return_dict, context_instance=django.template.context.RequestContext(request))
    except Exception, e:
        s = str(e)
        if "Another transaction is in progress".lower() in s.lower():
            return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
        else:
            return_dict["error_details"] = "An error occurred when processing your request : %s" % s
        return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
    finally:
        lock.release_lock('gluster_commands')


def view_gridcell(request):
    return_dict = {}
    try:
        return_dict['base_template'] = "gridcell_base.html"
        return_dict["page_title"] = 'View GRIDCell information'
        return_dict['tab'] = 'gridcell_list_tab'
        return_dict["error"] = 'Error loading GRIDCells information'
        return_dict['tab'] = 'gridcell_list_tab'

        if 'gridcell_name' not in request.REQUEST:
            raise Exception('Invalid request. Please use the menus.')
        gridcell_name = request.REQUEST['gridcell_name']

        if 'ack' in request.GET:
            if request.REQUEST['ack'] == 'disk_blink':
                return_dict['ack_message'] = 'Successfully activated the disk LED on GRIDCell %s' % gridcell_name
            elif request.REQUEST['ack'] == 'disk_unblink':
                return_dict['ack_message'] = 'Successfully deactivated the disk LED on GRIDCell %s' % gridcell_name

        gluster_lck, err = lock.get_lock('gluster_commands')
        if err:
            raise Exception(err)

        if not gluster_lck:
            raise Exception(
                'This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')

        si, err = system_info.load_system_config()
        if err:
            raise Exception(err)
        if not si:
            raise Exception('Could not obtain system information')

        admin_gridcells, err = grid_ops.get_admin_gridcells()
        if err:
            raise Exception(err)
        return_dict['admin_gridcells'] = admin_gridcells

        return_dict['system_info'] = si
        return_dict['gridcell_info'] = si[gridcell_name]
        if si[gridcell_name]['errors']:
            print si[gridcell_name]['errors']

        ret, err = gluster_trusted_pools.can_remove_gridcell_from_storage_pool(
            gridcell_name, admin_gridcells, si)
        if err:
            raise Exception(err)
        return_dict['can_remove_from_trusted_pool'] = ret

        if si[gridcell_name]['node_status'] == -1:
            raise Exception(
                'GRIDCells details cannot be loaded as the GRIDCell seems to be down.')

        ret, err = gluster_trusted_pools.can_add_gridcell_to_storage_pool(
            gridcell_name, si)
        if err:
            raise Exception(err)
        return_dict['can_add_to_trusted_pool'] = ret

        # Figure out whether to callout errors for each component in the
        # template!
        if 'disks' in si[gridcell_name] and si[gridcell_name]['disks']:
            for sn, disk in si[gridcell_name]['disks'].items():
                pos = disk['scsi_info'][0] * 6 + disk['scsi_info'][2]
                # print pos, sn, disk['scsi_info']
                disk['chassis_pos_indicator'] = pos

        if (si[gridcell_name]['load_avg']['5_min'] > si[gridcell_name]['load_avg']['cpu_cores']) or (si[gridcell_name]['load_avg']['15_min'] > si[gridcell_name]['load_avg']['cpu_cores']):
            return_dict['flag_cpu'] = True
        for if_name, if_dict in si[gridcell_name]['interfaces'].items():
            if if_dict['status'].lower() != 'up':
                return_dict['flag_interfaces'] = True
                break
        for ipmi_info in si[gridcell_name]['ipmi_status']:
            if ipmi_info['status'].lower() != 'ok':
                return_dict['flag_ipmi'] = True
                break
        for sn, service_info in si[gridcell_name]['services'].items():
            if sn.lower() == 'nfs':
                continue
            if service_info[0] != 0:
                return_dict['flag_services'] = True
                break
        if si[gridcell_name]['in_cluster'] and si[gridcell_name]['cluster_status'] != 1:
            return_dict['flag_gluster_ctdb'] = True

        '''
    #Commenting out as we wont use CTDB for this build
    if 'ctdb_status' in si[gridcell_name] and si[gridcell_name]['ctdb_status'].lower() != 'ok':
      return_dict['flag_gluster_ctdb'] = True
    '''

        for did, disk_info in si[gridcell_name]['disks'].items():
            # print did, disk_info['status'].lower()
            if disk_info['status'] and disk_info['status'].lower() not in ['passed', 'ok']:
                return_dict['flag_disks'] = True
                break
        for pool in si[gridcell_name]['pools']:
            if pool['config']['pool']['root']['status']['state'].lower() != 'online':
                return_dict['flag_pools'] = True
                break

        return_dict['services'] = si[gridcell_name]['services']
        return_dict['gridcell_name'] = gridcell_name
        return django.shortcuts.render_to_response('view_gridcell.html', return_dict, context_instance=django.template.context.RequestContext(request))
    except Exception, e:
        s = str(e)
        if "Another transaction is in progress".lower() in s.lower():
            return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
        else:
            return_dict["error_details"] = "An error occurred when processing your request : %s" % s
        return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
    finally:
        lock.release_lock('gluster_commands')


def scan_for_new_gridcells(request):

    return_dict = {}
    try:
        gluster_lck, err = lock.get_lock('gluster_commands')
        if err:
            raise Exception(err)

        if not gluster_lck:
            raise Exception(
                'This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')

        return_dict['base_template'] = "gridcell_base.html"
        return_dict["page_title"] = 'Add GRIDCells to grid'
        return_dict['tab'] = 'gridcell_list_tab'
        return_dict["error"] = 'Error adding new GRIDCells to grid'

        pending_minions, err = grid_ops.get_pending_minions()
        if err:
            raise Exception(err)

        url = 'add_gridcells_to_grid_form.html'
        if request.method == 'GET':
            # Return a list of new nodes available to be pulled into the grid
            if pending_minions:
                form = gridcell_management_forms.AddGridcellsForm(
                    pending_minions_list=pending_minions)
                return_dict["form"] = form
            else:
                return_dict["no_new_gridcells"] = True
        else:
            form = gridcell_management_forms.AddGridcellsForm(
                request.POST, pending_minions_list=pending_minions)
            if form.is_valid():
                # print 'form valid'
                # User has chosen some gridcells to be added so add them.
                cd = form.cleaned_data
                admin_gridcells, err = grid_ops.get_admin_gridcells()
                if err:
                    raise Exception(err)
                (success, failed), errors = grid_ops.add_gridcells_to_grid(
                    request.META, cd["gridcells"], admin_gridcells)
                # print success, failed, errors
                url = 'add_gridcells_to_grid_result.html'
                return_dict["success"] = success
                return_dict["failed"] = failed
                return_dict["errors"] = errors

        return django.shortcuts.render_to_response(url, return_dict, context_instance=django.template.context.RequestContext(request))
    except Exception, e:
        s = str(e)
        if "Another transaction is in progress".lower() in s.lower():
            return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
        else:
            return_dict["error"] = "An error occurred when processing your request : %s" % s
        return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
    finally:
        lock.release_lock('gluster_commands')


def remove_a_gridcell_from_grid(request):
    return_dict = {}
    try:
        gluster_lck, err = lock.get_lock('gluster_commands')
        if err:
            raise Exception(err)

        if not gluster_lck:
            raise Exception(
                'This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')

        if 'gridcell_name' not in request.REQUEST:
            raise Exception('Invalid request. Please use the menus.')
        return_dict['base_template'] = "gridcell_base.html"
        return_dict["page_title"] = 'Remove a GRIDCell from the grid'
        return_dict['tab'] = 'gridcell_list_tab'
        return_dict["error"] = 'Error removing GRIDCell from the grid.'
        gridcell_name = request.REQUEST.get('gridcell_name')
        return_dict['gridcell_name'] = gridcell_name
        if request.method == "GET":
            return django.shortcuts.render_to_response("remove_gridcell_from_grid_conf.html", return_dict, context_instance=django.template.context.RequestContext(request))
        if request.method == "POST":
            ret, err = grid_ops.remove_a_gridcell_from_grid(gridcell_name)
            if err:
                raise Exception(err)

            audit_str = "Removed GRIDCell %s from the grid." % (gridcell_name)
            audit.audit("remove_gridcell_from_grid", audit_str, request)
            return django.http.HttpResponseRedirect('/view_gridcells?ack=removed_from_grid')
    except Exception, e:
        s = str(e)
        if "Another transaction is in progress".lower() in s.lower():
            return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
        else:
            return_dict["error"] = "An error occurred when processing your request : %s" % s
        return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
    finally:
        lock.release_lock('gluster_commands')


def add_a_gridcell_to_storage_pool(request):
    """ Used to add a gridcell to the trusted pool"""

    return_dict = {}
    try:
        gluster_lck, err = lock.get_lock('gluster_commands')
        if err:
            raise Exception(err)

        if not gluster_lck:
            raise Exception(
                'This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')

        return_dict['base_template'] = "gridcell_base.html"
        return_dict["page_title"] = 'Add a GRIDCell to the storage pool'
        return_dict['tab'] = 'gridcell_list_tab'
        return_dict["error"] = 'Error adding a GRIDCell to the storage pool'

        error_list = []

        if 'gridcell_name' not in request.REQUEST:
            raise Exception('Invalid request. Please try using the menus')
        gridcell_name = request.REQUEST['gridcell_name']

        si, err = system_info.load_system_config()
        if err:
            raise Exception(err)
        return_dict['system_info'] = si

        # Get list of possible GRIDCells that are available
        nl, err = gluster_trusted_pools.get_gridcells_not_in_trusted_pool(si)
        if err:
            raise Exception(err)
        if nl:
            anl = []
            for n in nl:
                anl.append(n['hostname'])
            if not anl or gridcell_name not in anl:
                raise Exception(
                    'The specified GRIDCell cannot be added to the storage grid. This could be because it is unhealthy or because it is already part of the grid')

        d, errors = grid_ops.add_a_gridcell_to_storage_pool(si, gridcell_name)
        if errors:
            raise Exception(errors)
        if d:
            if ("op_status" in d) and d["op_status"]["op_ret"] == 0:
                audit.audit("add_storage", 'Added GRIDCell %s to the storage pool' %
                            gridcell_name, request)
            else:
                err = 'Operation failed : Error number : %s, Error : %s, Output : %s, Additional info : %s' % (
                    d['op_status']['op_errno'], d['op_status']['op_errstr'], d['op_status']['output'], d['op_status']['error_list'])
                raise Exception(err)
        else:
            raise Exception(
                'Could not add the GRIDCell %s to the grid.' % gridcell_name)

        return django.http.HttpResponseRedirect('/view_gridcells?ack=added_to_storage_pool')

    except Exception, e:
        s = str(e)
        if "Another transaction is in progress".lower() in s.lower():
            return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
        else:
            return_dict["error_details"] = "An error occurred when processing your request : %s" % s
        return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
    finally:
        lock.release_lock('gluster_commands')


def remove_a_gridcell_from_storage_pool(request):

    return_dict = {}
    try:
        gluster_lck, err = lock.get_lock('gluster_commands')
        if err:
            raise Exception(err)

        if not gluster_lck:
            raise Exception(
                'This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')

        return_dict['base_template'] = "gridcell_base.html"
        return_dict["page_title"] = 'Remove a GRIDCell from the storage pool'
        return_dict['tab'] = 'gridcell_list_tab'
        return_dict["error"] = 'Error removing a GRIDCell from the storage pool'

        si, err = system_info.load_system_config()
        if err:
            raise Exception(err)

        if request.method == "GET":
            if 'gridcell_name' not in request.GET:
                raise Exception('GRIDCell not chosen. Please use the menus')
            return_dict['gridcell_name'] = request.GET['gridcell_name']
            url = 'remove_gridcell_from_storage_pool_conf.html'

        else:
            if 'gridcell_name' not in request.POST:
                raise Exception('GRIDCell not specified. Please use the menus')
            gridcell_name = request.POST['gridcell_name']
            d, error = grid_ops.remove_a_gridcell_from_storage_pool(
                si, gridcell_name)
            # if error:
            #  raise Exception(error)
            return_dict['gridcell_name'] = gridcell_name
            return_dict['error'] = error
            return_dict['result_dict'] = d
            if not error:
                audit_str = "Removed GRIDCell from the storage pool %s" % gridcell_name
                audit.audit("remove_storage", audit_str,
                            request)
            url = 'remove_gridcell_from_storage_pool_result.html'

        #return_dict['form'] = form
        if settings.APP_DEBUG:
            return_dict['app_debug'] = True
        return django.shortcuts.render_to_response(url, return_dict, context_instance=django.template.context.RequestContext(request))
    except Exception, e:
        s = str(e)
        if "Another transaction is in progress".lower() in s.lower():
            return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
        else:
            return_dict["error_details"] = "An error occurred when processing your request : %s" % s
        return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
    finally:
        lock.release_lock('gluster_commands')

# COMPLETE THIS!!!!!


def replace_gridcell(request):

    return_dict = {}
    try:
        gluster_lck, err = lock.get_lock('gluster_commands')
        if err:
            raise Exception(err)

        if not gluster_lck:
            raise Exception(
                'This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')

        return_dict['base_template'] = "gridcell_base.html"
        return_dict["page_title"] = 'Replace a GRIDCell'
        return_dict['tab'] = 'gridcell_list_tab'
        return_dict["error"] = 'Error replacing a GRIDCell'

        form = None

        # Get info about all the volumes so we can find out which ones reside
        # on this gridcell
        vil, err = gluster_volumes.get_basic_volume_info_all()
        if err:
            raise Exception(err)

        # Get the system info dict so we can display the potential list of
        # replacement gridcells
        si, err = system_info.load_system_config()
        if err:
            raise Exception(err)
        if not si:
            raise Exception('Could not load system information')

        return_dict['system_config_list'] = si

        d, err = system_info.get_replacement_node_info(si, vil)
        if err:
            raise Exception(err)
        if not d:
            raise Exception("There are no GRIDCells eligible to be replaced.")

        if not d["src_node_list"]:
            raise Exception("There are no GRIDCells eligible to be replaced.")
        if not d["dest_node_list"]:
            raise Exception(
                "There are no eligible replacement destination GRIDCells.")

        return_dict["src_node_list"] = d["src_node_list"]
        return_dict["dest_node_list"] = d["dest_node_list"]
        #assert False

        if request.method == "GET":
            form = volume_management_forms.ReplaceNodeForm(
                d["src_node_list"], d["dest_node_list"])
            return_dict["form"] = form
            return_dict["supress_error_messages"] = True
            # print "form errors ----->"
            # print form.errors
            return django.shortcuts.render_to_response('replace_node_choose_node.html', return_dict, context_instance=django.template.context.RequestContext(request))
        else:
            if "conf" in request.POST:
                form = volume_management_forms.ReplaceNodeConfForm(
                    request.POST)
                if form.is_valid():
                    cd = form.cleaned_data

                    src_node = cd["src_node"]
                    dest_node = cd["dest_node"]

                    vol_list, err = gluster_volumes.get_volumes_on_node(
                        src_node, vil)
                    if err:
                        raise Exception(err)
                    client = salt.client.LocalClient()
                    revert_list = []
                    if vol_list:
                        for vol in vol_list:
                            vol_dict, err = gluster_volumes.get_basic_volume_info(
                                vil, vol)
                            if err:
                                raise Exception(err)
                            # Get the brick path and the data set name
                            if 'bricks' in vol_dict and vol_dict['bricks']:
                                for brick_list in vol_dict['bricks']:
                                    for brick in brick_list:
                                        d, err = gluster_volumes.get_components(
                                            brick)
                                        if err:
                                            raise Exception(err)
                                        if not d:
                                            raise Exception(
                                                "Error decoding the brick for the specified volume. Brick name : %s " % brick)
                                        if d['host'] != src_node:
                                            continue
                                        # Found the brick on the src node so
                                        # now proceed
                                        dataset_cmd = 'zfs create %s/%s/%s' % (
                                            d['pool'], d['ondisk_storage'], vol.strip())
                                        revert_list = [
                                            'zfs destroy %s/%s/%s' % (d['pool'], d['ondisk_storage'], vol.strip())]
                                        # print dataset_cmd
                                        r1 = client.cmd(
                                            dest_node, 'cmd.run_all', [dataset_cmd])
                                        errors = ''
                                        if r1:
                                            for node, ret in r1.items():
                                                print ret
                                                if ret["retcode"] != 0:
                                                    errors += ", Error creating the underlying storage brick on %s" % node
                                                    print errors
                                        if errors:
                                            print 'Reverting. Executing : ', revert_list
                                            r1 = client.cmd(
                                                dest_node, 'cmd.run_all', revert_list)
                                            if r1:
                                                for node, ret in r1.items():
                                                    print ret
                                                    if ret["retcode"] != 0:
                                                        errors += ", Error removing the underlying storage brick on %s" % node
                                                        print errors
                                            raise Exception(errors)

                        d, err = gluster_batch.create_replace_command_file(
                            si, vol_list, src_node, dest_node)
                        # print d, err
                        if err or (d and "error" in d):
                            if revert_list:
                                # Undo the creation of the datasets
                                for dsr_cmd in revert_list:
                                    r1 = client.cmd(
                                        dest_node, 'cmd.run_all', [dsr_cmd])
                                    if r1:
                                        for node, ret in r1.items():
                                                # print ret
                                            if ret["retcode"] != 0:
                                                errors += " , Error undoing the creation of the underlying storage brick on %s" % dest_node
                                                d["error"].append(errors)
                            if err:
                                raise Exception(err)
                            elif d and 'error' in d:
                                raise Exception(
                                    "Error initiating replace : %s" % d["error"])
                            else:
                                raise Exception(
                                    'Error creating the replace batch command file')
                        else:
                            ret, err = audit.audit("replace_node", "Scheduled replacement of GRIDCell %s with GRIDCell %s" % (
                                src_node, dest_node), request)
                            if err:
                                raise Exception(err)
                            return django.http.HttpResponseRedirect('/view_gridcells?ack=replaced_gridcell')
                    else:
                        raise Exception(
                            'No volumes found on the source GRIDCell')
                else:
                    # Invalid conf form
                    raise Exception('Invalid request. Please try again.')
            else:
                form = volume_management_forms.ReplaceNodeForm(
                    request.POST, src_node_list=d["src_node_list"], dest_node_list=d["dest_node_list"])
                if form.is_valid():
                    cd = form.cleaned_data
                    src_node = cd["src_node"]
                    dest_node = cd["dest_node"]
                    return_dict["src_node"] = src_node
                    return_dict["dest_node"] = dest_node
                    return django.shortcuts.render_to_response('replace_node_conf.html', return_dict, context_instance=django.template.context.RequestContext(request))
                else:
                    return_dict["form"] = form
                    return django.shortcuts.render_to_response('replace_node_choose_node.html', return_dict, context_instance=django.template.context.RequestContext(request))
    except Exception, e:
        s = str(e)
        if "Another transaction is in progress".lower() in s.lower():
            return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
        else:
            return_dict["error_details"] = "An error occurred when processing your request : %s" % s
        return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
    finally:
        lock.release_lock('gluster_commands')


def identify_disk(request):
    return_dict = {}
    try:
        return_dict['base_template'] = "gridcell_base.html"
        return_dict['tab'] = 'gridcell_list_tab'
        return_dict["page_title"] = 'Identify a disk in a GRIDCell'
        return_dict["error"] = 'Error identifying a disk in a GRIDCell'
        if 'gridcell_name' not in request.REQUEST or 'action' not in request.REQUEST or 'hw_platform' not in request.REQUEST:
            raise Exception('Invalid request. Please use the menus.')
        if request.REQUEST['hw_platform'] not in ['dell']:
            raise Exception(
                'This operation is not supported on your hardware platform')
        gridcell_name = request.REQUEST['gridcell_name']
        action = request.REQUEST['action']
        hw_platform = request.REQUEST['hw_platform']
        if request.REQUEST['hw_platform'] == 'dell':
            if 'controller' not in request.REQUEST or 'target_id' not in request.REQUEST or 'channel' not in request.REQUEST or 'enclosure_id' not in request.REQUEST:
                raise Exception('Invalid request. Please use the menus.')
            client = salt.client.LocalClient()
            rc = client.cmd(gridcell_name, 'integralstor.disk_action', kwarg={'controller': request.REQUEST['controller'], 'target_id': request.REQUEST[
                            'target_id'], 'channel': request.REQUEST['channel'], 'enclosure_id': request.REQUEST['enclosure_id'], 'action': request.REQUEST['action']})
            # print rc
            if rc:
                for node, ret in rc.items():
                    # print ret
                    if not ret[0]:
                        error = 'Error performing disk identification task : %s' % ret[1]
                        raise Exception(error)
            else:
                raise Exception(
                    'Error contacting the GRIDCell to perform the action!')
        else:
            raise Exception('Unsupported platform for this action')
        return django.http.HttpResponseRedirect('/view_gridcell?gridcell_name=%s&ack=%s' % (gridcell_name, action))
    except Exception, e:
        s = str(e)
        return_dict["error_details"] = "An error occurred when processing your request : %s" % s
        return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


def replace_disk(request):

    return_dict = {}
    try:
        return_dict['base_template'] = "gridcell_base.html"
        return_dict['tab'] = 'gridcell_list_tab'
        return_dict["page_title"] = 'Replace a disk in a GRIDCell'
        return_dict["error"] = 'Error replacing a disk in a GRIDCell'

        gluster_lck, err = lock.get_lock('gluster_commands')
        if err:
            raise Exception(err)

        if not gluster_lck:
            raise Exception(
                'This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')

        form = None

        vil, err = gluster_volumes.get_basic_volume_info_all()
        if err:
            raise Exception(err)
        # if not vil:
        #  raise Exception('Could not load volume information')
        si, err = system_info.load_system_config()
        if err:
            raise Exception(err)
        if not si:
            raise Exception('Could not load system information')
        return_dict['system_config_list'] = si

        python_scripts_path, err = config.get_python_scripts_path()
        if err:
            raise Exception(err)
        common_python_scripts_path, err = config.get_common_python_scripts_path()
        if err:
            raise Exception(err)
        if request.method == "GET":
            raise Exception("Incorrect access method. Please use the menus")
        else:
            node = request.POST["node"]
            serial_number = request.POST["serial_number"]

            if "conf" in request.POST:
                if "node" not in request.POST or "serial_number" not in request.POST:
                    return_dict["error"] = "Incorrect access method. Please use the menus"
                elif request.POST["node"] not in si:
                    return_dict["error"] = "Unknown GRIDCell. Please use the menus"
                elif "step" not in request.POST:
                    return_dict["error"] = "Incomplete request. Please use the menus"
                elif request.POST["step"] not in ["offline_disk", "scan_for_new_disk", "online_new_disk"]:
                    return_dict["error"] = "Incomplete request. Please use the menus"
                else:
                    step = request.POST["step"]

                    # Which step of the replace disk are we in?

                    if step == "offline_disk":

                        # get the pool corresponding to the disk
                        # zpool offline pool disk
                        # send a screen asking them to replace the disk

                        pool = None
                        if serial_number in si[node]["disks"]:
                            disk = si[node]["disks"][serial_number]
                            if "pool" in disk:
                                pool = disk["pool"]
                            disk_id = disk["id"]
                        if not pool:
                            raise Exception(
                                "Could not find the storage pool on that disk. Please use the menus")
                        else:
                            '''
                            pid = -1
                            #Got the pool so now find the brick pid corresponding to the pool.
                            for vol in vil:
                              if "brick_status" not in vol:
                                continue
                              bs = vol["brick_status"]
                              for brick_name, brick_status_dict in bs.items():
                                if node in brick_name: 
                                  path = brick_status_dict["path"]
                                  r = re.search('/%s/[\S]+'%pool, path)
                                  if r:
                                    pid = brick_status_dict['pid']
                                    break
                              if pid != -1:
                                break
                            if pid != -1:
                            #issue the kill to the process here, using salt
                            '''

                            # issue a zpool offline pool disk-id using salt
                            client = salt.client.LocalClient()
                            cmd_to_run = 'zpool offline %s %s' % (
                                pool, disk_id)
                            # print 'Running %s'%cmd_to_run
                            #assert False
                            rc = client.cmd(node, 'cmd.run_all', [cmd_to_run])
                            if rc:
                                for node, ret in rc.items():
                                    # print ret
                                    if ret["retcode"] != 0:
                                        error = "Error bringing the disk with serial number %s offline on %s : " % (
                                            serial_number, node)
                                        if "stderr" in ret:
                                            error += ret["stderr"]
                                        raise Exception(error)
                            # print rc
                            # if disk_status == "Disk Missing":
                            #  #Issue a reboot now, wait for a couple of seconds for it to shutdown and then redirect to the template to wait for reboot..
                            #  pass
                            audit_str = "Disk replacement of old disk(sno %s) on GRIDCell %s - disk taken offline." % (
                                serial_number, node)
                            ret, err = audit.audit(
                                "replace_disk_offline_disk", audit_str, request)
                            if err:
                                raise Exception(err)
                            return_dict["serial_number"] = serial_number
                            return_dict["node"] = node
                            return_dict["pool"] = pool
                            return_dict["old_id"] = disk_id
                            template = "replace_disk_prompt.html"

                    elif step == "scan_for_new_disk":

                        # they have replaced the disk so scan for the new disk
                        # and prompt for a confirmation of the new disk serial
                        # number

                        pool = request.POST["pool"]
                        old_id = request.POST["old_id"]
                        return_dict["node"] = node
                        return_dict["serial_number"] = serial_number
                        return_dict["pool"] = pool
                        return_dict["old_id"] = old_id
                        old_disks = si[node]["disks"].keys()
                        client = salt.client.LocalClient()
                        rc = client.cmd(
                            node, 'integralstor.disk_info_and_status')
                        if rc and node in rc:
                            new_disks = rc[node].keys()
                            if new_disks:
                                for disk in new_disks:
                                    if disk not in old_disks:
                                        return_dict["inserted_disk_serial_number"] = disk
                                        return_dict["new_id"] = rc[node][disk]["id"]
                                        break
                                if "inserted_disk_serial_number" not in return_dict:
                                    raise Exception(
                                        "Could not detect any new disk.")
                                else:
                                    template = "replace_disk_confirm_new_disk.html"

                    elif step == "online_new_disk":

                        # they have confirmed the new disk serial number
                        # get the id of the disk and
                        # zpool replace poolname old disk new disk
                        # zpool clear poolname to clear old errors
                        # return a result screen
                        pool = request.POST["pool"]
                        old_id = request.POST["old_id"]
                        new_id = request.POST["new_id"]
                        new_serial_number = request.POST["new_serial_number"]
                        cmd1 = "zpool replace -f %s %s %s" % (
                            pool, old_id, new_id)
                        cmd2 = 'zpool online %s %s' % (pool, new_id)
                        cmd3 = '%s/generate_manifest.py' % common_python_scripts_path
                        cmd4 = '%s/generate_status.py' % common_python_scripts_path
                        # print 'Running %s'%cmd_to_run
                        db_path, err = config.get_db_path()
                        if err:
                            raise Exception(
                                'Error scheduling a job - getting database location : %s' % err)
                        #job_id, err = scheduler_utils.schedule_a_job(db_path, 'Disk replacement on GRIDCell %s'%node, [{'Disk Replacement': cmd1}, {'Disk onlining':cmd2}], node=node, extra={'deleteable':0})
                        #new_job_id, err = scheduler_utils.schedule_a_job(db_path, 'Regeneration of system configuration', [{'Regeneration of system configuration':cmd3}, {'Regeneration of system status':cmd4}], extra = {'execute_after': job_id, 'deleteable':0})

                        job_id, err = scheduler_utils.create_task('Disk replacement on GRIDCell %s' % node, [{'Disk Replacement': cmd1}, {'Disk onlining': cmd2}, {
                                                               'Regeneration of system configuration': cmd3}, {'Regeneration of system status': cmd4}], task_type_id=1, node=node)
                        if err:
                            raise Exception(
                                'Error scheduling the disk replacement : %s' % err)
                        '''
            client = salt.client.LocalClient()
            rc = client.cmd(node, 'cmd.run_all', [cmd_to_run])
            if rc:
              #print rc
              for node, ret in rc.items():
                #print ret
                if ret["retcode"] != 0:
                  error = "Error replacing the disk on %s : "%(node)
                  if "stderr" in ret:
                    error += ret["stderr"]
                  rc = client.cmd(node, 'cmd.run', ['zpool online %s %s'%(pool, old_id)])
                  raise Exception(error)
            else:
              raise Exception("Error replacing the disk on %s : "%(node))

            '''
                        '''
            cmd_to_run = "zpool set autoexpand=on %s"%pool
            print 'Running %s'%cmd_to_run
            rc = client.cmd(node, 'cmd.run_all', [cmd_to_run])
            if rc:
              for node, ret in rc.items():
                #print ret
                if ret["retcode"] != 0:
                  error = "Error setting pool autoexpand on %s : "%(node)
                  if "stderr" in ret:
                    error += ret["stderr"]
                  raise Exception(error)
            print rc
            if new_serial_number in si[node]["disks"]:
              disk = si[node]["disks"][new_serial_number]
              disk_id = disk["id"]
            '''
                        '''
            cmd_to_run = 'zpool online %s %s'%(pool, new_id)
            #print 'Running %s'%cmd_to_run
            rc = client.cmd(node, 'cmd.run_all', [cmd_to_run])
            if rc:
              #print rc
              for node, ret in rc.items():
                #print ret
                if ret["retcode"] != 0:
                  error = "Error bringing the new disk online on %s : "%(node)
                  if "stderr" in ret:
                    error += ret["stderr"]
                  raise Exception(error)
            else:
              raise Exception("Error bringing the new disk online on %s : "%(node))
            (ret, rc), err = command.execute_with_rc('%s/generate_manifest.py'%common_python_scripts_path)
            if err:
              raise Exception(err)
            #print ret
            if rc != 0:
              #print ret
              raise Exception("Could not regenrate the new hardware configuration. Error generating manifest. Return code %d"%rc)
            else:
              (ret, rc), err = command.execute_with_rc('%s/generate_status.py'%common_python_scripts_path)
              if err:
                raise Exception(err)
              if rc != 0:
                #print ret
                raise Exception("Could not regenrate the new hardware configuration. Error generating status. Return code %d"%rc)
              si, err = system_info.load_system_config()
              if err:
                raise Exception(err)
            '''
                        return_dict["node"] = node
                        return_dict["old_serial_number"] = serial_number
                        return_dict["new_serial_number"] = new_serial_number
                        audit_str = "Scheduled replacement of old disk(sno %s) with new disk(sno %s) on GRIDCell %s." % (
                            serial_number, new_serial_number, node)
                        ret, err = audit.audit(
                            "replace_disk_scheduled", audit_str, request)
                        if err:
                            raise Exception(err)
                        template = "replace_disk_success.html"

                    return django.shortcuts.render_to_response(template, return_dict, context_instance=django.template.context.RequestContext(request))

            else:
                if "node" not in request.POST or "serial_number" not in request.POST:
                    raise Exception(
                        "Incorrect access method. Please use the menus")
                else:
                    return_dict["node"] = request.POST["node"]
                    return_dict["serial_number"] = request.POST["serial_number"]
                    template = "replace_disk_conf.html"
        return django.shortcuts.render_to_response(template, return_dict, context_instance=django.template.context.RequestContext(request))
    except Exception, e:
        s = str(e)
        if "Another transaction is in progress".lower() in s.lower():
            return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
        else:
            return_dict["error_details"] = "An error occurred when processing your request : %s" % s
        return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
    finally:
        lock.release_lock('gluster_commands')

#@django.views.decorators.csrf.csrf_exempt


def identify_gridcell(request):
    try:
        return_dict = {}
        return_dict['base_template'] = "gridcell_base.html"
        return_dict["page_title"] = 'Activate GRIDCell identification light'
        return_dict['tab'] = 'gridcell_list_tab'
        return_dict["error"] = 'Error activating GRIDCell identification light'

        if "gridcell_name" not in request.GET:
            raise Exception("Error flagging gridcell. No gridcell specified")

        gridcell_name = request.GET["gridcell_name"]

        client = salt.client.LocalClient()
        blink_time = 255
        ret = client.cmd(gridcell_name, 'cmd.run', [
                         'ipmitool chassis identify %s' % (blink_time)])
        # print ret
        if ret and ret[gridcell_name] == 'Chassis identify interval: %s seconds' % (blink_time):
            return django.shortcuts.render_to_response("node_flagged.html", return_dict, context_instance=django.template.context.RequestContext(request))
        else:
            raise Exception('Error flagging GRIDCell %s' % gridcell_name)
    except Exception, e:
        s = str(e)
        return_dict["error_details"] = "An error occurred when processing your request : %s" % s
        return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


'''
def add_nodes_to_pool(request):
  """ Used to add servers to the trusted pool"""

  return_dict = {}
  try:
    gluster_lck, err = lock.get_lock('gluster_commands')
    if err:
      raise Exception(err)

    if not gluster_lck:
      raise Exception('This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')

    return_dict['base_template'] = "gridcell_base.html"
    return_dict["page_title"] = 'Add GRIDCells to the storage pool'
    return_dict['tab'] = 'gridcell_list_tab'
    return_dict["error"] = 'Error adding GRIDCells to the storage pool'
    error_list = []
  
    si, err = system_info.load_system_config()
    if err:
      raise Exception(err)
    return_dict['system_info'] = si
  
    # Get list of possible nodes that are available
    nl, err = gluster_trusted_pools.get_gridcells_not_in_trusted_pool(si)
    if err:
      raise Exception(err)
    if not nl:
      return_dict["no_available_nodes"] = True
      return django.shortcuts.render_to_response('add_servers_form.html', return_dict, context_instance = django.template.context.RequestContext(request))
  
  
    if request.method == "GET":
      form = trusted_pool_setup_forms.AddNodesForm(addable_node_list = nl)
      return_dict["form"] = form
      return_dict["addable_node_list"] = nl
      url = 'add_servers_form.html'
  
    else:
  
      form = trusted_pool_setup_forms.AddNodesForm(request.POST, addable_node_list = nl)
  
      if form.is_valid():
        cd = form.cleaned_data
      else:
        return_dict['form'] = form
        return django.shortcuts.render_to_response('add_servers_form.html', return_dict, context_instance=django.template.context.RequestContext(request))
  
      # Actual command processing begins
      dbg_node_list = []
      rd = {}
      for n in nl:
        dbg_node_list.append(n.keys()[0])
      iv_logging.debug("Initiating add nodes for %s"%' '.join(dbg_node_list))
      for node in nl:
        td = {}
        d, errors = grid_ops.add_a_node_to_storage_pool(si, node["hostname"])
        if d:
          if d and ("op_status" in d) and d["op_status"]["op_ret"] == 0:
            audit.audit("add_storage", d["audit_str"], request)
        hostname = node["hostname"]
        td['rc'] = rc
        td['d'] = rc
        td['error_list'] = el
        rd[hostname] = td
        if errors:
          error_list.append(errors)

      return_dict['result_dict'] = rd
      if error_list:
        return_dict['error_list'] = error_list
  
      if settings.APP_DEBUG:
        return_dict['app_debug'] = True 
  
      url =  'add_server_results.html'

    return django.shortcuts.render_to_response(url, return_dict, context_instance = django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
  finally:
    lock.release_lock('gluster_commands')
'''

# vim: tabstop=8 softtabstop=0 expandtab ai shiftwidth=4 smarttab
