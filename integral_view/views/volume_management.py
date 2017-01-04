import re, json

import django.http, django
from  django.contrib import auth
from django.conf import settings

import salt.client

import integralstor_gridcell
from integralstor_gridcell import gluster_volumes, system_info, gluster_batch, iscsi, gluster_quotas, gluster_snapshots, xml_parse , gluster_gfapi
import integralstor_common
from integralstor_common import command, audit, common, cifs, lock, filesize

import integral_view
from integral_view.forms import volume_management_forms
from integral_view.utils import iv_logging

def view_volumes(request):
  """ Display the list of all user created volumes"""
  return_dict = {}
  try:
    return_dict['base_template'] = "volume_base.html"
    return_dict["page_title"] = 'View volume information'
    return_dict['tab'] = 'view_volumes_tab'
    return_dict["error"] = 'Error loading volume information'

    gluster_lck, err = lock.get_lock('gluster_commands')
    if err:
      raise Exception(err)

    if not gluster_lck:
      raise Exception('This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')

    vil, err  = gluster_volumes.get_basic_volume_info_all()
    if err:
      raise Exception(err)
    return_dict['volume_info_list'] = vil

    '''
    ivl, err = iscsi.load_iscsi_volumes_list(vil)
    if err:
      raise Exception(err)
    return_dict['iscsi_volumes'] = ivl
    '''
    return django.shortcuts.render_to_response('view_volumes.html', return_dict, context_instance=django.template.context.RequestContext(request))

  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
  finally:
    lock.release_lock('gluster_commands')

def volume_selector(request):
  """A generic volume selector view to precede other actions"""
  return_dict = {}
  try:
    if 'action' not in request.REQUEST or request.REQUEST['action'] not in ['cifs_share_creation']:
      return_dict['base_template'] = "volume_base.html"
      return_dict["page_title"] = 'Volume selection'
      return_dict['tab'] = 'view_volumes_tab'
      return_dict["error"] = 'Error selecting volume'
      raise Exception('Invalid request. Please use the menus.')

    action = request.REQUEST['action']
    return_dict['action'] = action
    if action == 'cifs_share_creation':
      return_dict['base_template'] = "shares_and_targets_base.html"
      return_dict["page_title"] = 'Create a Windows share'
      return_dict['tab'] = 'view_cifs_shares_tab'
      return_dict['cancel_url'] = '/view_cifs_shares'
      return_dict["error"] = 'Error creating a Windows share'
      template = 'create_cifs_share.html'
      redirect_url="/create_cifs_share"

    gluster_lck, err = lock.get_lock('gluster_commands')
    if err:
      raise Exception(err)

    if not gluster_lck:
      raise Exception('This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')

    vil, err  = gluster_volumes.get_basic_volume_info_all()
    if err:
      raise Exception(err)
    if not vil:
      raise Exception('No volumes created. Please create a volume before performing this action.')
    vol_list = []
    for v in vil:
      vol_list.append(v['name'])
    if request.method == 'GET':
      form = integral_view.forms.volume_management_forms.VolumeNameForm(vol_list = vol_list)
      return_dict['form'] = form
      return django.shortcuts.render_to_response('volume_selector.html', return_dict, context_instance=django.template.context.RequestContext(request))
    else:
      form = integral_view.forms.volume_management_forms.VolumeNameForm(request.POST, vol_list = vol_list)
      if not form.is_valid():
        return_dict['form'] = form
        return django.shortcuts.render_to_response('volume_selector.html', return_dict, context_instance=django.template.context.RequestContext(request))
      cd = form.cleaned_data
      return django.http.HttpResponseRedirect('%s?vol_name=%s'%(redirect_url, cd['vol_name']))

  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
  finally:
    lock.release_lock('gluster_commands')
def view_volume(request):
  """Display the information about a specific volume"""
  return_dict = {}
  try:
    return_dict['base_template'] = "volume_base.html"
    return_dict["page_title"] = 'View volume information'
    return_dict['tab'] = 'view_volumes_tab'
    return_dict["error"] = 'Error loading volume information'

    if "ack" in request.GET:
      if request.GET["ack"] == "set_quota":
        return_dict['ack_message'] = "Volume quota successfully updated."
      elif request.GET["ack"] == "removed_quota":
        return_dict['ack_message'] = "Volume quota successfully removed."
      elif request.GET["ack"] == "enabled_quota":
        return_dict['ack_message'] = "Volume quota successfully enabled."
      elif request.GET["ack"] == "disabled_quota":
        return_dict['ack_message'] = "Volume quota successfully disabled."
      elif request.GET["ack"] == "stopped":
        return_dict['ack_message'] = "Volume successfully stopped."
      elif request.GET["ack"] == "started":
        return_dict['ack_message'] = "Volume successfully started."
      elif request.GET["ack"] == "expanded":
        return_dict['ack_message'] = "Volume successfully expanded. Please rebalance the volume in order to use all the GRIDCells."
      elif request.GET["ack"] == "rebalance_started":
        return_dict['ack_message'] = 'A volume rebalance batch process has been scheduled. Please view the "Batch processes" screen to check the status.'

    if 'vol_name' not in request.GET:
      raise Exception('Invalid request. Please use the menus.')
    vol_name = request.GET['vol_name']

    gluster_lck, err = lock.get_lock('gluster_commands')
    if err:
      raise Exception(err)

    if not gluster_lck:
      raise Exception('This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')

    vil, err  = gluster_volumes.get_basic_volume_info_all()
    if err:
      raise Exception(err)

    vol, err = gluster_volumes.get_complete_volume_info(vol_name)
    if err:
      raise Exception(err)
    if not vol:
      raise Exception("Could not locate information for volume %s"%vol_name)
    return_dict["vol"] = vol

    quota_enabled = False
    if "options" in vol :
      for o in vol["options"]:
        if "features.quota" == o["name"] and  o["value"] == "on":
          quota_enabled = True
          break
    return_dict['quota_enabled'] = quota_enabled

    data_locations_list, err = gluster_volumes.get_brick_hostname_list(vol)
    if err:
      raise Exception(err)
    #print data_locations_list
    return_dict["data_locations_list"] = data_locations_list

    ivl, err = iscsi.load_iscsi_volumes_list(vil)
    if err:
      raise Exception(err)
    if ivl and vol["name"] in ivl:
      return_dict["iscsi"] = True

    if 'replicate' in vol["type"].lower():
      return_dict["replicate"] = True
    if 'distribute' in vol["type"].lower():
      return_dict["distribute"] = True

    return django.shortcuts.render_to_response('view_volume.html', return_dict, context_instance=django.template.context.RequestContext(request))

  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
  finally:
    lock.release_lock('gluster_commands')

def volume_browser(request):
  """Volume directory browser for a specific volume"""
  return_dict = {}
  try:
    return_dict['base_template'] = "volume_base.html"
    return_dict["page_title"] = 'Volume browser'
    return_dict["error"] = 'Error browsing volume'
    return_dict['tab'] = 'view_volumes_tab'

    if 'vol_name' not in request.GET:
      raise Exception('Invalid request. Please use the menus.')
    vol_name = request.GET['vol_name']
    return_dict['vol_name'] = vol_name

    if "ack" in request.GET:
      if request.GET["ack"] == "dir_created":
        return_dict['ack_message'] = "Volume directory successfully created."
      elif request.GET["ack"] == "dir_removed":
        return_dict['ack_message'] = "Volume directory successfully removed."

    '''
    gluster_lck, err = lock.get_lock('gluster_commands')
    if err:
      raise Exception(err)
    if not gluster_lck:
      raise Exception('This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')
    '''

    return django.shortcuts.render_to_response('volume_browser.html', return_dict, context_instance=django.template.context.RequestContext(request))  
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
  '''
  finally:
    lock.release_lock('gluster_commands')
  '''

