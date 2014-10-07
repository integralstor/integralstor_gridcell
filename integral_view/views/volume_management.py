import re

import django.http, django
from  django.contrib import auth
from django.conf import settings

import integral_view
from integral_view.forms import volume_management_forms
from integral_view.utils import command, volume_info, system_info, audit, gluster_commands
from integral_view.iscsi import iscsi

def volume_specific_op(request, operation, vol_name=None):
  """ Used to carry out various volume related operations which is specified in the operation parameter. 
  The volume to be operated on is specified in the vol_name parameter"""

  if not operation:
    return_dict["error"] = "Operation not specified."
    return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))

  return_dict = {}
  return_dict['op'] = operation
  form = None

  vil = volume_info.get_volume_info_all()
  #scl = system_info.load_system_config()
  si = system_info.load_system_config()

  if request.method == "GET":

    if operation == "vol_start":
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
      il = iscsi.load_iscsi_volumes_list(vil)
      l = []
      for v in vil:
        #Ignore ISCSI volumes for this
        if il and v["name"] in il:
          continue
        l.append(v["name"])
      form = integral_view.forms.volume_management_forms.VolumeNameForm(vol_list = l)
      if not l:
        return_dict["no_vols"] = True
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
    else:
      l = []
      for v in vil:
        l.append(v["name"])
      form = integral_view.forms.volume_management_forms.VolumeNameForm(request.POST, vol_list = l)
    if form.is_valid():
      cd = form.cleaned_data
      try:
        vol_name = cd['vol_name']
      except Exception:
        return_dict["error"] = "Volume name not specified."
        return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))
      return_dict['vol_name'] = vol_name
      if operation in ['vol_stop', 'vol_delete']:
        return_dict['op_conf_msg'] = op_conf_msg[operation]
        return django.shortcuts.render_to_response('volume_specific_op_conf.html', return_dict, context_instance=django.template.context.RequestContext(request))
      elif operation == 'vol_quota':
        init = {}
        init["vol_name"] = vol_name
        vd = volume_info.get_volume_info(None, vol_name)
        enable_quota = True
        if "options" in vd :
          for o in vd["options"]:
            if "features.quota" == o["name"]:
              if o["value"] == "on":
                init["set_quota"] = True
                if "quotas" in vd and "/" in vd["quotas"]:
                  q = vd["quotas"]["/"]
                  match = re.search('([0-9]+)([A-Za-z]+)', q["limit"])
                  if match:
                    r  = match.groups()
                    init["limit"] = r[0]
                    init["unit"] = r[1].upper()
        form = volume_management_forms.VolumeQuotaForm(initial=init)
        return_dict["form"] = form
        return django.shortcuts.render_to_response('edit_volume_quota.html', return_dict, context_instance=django.template.context.RequestContext(request))
      elif operation == "vol_options":
        vol_dict = volume_info.get_volume_info(vil, vol_name)
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
              d["nfs_disable"] = option["value"]
            if option["name"] == "nfs.volume-access": 
              d["nfs_volume_access"] = option["value"]
            if option["name"] == "features.read-only": 
              d["readonly"] = option["value"]
        form = integral_view.forms.volume_management_forms.VolumeOptionsForm(initial=d)
        return_dict["form"] = form
        return django.shortcuts.render_to_response('volume_options_form.html', return_dict, context_instance=django.template.context.RequestContext(request))
      elif operation == 'start_rebalance':
        d = gluster_commands.create_rebalance_command_file(vol_name)
        if not "error" in d:
          audit.audit("vol_rebalance_start", "Scheduled volume rebalance start for volume %s"%vol_name, request.META["REMOTE_ADDR"])
          return django.http.HttpResponseRedirect('/show/batch_start_conf/%s'%d["file_name"])
        else:
          return_dict["error"] = "Error initiating rebalance : %s"%d["error"]
          return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))

      elif operation in ['vol_start', 'rotate_log', 'check_rebalance', 'stop_rebalance']:
        return django.http.HttpResponseRedirect('/perform_op/%s/%s'%(operation, vol_name))

      elif operation == 'expand_volume':

        for vol in vil:
          if vol_name == vol["name"]:
            break
        count = 0
        replicated = False
        repl_count = 0

        if vol["type"] == "Replicate":
          replica_count = int(vol["replicaCount"])
          replicated = True

        #d = volume_info.get_expandable_node_list(si, vol, replicated, replica_count) 
        d = gluster_commands.build_expand_volume_command(vol, si)
        if "error" in d:
          return_dict["error"] = "Error creating the volume : %s"%d["error"]
          return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))

        return_dict['cmd'] = d['cmd']
        return_dict['node_list'] = d['node_list']
        return_dict['count'] = d['count']
        return_dict['vol_name'] = vol["name"]
        if vol["type"] == "Replicate":
          return_dict['vol_type'] = "replicated"
        else:
          return_dict['vol_type'] = "distributed"
          

        #form = volume_management_forms.ExpandVolumeForm(vol_name = vol_name, system_config_list = scl, volume_info_list = vil)
        #List of hosts that are part of this volume
        #hosts_in_vol_list = []
        #hosts_in_vol_list = volume_info.get_brick_hostname_list(vol)
        #return_dict['form'] = form
        #return_dict['hosts_in_vol_list'] = hosts_in_vol_list
        #return_dict['system_info'] = si
        #return_dict['vol_type'] = vol["type"]
        #return_dict['replica_count'] = replica_count
        #return_dict['node_list'] = nl
        #return_dict['colour_dict'] = settings.DISPLAY_COLOURS
        #for brick in vol["bricks"]:
        #  hosts_in_vol_list.append(brick["host"])
        return django.shortcuts.render_to_response('expand_volume_form.html', return_dict, context_instance=django.template.context.RequestContext(request))
  # form not valid or called using get so return same form
  return_dict['form'] = form
  if operation == "volume_status":
    return django.shortcuts.render_to_response('volume_specific_status.html', return_dict, context_instance=django.template.context.RequestContext(request))
  else:
    return django.shortcuts.render_to_response('volume_specific_op_form.html', return_dict, context_instance=django.template.context.RequestContext(request))

