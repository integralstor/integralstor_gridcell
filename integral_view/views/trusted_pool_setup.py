
import socket

from django.conf import settings
import django, django.template

import integral_view
from integral_view.forms import trusted_pool_setup_forms
from integral_view.utils import iv_logging

import fractalio
from fractalio import volume_info, system_info, audit, gluster_commands

def add_nodes(request):
  """ Used to add servers to the trusted pool"""

  return_dict = {}

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
    for n in nl:
      dbg_node_list.append(n.keys()[0])
    iv_logging.debug("Initiating add nodes for %s"%' '.join(dbg_node_list))
    ol = gluster_commands.add_nodes(nl)
    for d in ol:
      if d and ("op_status" in d) and d["op_status"]["op_ret"] == 0:
        audit.audit("add_storage", d["audit_str"], request.META["REMOTE_ADDR"])

    return_dict['result_list'] = ol

    if settings.APP_DEBUG:
      return_dict['app_debug'] = True 

    url =  'add_server_results.html'

  return django.shortcuts.render_to_response(url, return_dict, context_instance = django.template.context.RequestContext(request))


def remove_node(request):

  vil = volume_info.get_volume_info_all()
  si = system_info.load_system_config()

  return_dict = {}
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
        cd = form.cleaned_data
        node = cd["node"]
        iv_logging.info("Removing node '%s'"%node)
        d = gluster_commands.remove_node(si, node)
        if d and ("op_status" in d) and d["op_status"]["op_ret"] == 0:
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
