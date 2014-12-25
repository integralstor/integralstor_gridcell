
import urllib

import django, django.template
from django.contrib import auth
from django.conf import settings

import fractalio
from fractalio import command, common, volume_info, system_info, audit, gluster_commands

import integral_view
from integral_view.forms import trusted_pool_setup_forms

def perform_op(request, op, name1=None, name2= None):
  """ Used to translate an operation name specified in the op param into an actual command and return the results
  name1 and name2 are extra parameters to the operations"""

  return_dict = {}

  scl = system_info.load_system_config()
  return_dict['system_config_list'] = scl

  # Actual command processing begins

  #By default show error page
  template = "logged_in_error.html"

  if not op:
    return_dict["error"] = "Operation not specified"
    return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))

  audit_code = None
  audit_str = None
  if op == 'add_server':
    command = 'gluster peer probe '+hostname
  elif op == 'remove_server':
    command = 'gluster peer detach '+hostname
  elif op == 'view_server_status':
    command = 'gluster peer status'
  elif op == 'view_volume_status_all':
    command = 'gluster volume status '
  elif op == 'view_volume_info_all':
    command = 'gluster volume info all '
  elif op == 'enable_quota':
    command = 'gluster volume quota %s enable'%name1
  elif op == 'vol_stop':
    command = 'gluster volume stop %s force'%name1
    audit_code = "vol_stop"
    audit_str = "Stopped volume %s"%name1
  elif op == 'vol_delete':
    command = 'gluster volume delete %s force'%name1
  elif op == 'start_rebalance':
    command = 'gluster volume rebalance %s start'%name1
    audit_code = "vol_rebalance_start"
    audit_str = "Started volume rebalance for volume %s"%name1
  elif op == 'stop_rebalance':
    command = 'gluster volume rebalance %s stop'%name1
    audit_code = "vol_rebalance_stop"
    audit_str = "Stopped volume rebalance for volume %s"%name1
  elif op == 'check_rebalance':
    command = 'gluster volume rebalance %s status'%name1
  elif op == 'disable_quota':
    command = 'gluster volume quota %s disable'%name1
  elif op == 'display_disk_level_quota':
    command = 'gluster volume quota %s list'%name1
  elif op == 'vol_start':
    command = 'gluster volume start %s '%name1
    audit_code = "vol_start"
    audit_str = "Started volume %s"%name1
  elif op == 'rotate_log':
    command = 'gluster volume log rotate %s '%name1
    audit_code = "log_rotate"
    audit_str = "Rotated log for volume %s"%name1
  elif op == 'expand_volume':
    command = 'gluster volume add brick %s %s'%(name1, urllib.unquote(name2))
  else:
    return_dict["error"] = "Unknown operation specified"

  template = 'render_op_results.html'
  if "error" not in return_dict:
    if op in ["vol_stop", "vol_start"]:
      if op == "vol_stop":
        d = gluster_commands.volume_stop_or_start(name1, "stop")
      elif op == "vol_start":
        d = gluster_commands.volume_stop_or_start(name1, "start")
      if d:
        if ("op_status" in d) and d["op_status"]["op_ret"] == 0 and d["op_status"]["op_errno"] == 115:
          if audit_code:
            audit.audit(audit_code, audit_str, request.META["REMOTE_ADDR"])
        if op == "vol_stop":
          d["command"] = "Stopping volume %s"%name1
        elif op == "vol_start":
          d["command"] = "Starting volume %s"%name1
      return_dict["result_dict"] = d
      return_dict["op"] = op
      template = 'render_op_xml_results.html'

    else:
      #Non XML raw results so display raw for now


      return_dict['cmd'] = command
      if not fractalio.common.is_production():
        command = 'ls -al'

      if audit_code:
        audit.audit(audit_code, audit_str, request.META["REMOTE_ADDR"])
      if op in ['vol_stop', 'vol_delete', 'disable_quota']:
        tup = integral_view.utils.command.execute_with_conf(command)
        e = integral_view.utils.command.get_conf_error_list(tup)
        o = integral_view.utils.command.get_conf_output_list(tup)
      else:
        tup = integral_view.utils.command.execute(command)
        e = integral_view.utils.command.get_error_list(tup)
        o = integral_view.utils.command.get_output_list(tup)
      if e:
        return_dict['cmd_errors'] = e
      if o:
        return_dict['cmd_output'] = o
    
      if op == 'view_volume_status_all':
        # Need to execute two commands for this case!
        if fractalio.common.is_production():
          command = 'gluster volume status all detail'
        else:
          command = 'ls -al'
    
        tup = integral_view.utils.command.execute(command)
        e1 = integral_view.utils.command.get_error_list(tup)
        o1 = integral_view.utils.command.get_output_list(tup)
        if e1:
          if e:
            e.extend(e1)
            return_dict['cmd_errors'] = e
          else:
            return_dict['cmd_errors'] = e1
        if o1:
          if o:
            o.extend(o1)
            return_dict['cmd_output'] = o
          else:
            return_dict['cmd_output'] = o1
  
      return_dict['op'] = op

  if settings.APP_DEBUG:
    return_dict['app_debug'] = True 


  return django.shortcuts.render_to_response(template, return_dict, context_instance = django.template.context.RequestContext(request))