def set_volume_options(request):

  return_dict = {}
  if request.method == "GET":
    # Disallowed GET method so return error.
    return_dict["error"] = "Invalid request. Please use the menu options."
    return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))
  form = integral_view.forms.volume_management_forms.VolumeOptionsForm(request.POST)

  if not form.is_valid():
    return_dict["form"] = form
    return django.shortcuts.render_to_response('volume_options_form.html', return_dict, context_instance = django.template.context.RequestContext(request))
  cd = form.cleaned_data
  ol = integral_view.utils.gluster_commands.set_volume_options(cd)
  for d in ol:
    if d and ("op_status" in d) and d["op_status"]["op_ret"] == 0:
      #Success so audit the change
      audit.audit("set_vol_options", d["display_command"], request.META["REMOTE_ADDR"])

  return_dict["result_list"] = ol
  return django.shortcuts.render_to_response('volume_options_result.html', return_dict, context_instance = django.template.context.RequestContext(request))

def set_volume_quota(request):
  return_dict = {}
  if request.method == "GET":
    # Disallowed GET method so return error.
    return_dict["error"] = "Invalid request. Please use the menu options."
    return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))

  form = integral_view.forms.volume_management_forms.VolumeQuotaForm(request.POST)

  if not form.is_valid():
    return_dict["form"] = form
    return django.shortcuts.render_to_response('edit_volume_quota.html', return_dict, context_instance = django.template.context.RequestContext(request))
  cd = form.cleaned_data
  vol_name = cd["vol_name"]
  vd = volume_info.get_volume_info(None, vol_name)
  enable_quota = True
  if "options" in vd :
    for o in vd["options"]:
      if o["name"] == "features.quota" and o["value"] == "on":
        enable_quota = False
        break
  ol = integral_view.utils.gluster_commands.set_volume_quota(cd["vol_name"], enable_quota, cd["set_quota"], cd["limit"], cd["unit"])
  for d in ol:
    if d and ("op_status" in d) and d["op_status"]["op_ret"] == 0:
      #Success so audit the change
      audit.audit("set_vol_quota", d["display_command"], request.META["REMOTE_ADDR"])

  return_dict["result_list"] = ol
  return_dict["app_debug"] = True
  return django.shortcuts.render_to_response('volume_quota_result.html', return_dict, context_instance = django.template.context.RequestContext(request))