def create_volume_dir(request):
  return_dict = {}
  try:
    return_dict['base_template'] = "volume_base.html"
    return_dict["page_title"] = 'Create volume directory'
    return_dict["error"] = 'Error creating volume directory'
    return_dict['tab'] = 'view_volumes_tab'

    if request.method == 'GET':
      if 'vol_name' not in request.GET or 'path' not in request.GET :
        raise Exception('Invalid request. Please use the menus.')
      vol_name = request.REQUEST["vol_name"]
      path = request.REQUEST["path"]
      init = {}
      init['vol_name'] = vol_name
      init['path'] = path
      form = integral_view.forms.volume_management_forms.CreateVolumeDirForm(initial=init)
      return_dict['form'] = form
      return django.shortcuts.render_to_response('create_volume_dir.html', return_dict, context_instance=django.template.context.RequestContext(request))  
    else:
      form = integral_view.forms.volume_management_forms.CreateVolumeDirForm(request.POST)
      if not form.is_valid():
        return_dict['form'] = form
        return django.shortcuts.render_to_response('create_volume_dir.html', return_dict, context_instance=django.template.context.RequestContext(request))  
      else:
        cd = form.cleaned_data
        ret, err = gluster_gfapi.create_gluster_dir(cd['vol_name'],(cd['path']+cd['dir_name']),0777)
        if err:
          raise Exception(err)
        if ret:
          return django.http.HttpResponseRedirect('/volume_browser?vol_name=%s&ack=dir_created'%cd['vol_name'])
        else:
          raise Exception('Volume directory creation error')
      
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
  '''
  finally:
    lock.release_lock('gluster_commands')
  '''

def remove_volume_dir(request):
  return_dict = {}
  try:
    return_dict['base_template'] = "volume_base.html"
    return_dict["page_title"] = 'Remove volume directory'
    return_dict["error"] = 'Error removing volume directory'
    return_dict['tab'] = 'view_volumes_tab'

    vol_name = request.REQUEST["vol_name"]
    path = request.REQUEST["path"]
    return_dict['vol_name'] = vol_name
    return_dict['path'] = path

    if request.method == 'GET':
      if 'vol_name' not in request.GET or 'path' not in request.GET :
        raise Exception('Invalid request. Please use the menus.')

      return django.shortcuts.render_to_response('remove_volume_dir_tree_conf.html', return_dict, context_instance=django.template.context.RequestContext(request))  
    else:
      ret, err = gluster_gfapi.remove_gluster_dir_tree(vol_name,path)
      if err:
        raise Exception(err)
      if ret:
        return django.http.HttpResponseRedirect('/volume_browser?vol_name=%s&ack=dir_removed'%vol_name)
      else:
        raise Exception('Volume directory removal error')
      
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
  '''
  finally:
    lock.release_lock('gluster_commands')
  '''
def retrieve_volume_subdirs(request):
  return_dict = {}
  try:
    return_dict['base_template'] = "volume_base.html"
    return_dict["page_title"] = 'Get volume subdirectory'
    return_dict["error"] = 'Error retrieving volume sub directories'
    return_dict['tab'] = 'view_volumes_tab'

    dir_name = None
    error = False
    path_base = None
    vol_name = ""
    dir_list = []
    try:
      if ("vol_name" in request.GET) and ("dir" in request.GET):
        vol_name = request.GET.get("vol_name")
        dir_name = request.GET.get("dir")
        first = request.GET.get("first")
        #print first
      else:
        raise Exception ("No volume or Directory Specified")
      if first:
          dirs, err  = gluster_gfapi.get_gluster_dir_list(vol_name ,"")
      else:
        dirs, err  = gluster_gfapi.get_gluster_dir_list(vol_name ,dir_name)
      if err:
        raise Exception(err)

      dir_list = json.dumps(dirs)

    except Exception as e:
      return django.http.HttpResponse("Exception Occured : %s"%str(e))
      #iv_logging.debug("Exception while getting dir listing : "%e)
    else:
      return django.http.HttpResponse(dir_list,mimetype='application/json')
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
def change_volume_status(request):
  """ Used to either stop or start a gluster volume"""
  return_dict = {}
  try:
    return_dict['base_template'] = "volume_base.html"
    return_dict["page_title"] = 'Changing volume status'
    return_dict['tab'] = 'view_volumes_tab'
    return_dict["error"] = 'Error changing volume status'

    if 'action' not in request.REQUEST or 'vol_name' not in request.REQUEST:
      raise Exception('Invalid request. Please use the menus')
    action = request.REQUEST['action']
    if action not in ['start', 'stop']:
      raise Exception('Invalid request. Please use the menus')

    vol_name = request.REQUEST['vol_name']
    return_dict['vol_name'] = vol_name

    if action=='stop':
      if 'conf' not in request.REQUEST:
        return django.shortcuts.render_to_response('stop_volume_conf.html', return_dict, context_instance=django.template.context.RequestContext(request))
        

    gluster_lck, err = lock.get_lock('gluster_commands')
    if err:
      raise Exception(err)

    if not gluster_lck:
      raise Exception('This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')

    ret, err = gluster_volumes.volume_stop_or_start(vol_name, action)
    if err:
      raise Exception(err)

    if action=='start':
      audit_code = 'vol_start'
      audit_str = 'Started volume "%s"'%vol_name
      redirect_ack = 'started'
    else:
      audit_code = 'vol_stop'
      audit_str = 'Stopped volume "%s"'%vol_name
      redirect_ack = 'stopped'

    ret, err = audit.audit(audit_code, audit_str, request.META)
    if err:
      raise Exception(err)

    return django.http.HttpResponseRedirect('/view_volume?vol_name=%s&ack=%s'%(vol_name, redirect_ack))

  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
  finally:
    lock.release_lock('gluster_commands')

