import django, django.http
from django.conf import settings
from django.contrib import auth

import salt.client

import random
from integralstor_gridcell import volume_info, system_info, gluster_commands, iscsi
from integralstor_common import command, common, audit

from integral_view.utils import iv_logging

import integral_view
from integral_view.forms import volume_creation_forms

def volume_creation_wizard(request, action):
  """ Used to redirect requests to step a user through a wizrd 
  to create a volume"""

  return_dict = {}
  try:
    if not action:
      raise Exception("Unspecified action. Please use the menus.")
  
    if action == "select_vol_name":
      if request.method != "GET":
        raise Exception("Unsupported action. Please use the menus.")
      form = integral_view.forms.volume_creation_forms.VolumeNameForm()
      return_dict['form'] = form
      return django.shortcuts.render_to_response('vol_create_wiz_vol_name.html', return_dict, context_instance=django.template.context.RequestContext(request))
    else:
      if request.method != "POST":
        raise Exception("Unsupported action. Please use the menus.")
  
    if action == "select_vol_type":
      # Previous form to verify
      form = integral_view.forms.volume_creation_forms.VolumeNameForm(request.POST)
      if form.is_valid():
        cd = form.cleaned_data
        vol_name = cd["volume_name"]
        vol_access = 'file'
        return_dict['vol_name'] = vol_name
        init = {}
        init["vol_name"] = vol_name
        init["vol_access"] = vol_access
        form = integral_view.forms.volume_creation_forms.VolTypeForm(initial=init)
        url = "vol_create_wiz_vol_type.html"
      else:
        url = "vol_create_wiz_vol_name.html"
      '''
      Currently disabling ISCSI so...
      form = integral_view.forms.volume_creation_forms.VolAccessMethodForm(request.POST)
      if form.is_valid():
        cd = form.cleaned_data
        vol_name = cd["vol_name"]
        vol_access = cd["vol_access"]
        return_dict['vol_name'] = vol_name
        return_dict['vol_access'] = vol_access
        init = {}
        init["vol_name"] = vol_name
        init["vol_access"] = vol_access
        form = integral_view.forms.volume_creation_forms.VolTypeForm(initial=init)
        url = "vol_create_wiz_vol_type.html"
      else:
        url = "vol_create_wiz_vol_access.html"
      '''
    elif action == "select_ondisk_storage_type":
      # Previous form to verify
      form = integral_view.forms.volume_creation_forms.VolTypeForm(request.POST)
      if form.is_valid():
        cd = form.cleaned_data
        vol_name = cd["vol_name"]
        vol_access = cd["vol_access"]
        vol_type = cd["vol_type"]
        return_dict['vol_name'] = vol_name
        return_dict['vol_access'] = vol_access
        return_dict['vol_type'] = vol_type
        init = {}
        init["vol_name"] = vol_name
        init["vol_access"] = vol_access
        init["vol_type"] = vol_type
        form = integral_view.forms.volume_creation_forms.VolOndiskStorageForm(initial=init)
        url = "vol_create_wiz_ondisk_storage_type.html"
      else:
        url = "vol_create_wiz_vol_type.html"
    elif action == "select_vol_access":
      # Previous form to verify
      form = integral_view.forms.volume_creation_forms.VolumeNameForm(request.POST)
      if form.is_valid():
        cd = form.cleaned_data
        vol_name = cd["volume_name"]
        return_dict['vol_name'] = vol_name
        init = {}
        init["vol_name"] = vol_name
        form = integral_view.forms.volume_creation_forms.VolAccessMethodForm(initial=init)
        url = "vol_create_wiz_vol_access.html"
      else:
        url = "vol_create_wiz_vol_name.html"
    elif action == "repl_count":
      # Previous form to verify
      form = integral_view.forms.volume_creation_forms.VolTypeForm(request.POST)
      if form.is_valid():
        cd = form.cleaned_data
        return_dict['vol_type'] = cd['vol_type']
        return_dict['vol_name'] = cd['vol_name']
        # Next form to generate and display
        form = integral_view.forms.volume_creation_forms.ReplicationCountForm(vol_name = cd['vol_name'], vol_type=cd["vol_type"])
        url = "vol_create_wiz_repl_count.html"
      else:
        url = "vol_create_wiz_vol_type.html"
    else:
      raise Exception("Unknown action. Please use the menus.")
  
    return_dict['form'] = form
    return django.shortcuts.render_to_response(url, return_dict, context_instance=django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

      
def create_volume_conf(request):
  """ Used to confirm volume creation parameters"""

  return_dict = {}
  try:
    si, err = system_info.load_system_config()
    if err:
      raise Exception(err)
    if not si:
      raise Exception('Could not load system information')
  
    form = integral_view.forms.volume_creation_forms.VolOndiskStorageForm(request.POST or None)
  
    if form.is_valid():
      cd = form.cleaned_data
      vol_type = cd['vol_type']
      vol_name = cd['vol_name']
      ondisk_storage = cd['ondisk_storage']
      vol_access = cd['vol_access']
      repl_count = 2
      if vol_type == "replicated":
        # repl_count = int(cd["repl_count"])
        # Hardcoded to 2 for now till we resolve the hot spare issue
        repl_count = 2
      transport = "TCP"
  
      iv_logging.info("create volume initiated for vol_type %s, vol_name %s, ondisk_storage %s, vol_access %s"%(vol_type, vol_name, ondisk_storage, vol_access))
      d, err = gluster_commands.build_create_volume_command(vol_name, vol_type, ondisk_storage, repl_count, transport, si)
      if err:
        raise Exception(err)
      if d and "error" in d:
        return_dict["error"] = "Error creating the volume : %s"%d["error"]
        return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))
  
      node_list_str = ('<ul>')
      for n in d["node_list"]:
        node_list_str += '<li>'
        for i in n:
          node_list_str += str(i)
          node_list_str += ', '
        node_list_str += '</li>'
      node_list_str += '</ul>'
    
      iv_logging.debug("create vol node list %s"%node_list_str)
      return_dict['cmd'] = d['cmd']
      return_dict['dataset_list'] = d['dataset_list']
      return_dict['node_list_str'] = node_list_str
      return_dict['vol_type'] = vol_type
      return_dict['vol_name'] = vol_name
      return_dict['vol_access'] = vol_access
      return_dict['ondisk_storage'] = ondisk_storage
      if vol_type == "replicated":
        return_dict['repl_count'] = str(repl_count)
  
    else:
      #Invalid form
      url = 'vol_create_wiz_vol_type.html'
      return_dict['form'] = form
      return django.shortcuts.render_to_response(url, return_dict, context_instance = django.template.context.RequestContext(request))
  
    if settings.APP_DEBUG:
      return_dict['app_debug'] = True
  
    return_dict['form'] = form
    return django.shortcuts.render_to_response('vol_create_wiz_confirm.html', return_dict, context_instance = django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

  
def create_volume(request):
  """ Used to actually create the volume"""
  
  return_dict = {}
  try:
  
    if request.method != "POST":
      raise Exception("Invalid access method. Please use the menus.")
  
    if 'cmd' not in request.POST or 'dataset_list' not in request.POST:
      raise Exception('Required parameters not passed.')
    cmd = request.POST['cmd']
    dsl = request.POST.getlist('dataset_list')
    dataset_dict = {}
    for ds in dsl:
      tl = ds.split(':')
      dataset_dict[tl[0]] = tl[1]
  
  
    iv_logging.info("create volume command %s"%cmd)
    #First create the datasets on which the bricks will reside
    client = salt.client.LocalClient()
    revert_list = []
    errors = ""
    for node, dataset in dataset_dict.items():
      dataset_cmd = 'zfs create %s'%dataset
      dataset_revert_cmd = 'zfs destory %s'%dataset
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
  
    #Underlying storage created so now create the volume
    devel_files_path, err = common.get_devel_files_path()
    d, errors = gluster_commands.run_gluster_command("%s force"%cmd, "%s/create_volume.xml"%devel_files_path, "Volume creation")
    if d and ("op_status" in d) and d["op_status"]["op_ret"] == 0:
      #print rc, ret
      #All ok so mount and change the owner and group of the volume to integralstor
      (ret, rc), err = command.execute_with_rc("gluster volume set "+request.POST['vol_name']+" storage.owner-gid 500")
      (ret, rc), err = command.execute_with_rc("gluster volume start "+request.POST['vol_name'])
      (ret, rc), err = command.execute_with_rc("mount -t glusterfs localhost:/"+request.POST['vol_name']+" /mnt")
      (ret, rc), err = command.execute_with_rc("chmod 770 /mnt")
      (ret, rc), err = command.execute_with_rc("umount /mnt")
      (ret, rc), err = command.execute_with_conf_and_rc("gluster volume stop "+request.POST['vol_name'])
      #Success so audit the change
      audit_str = "Create "
      if request.POST["vol_type"] in ["replicated"]:
        audit_str = audit_str + "replicated (count %d) "%int(request.POST["repl_count"])
      else:
        audit_str = audit_str + "distributed  "
      audit_str = audit_str + " volume named %s"%request.POST["vol_name"]
      ret, err = audit.audit("create_volume", audit_str, request.META["REMOTE_ADDR"])
      if err:
        raise Exception(err)
      if request.POST["vol_access"] == "iscsi":
        ret, err = iscsi.add_iscsi_volume(request.POST["vol_name"])
        if err:
          raise Exception(err)
    else:
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
    if errors:
      raise Exception(errors)
  
    if request.POST['vol_type'] == 'replicated':
      return_dict['repl_count'] = request.POST['repl_count']
    return_dict['vol_type'] = request.POST['vol_type']
    return_dict['vol_name'] = request.POST['vol_name']
    return_dict['node_list_str'] = request.POST['node_list_str']
    return_dict['cmd'] = cmd
    return_dict['result_dict'] = d

    return django.shortcuts.render_to_response('vol_create_wiz_result.html', return_dict, context_instance = django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