def delete_volume(request):

  return_dict = {}

  form = None

  vil = volume_info.get_volume_info_all()
  si = system_info.load_system_config()
  return_dict['system_config_list'] = si

  if request.method == "GET":
    return_dict["error"] = "Invalid access. Please use the menus to perform functions."
    return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))
  else:
    if "vol_name" not in request.POST:
      return_dict["error"] = "Volume not specified. Please use the menus to perform functions."
      return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))
    vol_name = request.POST["vol_name"]
    v = volume_info.get_volume_info(vil, vol_name)
    #assert False
    result_list = []
    try:
      d = {}
      cmd = 'gluster --mode=script volume delete %s '%vol_name
      d["command"] = "Deleting volume %s"%vol_name
      d["actual_command"] = cmd
      (r, rc) = command.execute_with_rc(cmd)
      if rc == 0:
        audit.audit("vol_delete", "Deleted volume %s"%(vol_name), request.META["REMOTE_ADDR"])
        # Now delete the brick directories
        d["result"] = "Success"
        result_list.append(d)
        for bricks in  v["bricks"]:
          for b in bricks:
            d = {}
            l = b.split(':')
            d["command"] = "Deleting volume storage on node %s"%l[0]
            print "executing command"
            print "/opt/fractal/bin/client %s rcmd rm -rf %s"%(l[0], l[1])
            d["actual_command"] = "/opt/fractal/bin/client %s rcmd rm -rf %s"%(l[0], l[1])
            (r, rc) = command.execute_with_rc("/opt/fractal/bin/client %s rcmd rm -rf %s"%(l[0], l[1]))
            if rc == 0:
              audit.audit("vol_delete", "Deleted volume data on node %s"%(l[0]), request.META["REMOTE_ADDR"])
              d["result"] = "Success"
              result_list.append(d)
            else:
              el = command.get_error_list(r)
              ol = command.get_output_list(r)
              estr = ""
              if el:
                estr = " , ".join(el)
              if ol:
                estr += " , ".join(ol)
              d["result"] = "Failed with error : %s"%estr
              result_list.append(d)
      else:
        el = command.get_error_list(r)
        ol = command.get_output_list(r)
        estr = ""
        if el:
          estr = " , ".join(el)
        if ol:
          estr += " , ".join(ol)
        d["result"] = "Failed with error : %s"%estr
        result_list.append(d)
    except Exception, e:
      return_dict["error"] = "Error deleting volume %s."%(str(e))
      return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))

    return_dict["result_list"] = result_list
    return_dict["app_debug"] = True
    return django.shortcuts.render_to_response('volume_delete_results.html', return_dict, context_instance = django.template.context.RequestContext(request))

def replace_node(request):

  return_dict = {}

  form = None

  vil = volume_info.get_volume_info_all()
  si = system_info.load_system_config()
  return_dict['system_config_list'] = si

  return_dict['colour_dict'] = settings.DISPLAY_COLOURS
  
  d = volume_info.get_replacement_node_info(si, vil)
  return_dict["src_node_list"] = d["src_node_list"]
  return_dict["dest_node_list"] = d["dest_node_list"]

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

        d = gluster_commands.create_replace_command_file(si, vil, src_node, dest_node)
        if "error" in d:
          return_dict["error"] = "Error initiating replace : %s"%d["error"]
          return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))
        else:
          audit.audit("replace_node", "Scheduled replacement of node %s with node %s"%(src_node, dest_node), request.META["REMOTE_ADDR"])
          return django.http.HttpResponseRedirect('/show/batch_start_conf/%s'%d["file_name"])
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