def delete_volume(request):

  return_dict = {}
  try:
    return_dict['base_template'] = "volume_base.html"
    return_dict['tab'] = 'view_volumes_tab'
    return_dict["page_title"] = 'Delete a volume'
    return_dict["error"] = 'Error deleting a volume'

    if 'vol_name' not in request.REQUEST:
      raise Exception('Invalid request. Please use the menus.')
    vol_name = request.REQUEST['vol_name']
    return_dict['vol_name'] = vol_name

    shares_list, err = cifs.load_shares_list()
    if err:
      raise Exception("Unable to check for shares in the volume selected")

    shrs = []
    for share in shares_list:
      if vol_name == share['vol']:
        shrs.append(share['name'])
    if shrs:
      raise Exception("A volume can be removed only if all its underlying shares are removed. The share(s) with name(s) %s exists under volume. Please delete the share(s) and try again"%','.join(shrs))

    gluster_lck, err = lock.get_lock('gluster_commands')
    if err:
      raise Exception(err)

    if not gluster_lck:
      raise Exception('This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')

    form = None
  
    vol_info_dict, err = gluster_volumes.get_basic_volume_info(vol_name)
    if err:
      raise Exception(err)

    si, err = system_info.load_system_config()
    if err:
      raise Exception(err)
    if not si:
      raise Exception('Could not load system information')

    return_dict['system_config_list'] = si
  
    if request.method == "GET":
      return django.shortcuts.render_to_response('delete_volume_conf.html', return_dict, context_instance = django.template.context.RequestContext(request))
    else:
      result_list = []

      result_dict = {}
      result_dict["command"] = "Deleting volume %s"%vol_name

      cmd = 'gluster --mode=script volume delete %s --xml'%vol_name
      d, err = xml_parse.run_gluster_command(cmd)
      #print d, err
      if err:
        raise Exception(err)
      result_dict["result"] = "Success"
      result_list.append(result_dict)

      ret, err = audit.audit("vol_delete", "Deleted volume %s"%(vol_name), request.META)
      if err:
        d["result"] = "Failed with error : %s"%estr
        result_list.append(result_dict)
      else:
        # Now delete the brick directories
        for bricks in  vol_info_dict["bricks"]:
          for b in bricks:
            result_dict = {}
            l = b.split(':')
            result_dict["command"] = "Deleting volume storage on GRIDCell %s"%l[0]
            #print "executing command"
            client = salt.client.LocalClient()
            cmd_to_run = 'zfs destroy %s'%l[1][1:]
            #print 'Running %s'%cmd_to_run
            rc = client.cmd(l[0], 'cmd.run_all', [cmd_to_run])
            if rc:
              for hostname, res in rc.items():
                #print ret
                if res["retcode"] != 0:
                  errors = "Error destroying the brick path ZFS dataset on %s"%hostname
                  result_dict["result"] = "Failed with error : %s"%errors
                else:
                  result_dict["result"] = "Success"
                result_list.append(result_dict)
 
      return_dict["result_list"] = result_list
      return django.shortcuts.render_to_response('volume_delete_results.html', return_dict, context_instance = django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
  finally:
    lock.release_lock('gluster_commands')


def expand_volume(request):

  return_dict = {}
  try:
    return_dict['base_template'] = "volume_base.html"
    return_dict['tab'] = 'view_volumes_tab'
    return_dict["page_title"] = 'Expand a volume'
    return_dict["error"] = 'Error expanding a volume'

    if 'vol_name' not in request.REQUEST:
      raise Exception('Invalid request. Please use the menus.')
    vol_name = request.REQUEST['vol_name']

    gluster_lck, err = lock.get_lock('gluster_commands')
    if err:
      raise Exception(err)

    if not gluster_lck:
      raise Exception('This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')

    form = None
  
    vol, err = gluster_volumes.get_basic_volume_info(vol_name)
    if err:
      raise Exception(err)

    si, err = system_info.load_system_config()
    if err:
      raise Exception(err)
  
    if request.method == "GET":
      count = 0
      replicated = False
      repl_count = 0
  
      if "replicate" in vol["type"].lower():
        replica_count = int(vol["replica_count"])
        replicated = True
  
      d, err = gluster_volumes.build_expand_volume_command(vol, si)
      if err:
        raise Exception(err)
  
      return_dict['cmd'] = d['cmd']
      return_dict['node_list'] = d['node_list']
      return_dict['count'] = d['count']
      return_dict['dataset_list'] = d['dataset_list']
      return_dict['vol_name'] = vol["name"]
      if vol["type"] == "Replicate":
        return_dict['vol_type'] = "replicated"
      else:
        return_dict['vol_type'] = "distributed"

      return django.shortcuts.render_to_response('expand_volume_form.html', return_dict, context_instance=django.template.context.RequestContext(request))
    else:
      # POST method processing
  
      if "cmd" not in request.POST or "vol_name" not in request.POST or "count" not in request.POST:
        raise Exception("Invalid request. Please use the menu options.")
  
      cmd = request.POST['cmd']
      count = request.POST['count']
      dsl = request.POST.getlist('dataset_list')
      dataset_dict = {}
      for ds in dsl:
        tl = ds.split(':')
        dataset_dict[tl[0]] = tl[1]

      #First create the datasets on which the bricks will reside
      client = salt.client.LocalClient()
      revert_list = []
      errors = ""
      for node, dataset in dataset_dict.items():
        dataset_cmd = 'zfs create %s'%dataset
        #print dataset_cmd
        dataset_revert_cmd = 'zfs destroy %s'%dataset
        #print dataset_revert_cmd
        r1 = client.cmd(node, 'cmd.run_all', [dataset_cmd])
        if r1:
          for node, ret in r1.items():
            #print ret
            if ret["retcode"] != 0:
              errors += ", Error creating the underlying storage brick on %s"%node
              #print errors
            else:
              revert_list.append({node:dataset_revert_cmd})
  
      if errors != "":
        if revert_list:
          #Undo the creation of the datasets
          for revert in revert_list:
            for node, dsr_cmd in revert.items():
              r1 = client.cmd(node, 'cmd.run_all', [dsr_cmd])
              if r1:
                for node, ret in r1.items():
                  #print ret
                  if ret["retcode"] != 0:
                    errors += ", Error undoing the creating the underlying storage brick on %s"%node
        raise Exception(errors)
  
  
      #iv_logging.info("Running volume expand : %s"%cmd)
      #print cmd
      #Now run the actual expand volume command
      d, err = xml_parse.run_gluster_command(cmd)
      #print d, err
      if err:
        raise Exception(err)
  
      #Success so audit the change
      audit_str = "Expanded volume %s by adding %s storage units."%(vol_name, count)
      ret, err = audit.audit("expand_volume", audit_str, request.META)

      if err:
        if revert_list:
          #Undo the creation of the datasets
          #print 'undoing'
          for revert in revert_list:
            #print revert
            for node, dsr_cmd in revert.items():
              r1 = client.cmd(node, 'cmd.run_all', [dsr_cmd])
              if r1:
                for node, ret in r1.items():
                  #print ret
                  if ret["retcode"] != 0:
                    err += ", Error undoing the creating the underlying storage brick on %s"%node
        raise Exception(errors)
  
      return django.http.HttpResponseRedirect('/view_volume?vol_name=%s&ack=expanded'%vol_name)
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
  finally:
    lock.release_lock('gluster_commands')

def initiate_volume_rebalance(request):
  return_dict = {}
  try:
    return_dict['base_template'] = "volume_base.html"
    return_dict['tab'] = 'view_volumes_tab'
    return_dict["page_title"] = 'Initiate volume rebalance'
    return_dict["error"] = 'Error initiating volume rebalance'

    if 'vol_name' not in request.REQUEST:
      raise Exception('Invalid request. Please use the menus.')
    vol_name = request.REQUEST['vol_name']
    return_dict['vol_name'] = vol_name

    gluster_lck, err = lock.get_lock('gluster_commands')
    if err:
      raise Exception(err)

    if not gluster_lck:
      raise Exception('This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')

    d, err = gluster_batch.create_rebalance_command_file(vol_name)
    if err:
      raise Exception(err)
    ret, err = audit.audit("vol_rebalance_start", "Scheduled volume rebalance start for volume %s"%vol_name, request.META)
    if err:
      raise Exception(err)

    return django.http.HttpResponseRedirect('/view_volume?vol_name=%s&ack=rebalance_started'%vol_name)

  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
  finally:
    lock.release_lock('gluster_commands')

def set_volume_options(request):

  return_dict = {}
  try:
    return_dict['base_template'] = "volume_base.html"
    return_dict['tab'] = 'view_volumes_tab'
    return_dict["page_title"] = 'Set volume options'
    return_dict["error"] = 'Error setting volume options'

    if 'vol_name' not in request.REQUEST:
      raise Exception('Invalid request. Please use the menus.')
    vol_name = request.REQUEST['vol_name']
    return_dict['vol_name'] = vol_name

    gluster_lck, err = lock.get_lock('gluster_commands')
    if err:
      raise Exception(err)

    if not gluster_lck:
      raise Exception('This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')

    if request.method == "GET":
      vol_dict, err = gluster_volumes.get_basic_volume_info(vol_name)
      if err:
        raise Exception(err)
      if not vol_dict:
        raise Exception('Could not retrieve the information for volume %s'%vol_name)
      d = {}
      #Set default values
      d["auth_allow"] = '*'
      d["auth_reject"] = 'NONE'
      d["readonly"] = False
      d["nfs_disable"] = False
      d['nfs_volume_access'] = 'read-write'
      d["vol_name"] = vol_name
  
      # Now fill in current values and pass to the form
      if "options" in vol_dict:
        for option in vol_dict["options"]:
          if option["name"] == "auth.allow": 
            d["auth_allow"] = option["value"]
          if option["name"] == "auth.reject": 
            d["auth_reject"] = option["value"]
          if option["name"] == "nfs.disable": 
            if option["value"] == "on":
              d["nfs_disable"] = True
          if option["name"] == "nfs.volume-access": 
            d["nfs_volume_access"] = option["value"]
          if option["name"] == "features.read-only": 
            d["readonly"] = option["value"]
          if option["name"] == "features.worm": 
            d["enable_worm"] = option["value"]
      form = integral_view.forms.volume_management_forms.VolumeOptionsForm(initial=d)
      return_dict["form"] = form
      return django.shortcuts.render_to_response('volume_options_form.html', return_dict, context_instance=django.template.context.RequestContext(request))
    else:
      #POST request so form submission
      form = integral_view.forms.volume_management_forms.VolumeOptionsForm(request.POST)
      if not form.is_valid():
        return_dict["form"] = form
        return django.shortcuts.render_to_response('volume_options_form.html', return_dict, context_instance = django.template.context.RequestContext(request))
      cd = form.cleaned_data
      ol, err = gluster_volumes.set_volume_options(cd)
      if err:
        raise Exception(err)
      if ol:
        for d in ol:
          if d and ("op_status" in d) and d["op_status"]["op_ret"] == 0:
            #Success so audit the change
            ret, err = audit.audit("set_vol_options", d["audit_str"], request.META)
            if err:
              raise Exception(err)
  
      return_dict["result_list"] = ol
      return django.shortcuts.render_to_response('volume_options_result.html', return_dict, context_instance = django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
  finally:
    lock.release_lock('gluster_commands')

def set_dir_quota(request):
  return_dict = {}
  try:
    return_dict['base_template'] = "volume_base.html"
    return_dict['tab'] = 'view_volumes_tab'
    return_dict["page_title"] = 'Set volume directory quota'
    return_dict["error"] = 'Error setting volume directory quota'

    gluster_lck, err = lock.get_lock('gluster_commands')
    if err:
      raise Exception(err)

    if not gluster_lck:
      raise Exception('This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')

    vil, err = gluster_volumes.get_basic_volume_info_all()
    if err:
      raise Exception(err)

    if 'vol_name' not in request.REQUEST:
      raise Exception('Invalid request. Please use the menus.')

    vol_name = request.REQUEST['vol_name']
    return_dict['vol_name'] = vol_name

    dir = None
    if 'dir' in request.REQUEST:
      dir = request.REQUEST['dir']

    vd, err = gluster_volumes.get_basic_volume_info(vol_name)
    if err:
      raise Exception(err)
    return_dict['vol'] = vd

    quota_dict, err = gluster_volumes.get_volume_quota(vol_name, vd)
    if err:
      raise Exception(err)

    quota_enabled = False
    if "options" in vd :
      for o in vd["options"]:
        if "features.quota" == o["name"] and o["value"] == "on":
          quota_enabled = True
          break

    if request.method == 'GET':
      init = {}
      if vol_name:
        init['vol_name'] = vol_name
      if dir:
        return_dict['dir'] = dir
        init['dir'] = dir
        if quota_dict and request.REQUEST['dir'] in quota_dict:
          q = quota_dict[request.REQUEST['dir']]
          #print q
          return_dict['current_quota'] = filesize.naturalsize(q['hard_limit'])
      form = volume_management_forms.VolumeQuotaForm(initial=init)
      return_dict["form"] = form
      if vol_name and dir:
        return django.shortcuts.render_to_response('edit_volume_dir_quota.html', return_dict, context_instance=django.template.context.RequestContext(request))
      else:
        return django.shortcuts.render_to_response('set_volume_dir_quota.html', return_dict, context_instance=django.template.context.RequestContext(request))
    else:
      form = integral_view.forms.volume_management_forms.VolumeQuotaForm(request.POST)
      if not form.is_valid():
        return_dict["form"] = form
        return django.shortcuts.render_to_response('edit_volume_dir_quota.html', return_dict, context_instance = django.template.context.RequestContext(request))
      cd = form.cleaned_data
      vol_name = cd["vol_name"]
      if not quota_enabled:
        res, err = gluster_quotas.change_quota_status(vol_name, 'enable')
        if err:
          raise Exception(err)
        result_message = 'Auto enabled quota for volume %s'%vol_name
        ret, err = audit.audit("change_quota_status", result_message, request.META)
      res, err = gluster_quotas.set_volume_dir_quota(cd["vol_name"], cd["dir"], cd["limit"], cd["unit"])
      if err:
        raise Exception(err)
      result_message = 'Successfully set quota for directory %s on volume %s to %s %s'%(cd['dir'], cd['vol_name'], cd['limit'], cd['unit'])
      return_dict['result_message'] = result_message
      ret, err = audit.audit("set_vol_quota", result_message, request.META)
      return django.http.HttpResponseRedirect('/view_volume?vol_name=%s&ack=set_quota'%vol_name)
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
  finally:
    lock.release_lock('gluster_commands')

def remove_dir_quota(request):
  return_dict = {}
  try:
    return_dict['base_template'] = "volume_base.html"
    return_dict['tab'] = 'view_volumes_tab'
    return_dict["page_title"] = 'Remove volume directory quota'
    return_dict["error"] = 'Error removing volume directory quota '

    gluster_lck, err = lock.get_lock('gluster_commands')
    if err:
      raise Exception(err)

    if not gluster_lck:
      raise Exception('This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')

    if 'vol_name' not in request.REQUEST or 'dir' not in request.REQUEST:
      raise Exception('Invalid request. Please use the menus.')
    vol_name = request.REQUEST['vol_name']
    return_dict['vol_name'] = vol_name

    dir = request.REQUEST['dir']
    return_dict['dir'] = dir

    if request.method == 'GET':
      return django.shortcuts.render_to_response('remove_volume_dir_quota_conf.html', return_dict, context_instance=django.template.context.RequestContext(request))
    else:
      res, err = gluster_quotas.remove_volume_dir_quota(vol_name, dir)
      if err:
        raise Exception(err)
      audit_str = 'Successfully removed quota for directory %s on volume %s'%(dir, vol_name)
      ret, err = audit.audit("remove_vol_quota", audit_str, request.META)
      return django.http.HttpResponseRedirect('/view_volume?vol_name=%s&ack=removed_quota'%vol_name)
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
  finally:
    lock.release_lock('gluster_commands')

def change_quota_status(request):
  return_dict = {}
  try:
    return_dict['base_template'] = "volume_base.html"
    return_dict['tab'] = 'view_volumes_tab'
    return_dict["page_title"] = 'Change quota status'
    return_dict["error"] = 'Error changing quota status'

    gluster_lck, err = lock.get_lock('gluster_commands')
    if err:
      raise Exception(err)

    if not gluster_lck:
      raise Exception('This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')

    if 'vol_name' not in request.REQUEST or 'action' not in request.REQUEST:
      raise Exception('Invalid request. Please use the menus.')
    vol_name = request.REQUEST['vol_name']
    action = request.REQUEST['action']
    return_dict['vol_name'] = vol_name
    return_dict['action'] = action
    if request.method == 'GET' and  action == 'disable':
        return django.shortcuts.render_to_response('disable_volume_quota_conf.html', return_dict, context_instance=django.template.context.RequestContext(request))
    else:
      res, err = gluster_quotas.change_quota_status(vol_name, action)
      if err:
        raise Exception(err)
      result_message = 'Successfully %sd quota for volume %s'%(action, vol_name)
      return_dict['result_message'] = result_message
      ret, err = audit.audit("change_quota_status", result_message, request.META)
      if action == 'enable':
        ack = 'enabled_quota'
      else:
        ack = 'disabled_quota'
      return django.http.HttpResponseRedirect('/view_volume?vol_name=%s&ack=%s'%(vol_name, ack))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
  finally:
    lock.release_lock('gluster_commands')


def create_snapshot(request):

  return_dict = {}
  try:
    return_dict['base_template'] = "snapshot_base.html"
    return_dict['tab'] = 'snapshot_create_tab'
    return_dict["page_title"] = 'Create a volume snapshot'
    return_dict["error"] = 'Error creating volume snapshot'

    gluster_lck, err = lock.get_lock('gluster_commands')
    if err:
      raise Exception(err)

    if not gluster_lck:
      raise Exception('This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')

    vil, err = gluster_volumes.get_basic_volume_info_all()
    if err:
      raise Exception(err)
    if not vil:
      return_dict['no_volumes'] = True
      return django.shortcuts.render_to_response('create_snapshot.html', return_dict, context_instance = django.template.context.RequestContext(request))
    l = []
    for v in vil:
      l.append(v["name"])
    if request.method == "GET":
      form = integral_view.forms.volume_management_forms.CreateSnapshotForm(vol_list=l)
      return_dict["form"] = form
      return django.shortcuts.render_to_response('create_snapshot.html', return_dict, context_instance = django.template.context.RequestContext(request))
    else:
      form = integral_view.forms.volume_management_forms.CreateSnapshotForm(request.POST, vol_list=l)
      if not form.is_valid():
        return_dict["form"] = form
        return django.shortcuts.render_to_response('create_snapshot.html', return_dict, context_instance = django.template.context.RequestContext(request))
      cd = form.cleaned_data
      d, err  = gluster_snapshots.create_snapshot(cd)
      if err:
        raise Exception(err)
      if d and  ("op_status" in d) and d["op_status"]["op_ret"] == 0:
        #Success so audit the change
        ret, err = audit.audit("create_snapshot", d["display_command"], request.META)
        if err:
          raise Exception(err)
        return_dict["op"] = "Create snapshot"
        return_dict["conf"] = d["display_command"]
        return django.shortcuts.render_to_response('snapshot_op_result.html', return_dict, context_instance = django.template.context.RequestContext(request))
      else:
        err = "Error creating the snapshot : "
        #assert False
        if d:
          if "error_list" in d:
            err += " ".join(d["error_list"])
          if "op_status" in d and "op_errstr" in d["op_status"]:
            if d["op_status"]["op_errstr"]:
              err += d["op_status"]["op_errstr"]
        else:
          err += "The snapshot command did not return a result. Please try again."
        raise Exception(err)
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
  finally:
    lock.release_lock('gluster_commands')

def delete_snapshot(request):

  return_dict = {}
  try:
    return_dict['base_template'] = "snapshot_base.html"
    return_dict['tab'] = 'snapshot_view_tab'
    return_dict["page_title"] = 'Delete a volume snapshot'
    return_dict["error"] = 'Error deleting a volume snapshot'
    gluster_lck, err = lock.get_lock('gluster_commands')
    if err:
      raise Exception(err)

    if not gluster_lck:
      raise Exception('This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')


    if request.method == "GET":
      # Disallowed GET method so return error.
      return_dict["error"] = "Invalid request. Please use the menu options."
    else:
      # POST method processing
      if "snapshot_name" not in request.POST:
        return_dict["error"] = "Snapshot name not specified. Please use the menu options."
      elif "conf" not in request.POST:
        #Get a conf from the user before we proceed
        return_dict["snapshot_name"] = request.POST["snapshot_name"]
        template = "delete_snapshot_conf.html"
      else:
        #Got a conf from the user so proceed
        snapshot_name = request.POST["snapshot_name"]
        d, err = gluster_snapshots.delete_snapshot(snapshot_name)
        if err:
          raise Exception(err)
        if d:
          #assert False
          if "op_status" in d:
            if d["op_status"]["op_errno"] == 0:
              return_dict["conf"] = "Successfully deleted snapshot - %s"%snapshot_name
              return_dict["op"] = "Delete snapshot"
              audit_str = "Deleted snapshot %s."%snapshot_name
              ret, err = audit.audit("delete_snapshot", audit_str, request.META)
              if err:
                raise Exception(err)
              template = "snapshot_op_result.html"
            else:
              err = "Error deleting the snapshot :"
              if "op_status" in d and "op_errstr" in d["op_status"]:
                err += d["op_status"]["op_errstr"]
              if "error_list" in d:
                err += " ".join(d["error_list"])
              raise Exception(err)
          else:
            raise Exception("Could not detect the status of the snapshot deletion. Please try again.")
  
    return django.shortcuts.render_to_response(template, return_dict, context_instance = django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
  finally:
    lock.release_lock('gluster_commands')


def restore_snapshot(request):

  return_dict = {}
  try:
    return_dict['base_template'] = "snapshot_base.html"
    return_dict['tab'] = 'snapshot_view_tab'
    return_dict["page_title"] = 'Restore a volume snapshot'
    return_dict["error"] = 'Error restoring a volume snapshot'
    gluster_lck, err = lock.get_lock('gluster_commands')
    if err:
      raise Exception(err)

    if not gluster_lck:
      raise Exception('This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')

    form = None
  
    if request.method == "GET":
      # Disallowed GET method so return error.
      return_dict["error"] = "Invalid request. Please use the menu options."
    else:
      # POST method processing
      if "snapshot_name" not in request.POST:
        return_dict["error"] = "Snapshot name not specified. Please use the menu options."
      elif "conf" not in request.POST:
        #Get a conf from the user before we proceed
        return_dict["snapshot_name"] = request.POST["snapshot_name"]
        return_dict["vol_name"] = request.POST["vol_name"]
        template = "restore_snapshot_conf.html"
      else:
        #Got a conf from the user so proceed
        snapshot_name = request.POST["snapshot_name"]
        vol_name = request.POST["vol_name"]
        d, err = gluster_snapshots.restore_snapshot(snapshot_name)
        if err:
          raise Exception(err)
        if d:
          #assert False
          if "op_status" in d:
            if d["op_status"]["op_errno"] == 0:
              return_dict["conf"] = "Successfully restored snapshot %s onto volume %s"%(snapshot_name, vol_name)
              return_dict["op"] = "Restore snapshot"
              audit_str = "Restored snapshot %s onto volume %s."%(snapshot_name, vol_name)
              ret, err = audit.audit("restore_snapshot", audit_str, request.META)
              if err:
                raise Exception(err)
              template = "snapshot_op_result.html"
            else:
              err = "Error restoring the snapshot :"
              if "op_status" in d and "op_errstr" in d["op_status"]:
                err += d["op_status"]["op_errstr"]
              if "error_list" in d:
                err += " ".join(d["error_list"])
              raise Exception(err)
          else:
            raise Exception("Could not detect the status of the snapshot restoration. Please try again.")
  
    return django.shortcuts.render_to_response(template, return_dict, context_instance = django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
  finally:
    lock.release_lock('gluster_commands')

          
def deactivate_snapshot(request):

  return_dict = {}
  try:
    return_dict['base_template'] = "snapshot_base.html"
    return_dict['tab'] = 'snapshot_view_tab'
    return_dict["page_title"] = 'Deactivate a volume snapshot'
    return_dict["error"] = 'Error deactivating a volume snapshot'
    gluster_lck, err = lock.get_lock('gluster_commands')
    if err:
      raise Exception(err)

    if not gluster_lck:
      raise Exception('This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')

    form = None
  
    if request.method == "GET":
      # Disallowed GET method so return error.
      raise Exception("Invalid request. Please use the menu options.")
    else:
      # POST method processing
      if "snapshot_name" not in request.POST:
        raise Exception("Snapshot name not specified. Please use the menu options.")
      elif "conf" not in request.POST:
        #Get a conf from the user before we proceed
        return_dict["snapshot_name"] = request.POST["snapshot_name"]
        template = "deactivate_snapshot_conf.html"
      else:
        #Got a conf from the user so proceed
        snapshot_name = request.POST["snapshot_name"]
        d, err = gluster_snapshots.deactivate_snapshot(snapshot_name)
        if err:
          raise Exception(err)
        if d:
          #assert False
          if "op_status" in d:
            if d["op_status"]["op_errno"] == 0:
              return_dict["conf"] = "Successfully deactivated snapshot - %s"%snapshot_name
              return_dict["op"] = "Deactivate snapshot"
              audit_str = "Deactivated snapshot %s."%snapshot_name
              ret, err = audit.audit("deactivate_snapshot", audit_str, request.META)
              if err:
                raise Exception(err)
              template = "snapshot_op_result.html"
            else:
              err = "Error deactivating the snapshot :"
              if "op_status" in d and "op_errstr" in d["op_status"]:
                err += d["op_status"]["op_errstr"]
              if "error_list" in d:
                err += " ".join(d["error_list"])
              raise Exception(err)
          else:
            raise Exception("Could not detect the status of the snapshot deactivation. Please try again.")
  
    return django.shortcuts.render_to_response(template, return_dict, context_instance = django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
  finally:
    lock.release_lock('gluster_commands')

def activate_snapshot(request):

  return_dict = {}
  try:
    return_dict['base_template'] = "snapshot_base.html"
    return_dict['tab'] = 'snapshot_view_tab'
    return_dict["page_title"] = 'Activate a volume snapshot'
    return_dict["error"] = 'Error activating a volume snapshot'
    gluster_lck, err = lock.get_lock('gluster_commands')
    if err:
      raise Exception(err)

    if not gluster_lck:
      raise Exception('This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')

    form = None
  
    if request.method == "GET":
      # Disallowed GET method so return error.
      return_dict["error"] = "Invalid request. Please use the menu options."
    else:
      # POST method processing
      if "snapshot_name" not in request.POST:
        return_dict["error"] = "Snapshot name not specified. Please use the menu options."
      else:
        snapshot_name = request.POST["snapshot_name"]
        d, err = gluster_snapshots.activate_snapshot(snapshot_name)
        if err:
          raise Exception(err)
        if d:
          #assert False
          if "op_status" in d:
            if d["op_status"]["op_errno"] == 0:
              return_dict["conf"] = "Successfully activated snapshot - %s"%snapshot_name
              return_dict["op"] = "Activate snapshot"
              audit_str = "Activated snapshot %s."%snapshot_name
              ret, err = audit.audit("activate_snapshot", audit_str, request.META)
              if err:
                raise Exception(err)
              template = "snapshot_op_result.html"
            else:
              err = "Error activating the snapshot :"
              if "op_status" in d and "op_errstr" in d["op_status"]:
                err += d["op_status"]["op_errstr"]
              if "error_list" in d:
                err += " ".join(d["error_list"])
              raise Exception(err)
          else:
            raise Exception("Could not detect the status of the snapshot activation. Please try again.")
  
    return django.shortcuts.render_to_response(template, return_dict, context_instance = django.template.context.RequestContext(request))
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
def volume_specific_op(request, operation, vol_name=None):
  """ Used to carry out various volume related operations which is specified in the operation parameter. 
  The volume to be operated on is specified in the vol_name parameter"""

  return_dict = {}
  try:
    gluster_lck, err = lock.get_lock('gluster_commands')
    if err:
      raise Exception(err)

    if not gluster_lck:
      raise Exception('This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')

    return_dict['base_template'] = "volume_base.html"
    return_dict['tab'] = 'volume_configuration_tab'

    if not operation:
      raise Exception("Operation not specified.")

    if operation == 'vol_start':
      return_dict["page_title"] = 'Start a volume'
      return_dict["error"] = 'Error starting a volume'
    elif operation == 'vol_delete':
      return_dict["page_title"] = 'Delete a volume'
      return_dict["error"] = 'Error deleting a volume'
    elif operation == 'vol_stop':
      return_dict["page_title"] = 'Stop a volume'
      return_dict["error"] = 'Error stopping a volume'
    elif operation == 'expand_volume':
      return_dict["page_title"] = 'Expand a volume'
      return_dict["error"] = 'Error expanding a volume'
    elif operation == 'start_rebalance':
      return_dict["page_title"] = 'Start a volume rebalance'
      return_dict["error"] = 'Error starting a volume rebalance'
    elif operation == 'check_rebalance':
      return_dict["page_title"] = 'Check a volume rebalance'
      return_dict["error"] = 'Error checking a volume rebalance'
    elif operation == 'stop_rebalance':
      return_dict["page_title"] = 'Stop a volume rebalance'
      return_dict["error"] = 'Error stopping a volume rebalance'
    elif operation == 'vol_quota':
      return_dict["page_title"] = 'Set volume quota'
      return_dict["error"] = 'Error setting volume quota'
    elif operation == 'vol_options':
      return_dict["page_title"] = 'Set volume options'
      return_dict["error"] = 'Error setting volume options'
    elif operation == 'create_volume_dir':
      return_dict["page_title"] = 'Create a directory in a volume'
      return_dict["error"] = 'Error creatiing a directory in volume'
      return_dict['tab'] = 'create_volume_dir_tab'
    elif operation == 'rotate_log':
      return_dict['base_template'] = "volume_log_base.html"
      return_dict['tab'] = 'volume_log_rotate_tab'
      return_dict["page_title"] = 'Rotate volume log'
      return_dict["error"] = 'Error rotating volume log'
    elif operation == 'view_snapshots':
      return_dict['base_template'] = "snapshot_base.html"
      return_dict['tab'] = 'snapshot_view_tab'
      return_dict["page_title"] = 'View volume snapshots'
      return_dict["error"] = 'Error viewing volume snapshots'
  
    return_dict['op'] = operation
    form = None
  
    vil, err = gluster_volumes.get_basic_volume_info_all()
    if err:
      raise Exception(err)
    if not vil:
      if operation != "view_snapshots":
        raise Exception('Could not load volume information')

    si, err = system_info.load_system_config()
    if err:
      raise Exception(err)
    if not si:
      raise Exception('Could not load system information')
 
    if request.method == "GET":
  
      if operation in ["vol_start", "vol_delete"]:
        l = []
        for v in vil:
          if v["status"] != 1:
            l.append(v["name"])
        form = integral_view.forms.volume_management_forms.VolumeNameForm(vol_list = l)
        if not l:
          return_dict["no_vols"] = True
      elif operation in ["vol_stop", "expand_volume", "start_rebalance", "vol_quota"]:
        l = []
        for v in vil:
          if v["status"] == 1:
            l.append(v["name"])
        form = integral_view.forms.volume_management_forms.VolumeNameForm(vol_list = l)

        if not l:
          return_dict["no_vols"] = True
      elif operation == "vol_options":
        il, err = iscsi.load_iscsi_volumes_list(vil)
        if err:
          raise Exception(err)
        l = []
        for v in vil:
          #Ignore ISCSI volumes for this
          if il and v["name"] in il:
            continue
          l.append(v["name"])
        form = integral_view.forms.volume_management_forms.VolumeNameForm(vol_list = l)
        if not l:
          return_dict["no_vols"] = True
  
      elif operation == "create_volume_dir":
        l = []
        for v in vil:
          l.append(v["name"])
        if not l:
          return_dict["no_vols"] = True
        form = integral_view.forms.volume_management_forms.VolumeNameForm(vol_list = l)
        return_dict['form'] = form
        return django.shortcuts.render_to_response('create_volume_dir.html', return_dict, context_instance=django.template.context.RequestContext(request))  
      else:
        l = []
        for v in vil:
          l.append(v["name"])
        if not l:
          return_dict["no_vols"] = True
        form = integral_view.forms.volume_management_forms.VolumeNameForm(vol_list = l)
    else:
      # POST method processing
      op_conf_msg = {
        'vol_stop':'Stopping volume will make its data inaccessible. Do you want to continue?', 
        'vol_delete': 'Deleting volume will erase all information about the volume. Do you want to continue?',
      }
      if operation == "vol_start":
        l = []
        for v in vil:
          if v["status"] != 1:
            l.append(v["name"])
        form = integral_view.forms.volume_management_forms.VolumeNameForm(request.POST, vol_list = l)
      elif operation in ["vol_stop", "expand_volume", "start_rebalance", "vol_quota"]:
        l = []
        for v in vil:
          if v["status"] == 1:
            l.append(v["name"])
        form = integral_view.forms.volume_management_forms.VolumeNameForm(request.POST, vol_list = l)
  
      elif operation == "create_volume_dir":
        dir_name = request.POST["name"]
        vol_name = request.POST["vol"]
        path = request.POST["path"]
  
        vol_creation, err = gluster_gfapi.create_gluster_dir(vol_name,(path+dir_name),0777)
        if err:
          raise Exception(err)
        if vol_creation:
          return_dict["conf_message"] = "Directory Creation success in path %s for volume %s"%(path+dir_name,vol_name)
          #Reinitialize the form and render back it on the screen.
          l = []
          for v in vil:
            l.append(v["name"])
          if not l:
            return_dict["no_vols"] = True
          form = integral_view.forms.volume_management_forms.VolumeNameForm(vol_list = l)
          return_dict['form'] = form        
          
          return django.shortcuts.render_to_response('create_volume_dir.html', return_dict, context_instance=django.template.context.RequestContext(request))  
        else:
          raise Exception("Directory creation error %s. Please try again"%(path+dir_name))
      else:
        l = []
        for v in vil:
          l.append(v["name"])
        form = integral_view.forms.volume_management_forms.VolumeNameForm(request.POST, vol_list = l)
      if form.is_valid():
        cd = form.cleaned_data
        vol_name = cd['vol_name']
        return_dict['vol_name'] = vol_name
        if operation in ['vol_stop', 'vol_delete']:
          # Check if a share exists before even letting a user delete a volume
          if operation == "vol_delete":
            shares_list, err = cifs.load_shares_list()
            if err:
              raise Exception("Unable to check for shares in the volume selected")
            for share in shares_list:
              if vol_name == share['vol']:
                raise Exception("Share with name %s exists under volume. Cannot delete. Delete the share and try again"%share['name'])

          return_dict['op_conf_msg'] = op_conf_msg[operation]
          return django.shortcuts.render_to_response('volume_specific_op_conf.html', return_dict, context_instance=django.template.context.RequestContext(request))
        elif operation == 'vol_quota':
          init = {}
          init["vol_name"] = vol_name
          vd, err = gluster_volumes.get_basic_volume_info(None, vol_name)
          if err:
            raise Exception(err)
          if not vd:
            raise Exception('Could not retrieve the information for volume %s'%vol_name)
          enable_quota = True
          if "options" in vd :
            for o in vd["options"]:
              if "features.quota" == o["name"]:
                if o["value"] == "on":
                  init["set_quota"] = True
                  if "quotas" in vd and "/" in vd["quotas"]:
                    q = vd["quotas"]["/"]
                    match = re.search('([0-9.]+)([A-Za-z]+)', q["limit"])
                    if match:
                      r  = match.groups()
                      init["limit"] = r[0]
                      init["unit"] = r[1].upper()
          form = volume_management_forms.VolumeQuotaForm(initial=init)
          return_dict["form"] = form
          return django.shortcuts.render_to_response('edit_volume_quota.html', return_dict, context_instance=django.template.context.RequestContext(request))
        elif operation == 'view_snapshots':
          l, err = gluster_volumes.get_snapshots(vol_name)
          if err:
            raise Exception(err)
          vd, err = gluster_volumes.get_basic_volume_info(vil, vol_name)
          if err:
            raise Exception(err)
          if not vd:
            raise Exception('Could not retrieve the information for volume %s'%vol_name)
          if vd["status"] == 1:
            return_dict["vol_started"] = True
          else:
            return_dict["vol_started"] = False
          return_dict["snapshots"] = l
          return_dict["vol_name"] = vol_name
          return django.shortcuts.render_to_response('view_snapshots.html', return_dict, context_instance=django.template.context.RequestContext(request))
        elif operation == "vol_options":
          vol_dict, err = gluster_volumes.get_basic_volume_info(vil, vol_name)
          if err:
            raise Exception(err)
          if not vol_dict:
            raise Exception('Could not retrieve the information for volume %s'%vol_name)
          d = {}
          #Set default values
          d["auth_allow"] = '*'
          d["auth_reject"] = 'NONE'
          d["readonly"] = False
          d["nfs_disable"] = False
          d['nfs_volume_access'] = 'read-write'
          d["vol_name"] = vol_name
  
          # Now fill in current values and pass to the form
          if "options" in vol_dict:
            for option in vol_dict["options"]:
              if option["name"] == "auth.allow": 
                d["auth_allow"] = option["value"]
              if option["name"] == "auth.reject": 
                d["auth_reject"] = option["value"]
              if option["name"] == "nfs.disable": 
                if option["value"] == "on":
                  d["nfs_disable"] = True
              if option["name"] == "nfs.volume-access": 
                d["nfs_volume_access"] = option["value"]
              if option["name"] == "features.read-only": 
                d["readonly"] = option["value"]
              if option["name"] == "features.worm": 
                d["enable_worm"] = option["value"]
          form = integral_view.forms.volume_management_forms.VolumeOptionsForm(initial=d)
          return_dict["form"] = form
          return django.shortcuts.render_to_response('volume_options_form.html', return_dict, context_instance=django.template.context.RequestContext(request))
        elif operation == 'start_rebalance':
          d, err = gluster_batch.create_rebalance_command_file(vol_name)
          if err:
            raise Exception(err)
          if not "error" in d:
            ret, err = audit.audit("vol_rebalance_start", "Scheduled volume rebalance start for volume %s"%vol_name, request.META)
            if err:
              raise Exception(err)
            return django.http.HttpResponseRedirect('/show/batch_start_conf/%s'%d["file_name"])
          else:
            raise Exception("Error initiating rebalance : %s"%d["error"])
  
        elif operation in ['vol_start', 'rotate_log', 'check_rebalance', 'stop_rebalance']:
          return django.http.HttpResponseRedirect('/perform_op/%s/%s'%(operation, vol_name))
  
        elif operation == 'expand_volume':
  
          for vol in vil:
            if vol_name == vol["name"]:
              break
          count = 0
          replicated = False
          repl_count = 0
  
          if "replicate" in vol["type"].lower():
            replica_count = int(vol["replica_count"])
            replicated = True
  
          d, err = gluster_volumes.build_expand_volume_command(vol, si)
          if err:
            raise Exception(err)
          if "error" in d:
            raise Exception("Error expanding the volume : %s"%d["error"])
          iv_logging.debug("Expand volume node list %s for volume %s"%(d['node_list'], vol["name"]))
  
          return_dict['cmd'] = d['cmd']
          return_dict['node_list'] = d['node_list']
          return_dict['count'] = d['count']
          return_dict['dataset_list'] = d['dataset_list']
          return_dict['vol_name'] = vol["name"]
          if vol["type"] == "Replicate":
            return_dict['vol_type'] = "replicated"
          else:
            return_dict['vol_type'] = "distributed"
              
          return django.shortcuts.render_to_response('expand_volume_form.html', return_dict, context_instance=django.template.context.RequestContext(request))
    # form not valid or called using get so return same form
    return_dict['form'] = form
    if operation == "volume_status":
      return_dict['vil'] = vil
      return django.shortcuts.render_to_response('volume_specific_status.html', return_dict, context_instance=django.template.context.RequestContext(request))
    else:
      if operation == 'rotate_log':
        return_dict['base_template'] = 'volume_log_base.html'
      elif operation == 'view_snapshots':
        return_dict['base_template'] = 'snapshot_base.html'
      else:
        return_dict['base_template'] = 'volume_base.html'
      return django.shortcuts.render_to_response('volume_specific_op_form.html', return_dict, context_instance=django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    print s
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
  finally:
    lock.release_lock('gluster_commands')

'''    
'''
def set_volume_quota(request):
  return_dict = {}
  try:
    return_dict['base_template'] = "volume_base.html"
    return_dict['tab'] = 'volume_configuration_tab'
    return_dict["page_title"] = 'Set volume quota'
    return_dict["error"] = 'Error setting volume quota'
    if request.method == "GET":
      # Disallowed GET method so return error.
      raise Exception("Invalid request. Please use the menu options.")
  
    form = integral_view.forms.volume_management_forms.VolumeQuotaForm(request.POST)
  
    if not form.is_valid():
      return_dict["form"] = form
      return django.shortcuts.render_to_response('edit_volume_quota.html', return_dict, context_instance = django.template.context.RequestContext(request))
    cd = form.cleaned_data
    vol_name = cd["vol_name"]
    vd, err = gluster_volumes.get_basic_volume_info(None, vol_name)
    if err:
      raise Exception(err)
    enable_quota = True
    if "options" in vd :
      for o in vd["options"]:
        if o["name"] == "features.quota" and o["value"] == "on":
          enable_quota = False
          break
    ol, err = gluster_quotas.set_volume_quota(cd["vol_name"], enable_quota, cd["set_quota"], cd["limit"], cd["unit"])
    if err:
      raise Exception(err)
    print ol, err
    if ol:
      for d in ol:
        if d and ("op_status" in d) and d["op_status"]["op_ret"] == 0:
          #Success so audit the change
          ret, err = audit.audit("set_vol_quota", d["display_command"], request.META)
          if err:
            raise Exception(err)
    # This is setup so as to make sure windows share also reflect the quota applied on gluster volumes
    (ret, rc), err = command.execute_with_rc("gluster volume set "+request.POST['vol_name']+" quota-deem-statfs on")
    if err:
      raise Exception(err)
    return_dict["result_list"] = ol
    return_dict["app_debug"] = settings.APP_DEBUG
    return django.shortcuts.render_to_response('volume_quota_result.html', return_dict, context_instance = django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

'''
'''
def replace_node(request):

  return_dict = {}
  try:
    gluster_lck, err = lock.get_lock('gluster_commands')
    if err:
      raise Exception(err)

    if not gluster_lck:
      raise Exception('This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')

    return_dict['base_template'] = "gridcell_base.html"
    return_dict['tab'] = 'replace_gridcell_tab'
    return_dict["page_title"] = 'Replace a GRIDCell'
    return_dict["error"] = 'Error replacing a GRIDCell'
    form = None
  
    vil, err = gluster_volumes.get_basic_volume_info_all()
    if err:
      raise Exception(err)
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
      raise Exception("There are no eligible replacement destination GRIDCells.")
  
    return_dict["src_node_list"] = d["src_node_list"]
    return_dict["dest_node_list"] = d["dest_node_list"]
    #assert False
  
    if request.method == "GET":
      form = volume_management_forms.ReplaceNodeForm(d["src_node_list"], d["dest_node_list"])
      return_dict["form"] = form
      return_dict["supress_error_messages"] = True
      #print "form errors ----->"
      #print form.errors
      return django.shortcuts.render_to_response('replace_node_choose_node.html', return_dict, context_instance=django.template.context.RequestContext(request))
    else:
      if "conf" in request.POST:
        form = volume_management_forms.ReplaceNodeConfForm(request.POST)
        if form.is_valid():
          cd = form.cleaned_data
  
          src_node = cd["src_node"]
          dest_node = cd["dest_node"]
  
          vol_list, err = gluster_volumes.get_volumes_on_node(src_node, vil)
          if err:
            raise Exception(err)
          client = salt.client.LocalClient()
          revert_list = []
          if vol_list:
            for vol in vol_list:
              vol_dict, err = gluster_volumes.get_basic_volume_info(vil, vol)
              if err:
                raise Exception(err)
              #Get the brick path and the data set name
              if 'bricks' in vol_dict and vol_dict['bricks']:
                for brick_list in vol_dict['bricks']:
                  for brick in brick_list:
                    d, err = gluster_volumes.get_components(brick)
                    if err:
                      raise Exception(err)
                    if not d:
                      raise Exception("Error decoding the brick for the specified volume. Brick name : %s "%brick)
                    if d['host'] != src_node:
                      continue
                    #Found the brick on the src node so now proceed
                    dataset_cmd = 'zfs create %s/%s/%s'%(d['pool'], d['ondisk_storage'], vol.strip())
                    revert_list = ['zfs destroy %s/%s/%s'%(d['pool'], d['ondisk_storage'], vol.strip())]
                    #print dataset_cmd
                    r1 = client.cmd(dest_node, 'cmd.run_all', [dataset_cmd])
                    errors = ''
                    if r1:
                      for node, ret in r1.items():
                        print ret
                        if ret["retcode"] != 0:
                          errors += ", Error creating the underlying storage brick on %s"%node
                          print errors
                    if errors:
                      print 'Reverting. Executing : ', revert_list
                      r1 = client.cmd(dest_node, 'cmd.run_all', revert_list)
                      if r1:
                        for node, ret in r1.items():
                          print ret
                          if ret["retcode"] != 0:
                            errors += ", Error removing the underlying storage brick on %s"%node
                            print errors
                      raise Exception(errors)
                  
                  

            d, err = gluster_batch.create_replace_command_file(si, vol_list, src_node, dest_node)
            print d, err
            if err or (d and "error" in d):
              if revert_list:
                #Undo the creation of the datasets
                for dsr_cmd in revert_list:
                    r1 = client.cmd(dest_node, 'cmd.run_all', [dsr_cmd])
                    if r1:
                      for node, ret in r1.items():
                        #print ret
                        if ret["retcode"] != 0:
                          errors += " , Error undoing the creation of the underlying storage brick on %s"%dest_node
                          d["error"].append(errors)
              if err:
                raise Exception(err)
              elif d and 'error' in d:
                raise Exception("Error initiating replace : %s"%d["error"])
              else:
                raise Exception('Error creating the replace batch command file')
            else:
              ret, err = audit.audit("replace_node", "Scheduled replacement of GRIDCell %s with GRIDCell %s"%(src_node, dest_node), request.META)
              if err:
                raise Exception(err)
              return django.http.HttpResponseRedirect('/show/batch_start_conf/%s'%d["file_name"])
          else:
            raise Exception('No volumes found on the source GRIDCell')
        else:
          #Invalid conf form
          raise Exception('Invalid request. Please try again.')
      else:
        form = volume_management_forms.ReplaceNodeForm(request.POST, src_node_list = d["src_node_list"], dest_node_list = d["dest_node_list"])
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
      return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
  finally:
    lock.release_lock('gluster_commands')
'''

