
import socket

from django.contrib import auth
from django.conf import settings
import django, django.template

import integral_view
from integral_view.forms import trusted_pool_setup_forms
from integral_view.utils import volume_info, system_info, host_info, audit, gluster_commands, iv_logging


'''
def server_op(request, op):
  """ Used to present an appropriate form to either add or remove a node from a trusted pool"""

  return_dict = {}

  try:
    assert request.method == 'GET'
  except Exception as e:
    return_dict["error"] = "Invalid use of this functionality"
    return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))

  if not op or op not in ["add_servers", "remove_sled"]:
    return_dict["error"] = "Invalid operation"
    return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))

  vil = volume_info.get_volume_info_all()
  scl = system_info.load_system_config()
  return_dict['system_config_list'] = scl

  if op == "remove_sled":

    sl = volume_info.get_removable_sled_list(scl, vil)
    return_dict['sled_list'] = sl
    form = trusted_pool_setup_forms.RemoveSledForm(sled_list = sl)
    url = 'remove_sled_form.html'

  elif op == "add_servers":

    # Get list of possible nodes that are available
    nl = system_info.get_available_node_list(scl)

    # From that get the spare sled
    spare_sled = system_info.get_spare_sled(scl, nl)
    if spare_sled == -1:
      error
    else:
      # Remove the spare sled nodes and the local host nodes and return the rest of the list
      anl = system_info.get_addable_node_list(nl, spare_sled)

    if system_info.prompt_for_spare(nl):
        return_dict["prompt_for_spare"] = True

    form = trusted_pool_setup_forms.AddServersForm(addable_node_list = anl)
    
    # If there are more than one free sleds, reserve one for a hot spare
    # If only one then warn the user they are adding the hot spare.

    return_dict["free_sled_list"] = sl
    url = 'add_servers_form.html'
  else:
    return_dict["error"] = "Unknown operation. Please use the menus"
    url = 'logged_in_error.html'

  display_node_list = system_info.generate_display_node_list(scl)
  return_dict["display_node_list"] = display_node_list
  return_dict['colour_dict'] = settings.DISPLAY_COLOURS
  return_dict['form'] = form
  if settings.APP_DEBUG:
    return_dict['app_debug'] = True
  return_dict['op'] = op
  return django.shortcuts.render_to_response(url, return_dict, context_instance=django.template.context.RequestContext(request))

'''

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
        ol = gluster_commands.remove_node(si, node)
        audit_str = ""
        for d in ol:
          if "audit_str" in d:
            audit_str = audit_str + d["audit_str"] + ", "
        audit.audit("remove_storage", audit_str, request.META["REMOTE_ADDR"])
        return_dict["result_list"] = ol

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
  return_dict['colour_dict'] = settings.DISPLAY_COLOURS
  if settings.APP_DEBUG:
    return_dict['app_debug'] = True
  return django.shortcuts.render_to_response(url, return_dict, context_instance=django.template.context.RequestContext(request))

  


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


  '''
  # From that get the spare sled
  spare_sled = system_info.get_spare_sled(scl, nl)

  if system_info.prompt_for_spare(nl):
      return_dict["prompt_for_spare"] = True

  if spare_sled == -1:
    return_dict["warn_no_spare"] = True
    anl = nl
  else:
    # Remove the spare sled nodes and the local host nodes and return the rest of the list
    if "prompt_for_spare" in return_dict:
      #Allow adding spare
      anl = nl
    else:
      #Exclude spare
      anl = system_info.get_addable_node_list(nl, spare_sled)
    return_dict["spare_sled"] = spare_sled

  if not anl:
    #Nothing available to add so show that message and bail out!
    return_dict["no_available_nodes"] = True
    return django.shortcuts.render_to_response('add_servers_form.html', return_dict, context_instance = django.template.context.RequestContext(request))

  '''




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
    iv_logging.debug("Initiating add nodes for %s"%' '.join(nl))
    ol = gluster_commands.add_servers(nl)
    audit_str = ""
    for d in ol:
      if "audit_str" in d:
        audit_str = audit_str + d["audit_str"] + ", "
    if audit:
      audit.audit("add_storage", audit_str, request.META["REMOTE_ADDR"])

    return_dict['result_list'] = ol

    if settings.APP_DEBUG:
      return_dict['app_debug'] = True 

    url =  'add_server_results.html'

  return django.shortcuts.render_to_response(url, return_dict, context_instance = django.template.context.RequestContext(request))