''' 
def replace_sled(request):

  return_dict = {}

  form = None

  vil = volume_info.get_volume_info_all()
  scl = system_info.load_system_config()
  return_dict['system_config_list'] = scl

  display_node_list = system_info.generate_display_node_list(scl)
  return_dict["display_node_list"] = display_node_list
  return_dict['colour_dict'] = settings.DISPLAY_COLOURS
  
  d = volume_info.get_replacement_sled_info(scl, vil)
  return_dict["src_sled_list"] = d["src_sled_list"]
  return_dict["dest_sled_list"] = d["dest_sled_list"]

  if request.method == "GET":
    form = volume_management_forms.ReplaceSledForm(d["src_sled_list"], d["dest_sled_list"])
    return_dict["form"] = form
    return_dict["supress_error_messages"] = True
    #print "form errors ----->"
    #print form.errors
    return django.shortcuts.render_to_response('replace_sled_choose_sled.html', return_dict, context_instance=django.template.context.RequestContext(request))
  else:
    if "conf" in request.POST:
      form = volume_management_forms.ReplaceSledConfForm(request.POST)
      if form.is_valid():
        cd = form.cleaned_data

        src_sled = cd["src_sled"]
        dest_sled = cd["dest_sled"]

        d = gluster_commands.create_replace_command_file(scl, vil, int(src_sled), int(dest_sled))
        if "error" in d:
          return_dict["error"] = "Error initiating replace : %s"%d["error"]
          return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))
        else:
          audit.audit("replace_sled", "Scheduled replacement of sled %d with sled %d"%(src_sled, dest_sled), request.META["REMOTE_ADDR"])
          return django.http.HttpResponseRedirect('/show/batch_start_conf/%s'%d["file_name"])
    else:
      form = volume_management_forms.ReplaceSledForm(request.POST, src_sled_list = d["src_sled_list"], dest_sled_list = d["dest_sled_list"])
      if form.is_valid():
        cd = form.cleaned_data
        src_sled = cd["src_sled"]
        dest_sled = cd["dest_sled"]
        return_dict["src_sled"] = src_sled
        return_dict["dest_sled"] = dest_sled
        return django.shortcuts.render_to_response('replace_sled_conf.html', return_dict, context_instance=django.template.context.RequestContext(request))
      else:
        return_dict["form"] = form
        return django.shortcuts.render_to_response('replace_sled_choose_sled.html', return_dict, context_instance=django.template.context.RequestContext(request))

''' 


def expand_volume(request):

  return_dict = {}
  form = None

  vil = volume_info.get_volume_info_all()
  #scl = system_info.load_system_config()
  #return_dict['system_config_list'] = scl

  if request.method == "GET":
    # Disallowed GET method so return error.
    return_dict["error"] = "Invalid request. Please use the menu options."
    return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))
  else:
    # POST method processing

    if "cmd" not in request.POST or "vol_name" not in request.POST or "count" not in request.POST:
      return_dict["error"] = "Invalid request. Please use the menu options."
      return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))

    cmd = request.POST['cmd']
    vol_name = request.POST['vol_name']
    count = request.POST['count']

    d = gluster_commands.run_gluster_command(cmd, "%s/add_brick.xml"%settings.BASE_FILE_PATH, "Volume expansion")

    if d and ("op_status" in d) and d["op_status"]["op_ret"] == 0:
      #Success so audit the change
      audit_str = "Expanded volume %s by adding %s storage units."%(vol_name, count)
      audit.audit("expand_volume", audit_str, request.META["REMOTE_ADDR"])

    if d:
      d["command"] = "Volume expansion of %s by adding %s storage units."%(vol_name, count)

    return_dict['result_dict'] = d 
    if settings.APP_DEBUG:
      return_dict['app_debug'] = True 

    return django.shortcuts.render_to_response('render_op_xml_results.html', return_dict, context_instance = django.template.context.RequestContext(request))
