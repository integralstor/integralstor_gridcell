
import socket

from django.conf import settings
import django, django.template

import integral_view
from integral_view.forms import trusted_pool_setup_forms
from integral_view.utils import iv_logging

import fractalio
from fractalio import volume_info, system_info, audit, gluster_commands, grid_ops

def add_nodes_to_pool(request):
  """ Used to add servers to the trusted pool"""

  return_dict = {}
  try:
    error_list = []
  
    si = system_info.load_system_config()
    return_dict['system_info'] = si
  
    # Get list of possible nodes that are available
    nl = system_info.get_available_node_list(si)
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
        rc, d, el = grid_ops.add_a_node_to_storage_pool(si, node["hostname"])
        if rc == 0 and d:
          if d and ("op_status" in d) and d["op_status"]["op_ret"] == 0:
            audit.audit("add_storage", d["audit_str"], request.META["REMOTE_ADDR"])
        hostname = node["hostname"]
        td['rc'] = rc
        td['d'] = rc
        td['error_list'] = el
        rd[hostname] = td
        if el:
          error_list.extend(el)

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
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))



def remove_node_from_pool(request):

  return_dict = {}
  try:
    vil = volume_info.get_volume_info_all()
    si = system_info.load_system_config()
  
    return_dict['system_info'] = si
    nl = []
    localhost = socket.gethostname().strip()
    for hostname in si.keys():
      if hostname == localhost:
        continue
      if si[hostname]["in_cluster"] and (not si[hostname]["volume_list"]):
        nl.append(hostname)
    return_dict['node_list'] = nl
    iv_logging.debug("Remove node node list %s"%' '.join(nl))
  
    if request.method == "GET":
      form = trusted_pool_setup_forms.RemoveNodeForm(node_list = nl)
      url = 'remove_node_form.html'
    else:
      if "conf" in request.POST:
        #got final conf so process
        form = trusted_pool_setup_forms.RemoveNodeConfForm(request.POST)
        if form.is_valid():
          rd = {}
          cd = form.cleaned_data
          node = cd["node"]
          iv_logging.info("Removing node '%s'"%node)
          rc, d, error_list = grid_ops.remove_a_node_from_storage_pool(si, node)

          return_dict['result_code'] = rc
          return_dict['node_name'] = node
          return_dict['result_dict'] = d
          if error_list:
            return_dict['error_list'] = error_list
          if rc == 0:
            audit_str =  "Removed node %s"%node
            audit.audit("remove_storage", audit_str, request.META["REMOTE_ADDR"])
          return_dict["result_dict"] = d
          url = 'remove_node_result.html'
      else:
        #send for conf if form ok
        form = trusted_pool_setup_forms.RemoveNodeForm(request.POST, node_list = nl)
        if form.is_valid():
          cd = form.cleaned_data
          node = cd["node"]
          return_dict["node"] = node
          url = 'remove_node_conf.html'
        else:
          #invalid form so send back
          url = 'remove_node_form.html'
  
    return_dict['form'] = form
    if settings.APP_DEBUG:
      return_dict['app_debug'] = True
    return django.shortcuts.render_to_response(url, return_dict, context_instance=django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


