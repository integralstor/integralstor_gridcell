
import urllib

import django, django.template
from django.contrib import auth
from django.conf import settings

import fractalio
from fractalio import command, common, volume_info, system_info, audit, gluster_commands

import integral_view
from integral_view.forms import trusted_pool_setup_forms

def perform_op(request, op, name1=None, name2= None):
  """ Used to translate an operation name specified in the op param into an actual cmd and return the results
  name1 and name2 are extra parameters to the operations"""

  return_dict = {}
  try:
    scl = system_info.load_system_config()
    return_dict['system_config_list'] = scl
  
    # Actual cmd processing begins
  
    #By default show error page
    template = "logged_in_error.html"
  
    if not op:
      return_dict["error"] = "Operation not specified"
      return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))
  
    audit_code = None
    audit_str = None
    if op == 'add_server':
      cmd = 'gluster peer probe '+hostname
    elif op == 'remove_server':
      cmd = 'gluster peer detach '+hostname
    elif op == 'view_server_status':
      cmd = 'gluster peer status'
    elif op == 'view_volume_status_all':
      cmd = 'gluster volume status '
    elif op == 'view_volume_info_all':
      cmd = 'gluster volume info all '
    elif op == 'enable_quota':
      cmd = 'gluster volume quota %s enable'%name1
    elif op == 'vol_stop':
      cmd = 'gluster volume stop %s force'%name1
      audit_code = "vol_stop"
      audit_str = "Stopped volume %s"%name1
    elif op == 'vol_delete':
      cmd = 'gluster volume delete %s force'%name1
    elif op == 'start_rebalance':
      cmd = 'gluster volume rebalance %s start'%name1
      audit_code = "vol_rebalance_start"
      audit_str = "Started volume rebalance for volume %s"%name1
    elif op == 'stop_rebalance':
      cmd = 'gluster volume rebalance %s stop'%name1
      audit_code = "vol_rebalance_stop"
      audit_str = "Stopped volume rebalance for volume %s"%name1
    elif op == 'check_rebalance':
      cmd = 'gluster volume rebalance %s status'%name1
    elif op == 'disable_quota':
      cmd = 'gluster volume quota %s disable'%name1
    elif op == 'display_disk_level_quota':
      cmd = 'gluster volume quota %s list'%name1
    elif op == 'vol_start':
      cmd = 'gluster volume start %s '%name1
      audit_code = "vol_start"
      audit_str = "Started volume %s"%name1
  
    elif op == 'rotate_log':
      cmd = 'gluster volume log rotate %s '%name1
      audit_code = "log_rotate"
      audit_str = "Rotated log for volume %s"%name1
    elif op == 'expand_volume':
      cmd = 'gluster volume add brick %s %s'%(name1, urllib.unquote(name2))
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
            d["cmd"] = "Stopping volume %s"%name1
          elif op == "vol_start":
            d["cmd"] = "Starting volume %s"%name1
            fractalio.command.execute("[ ! -d /mnt/perm_vol ] && mkdir /mnt/perm_vol")
            fractalio.command.execute("umount /mnt/perm_vol/")
            fractalio.command.execute(" mount -t glusterfs localhost:/"+name1+" /mnt/perm_vol/")
            fractalio.command.execute("chmod -R 775 /mnt/perm_vol/")
            fractalio.command.execute("umount /mnt/perm_vol/")
  
        return_dict["result_dict"] = d
        return_dict["op"] = op
        template = 'render_op_xml_results.html'
  
      else:
        #Non XML raw results so display raw for now
  
  
        return_dict['cmd'] = cmd
        if not fractalio.common.is_production():
          cmd = 'ls -al'
  
        if audit_code:
          audit.audit(audit_code, audit_str, request.META["REMOTE_ADDR"])
        if op in ['vol_stop', 'vol_delete', 'disable_quota']:
          tup = fractalio.command.execute_with_conf(cmd)
          e = fractalio.command.get_conf_error_list(tup)
          o = fractalio.command.get_conf_output_list(tup)
        else:
          tup = fractalio.command.execute(cmd)
          e = fractalio.command.get_error_list(tup)
          o = fractalio.command.get_output_list(tup)
        if e:
          return_dict['cmd_errors'] = e
        if o:
          return_dict['cmd_output'] = o
      
        if op == 'view_volume_status_all':
          # Need to execute two cmds for this case!
          if fractalio.common.is_production():
            cmd = 'gluster volume status all detail'
          else:
            cmd = 'ls -al'
      
          tup = fractalio.command.execute(cmd)
          e1 = fractalio.command.get_error_list(tup)
          o1 = fractalio.command.get_output_list(tup)
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
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

