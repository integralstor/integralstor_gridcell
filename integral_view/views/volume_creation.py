import django, django.http
from django.conf import settings
from django.contrib import auth

import random
import logging

import integral_view
from integral_view.forms import volume_creation_forms
from integral_view.utils import command, volume_info, system_info, audit, gluster_commands, iv_logging
from integral_view.iscsi import iscsi

def volume_creation_wizard(request, action):
  """ Used to redirect requests to step a user through a wizrd 
  to create a volume"""

  return_dict = {}

  if not action:
    return_dict["error"] = "Unspecified action. Please try again."
    return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))

  if action == "select_vol_name":
    assert request.method == "GET"
    form = integral_view.forms.volume_creation_forms.VolumeNameForm()
    return_dict['form'] = form
    return django.shortcuts.render_to_response('vol_create_wiz_vol_name.html', return_dict, context_instance=django.template.context.RequestContext(request))
  else:
    assert request.method == "POST"

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
    return_dict["error"] = "Unknown action. Please try again."
    return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))

  return_dict['form'] = form
  return django.shortcuts.render_to_response(url, return_dict, context_instance=django.template.context.RequestContext(request))
    
def create_volume_conf(request):
  """ Used to confirm volume creation parameters"""

  return_dict = {}
  scl = system_info.load_system_config()

  form = integral_view.forms.volume_creation_forms.VolOndiskStorageForm(request.POST or None)

  if form.is_valid():
    cd = form.cleaned_data
    try:
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
    except Exception as e:
      return_dict["error"] = "Required information not provided : %s"%str(e)
      return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))

    iv_logging.info("create volume initiated for vol_type %s, vol_name %s, ondisk_storage %s, vol_access %s"%(vol_type, vol_name, ondisk_storage, vol_access))
    d = gluster_commands.build_create_volume_command(vol_name, vol_type, ondisk_storage, repl_count, transport, scl)
    if "error" in d:
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

def create_volume(request):
  """ Used to actually create the volume"""

  scl = system_info.load_system_config()

  return_dict = {}

  assert request.method == "POST"
  cmd = request.POST['cmd']
  if not settings.PRODUCTION:
    cmd = 'ls -al'

  iv_logging.info("create volume command %s"%cmd)
  d = gluster_commands.run_gluster_command(cmd, "%s/create_volume.xml"%settings.BASE_FILE_PATH, "Volume creation")

  if d and ("op_status" in d) and d["op_status"]["op_ret"] == 0:
    #Success so audit the change
    audit_str = "Create "
    if request.POST["vol_type"] in ["replicated"]:
      audit_str = audit_str + "replicated (count %d) "%int(request.POST["repl_count"])
    else:
      audit_str = audit_str + "distributed  "
    audit_str = audit_str + " volume named %s"%request.POST["vol_name"]
    audit.audit("create_volume", audit_str, request.META["REMOTE_ADDR"])
    if request.POST["vol_access"] == "iscsi":
      iscsi.add_iscsi_volume(request.POST["vol_name"])

  if request.POST['vol_type'] == 'replicated':
    return_dict['repl_count'] = request.POST['repl_count']
  return_dict['vol_type'] = request.POST['vol_type']
  return_dict['vol_name'] = request.POST['vol_name']
  return_dict['node_list_str'] = request.POST['node_list_str']
  return_dict['cmd'] = cmd
  return_dict['result_dict'] = d

  return django.shortcuts.render_to_response('vol_create_wiz_result.html', return_dict, context_instance = django.template.context.RequestContext(request))
