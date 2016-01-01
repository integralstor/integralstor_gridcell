
import socket

from django.conf import settings
import django, django.template

import integral_view
from integral_view.forms import trusted_pool_setup_forms
from integral_view.utils import iv_logging

import integralstor_gridcell
from integralstor_gridcell import volume_info, system_info, gluster_commands, grid_ops
from integralstor_common import audit

def add_nodes_to_pool(request):
  """ Used to add servers to the trusted pool"""

  return_dict = {}
  try:
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
    nl, err = system_info.get_available_node_list(si)
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
            audit.audit("add_storage", d["audit_str"], request.META["REMOTE_ADDR"])
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


def add_a_node_to_pool(request):
  """ Used to add servers to the trusted pool"""

  return_dict = {}
  try:
    return_dict['base_template'] = "gridcell_base.html"
    return_dict["page_title"] = 'Add a GRIDCell to the storage pool'
    return_dict['tab'] = 'gridcell_list_tab'
    return_dict["error"] = 'Error adding a GRIDCell to the storage pool'

    error_list = []
  
    if request.method != 'POST':
      raise Exception('Invalid access. Please try using the menus')

    if 'node_name' not in request.POST:
      raise Exception('Invalid request. Please try using the menus')
    node_name = request.POST['node_name']

    si, err = system_info.load_system_config()
    if err:
      raise Exception(err)
    return_dict['system_info'] = si
  
    # Get list of possible nodes that are available
    nl, err = system_info.get_available_node_list(si)
    if err:
      raise Exception(err)
    if nl:
      anl = []
      for n in nl:
        anl.append(n['hostname'])
      if not anl or node_name not in anl:
        raise Exception('The specified GRIDCell cannot be added to the storage grid. This could be because it is unhealthy or because it is already part of the grid')
  
    d, errors = grid_ops.add_a_node_to_storage_pool(si, node_name)
    if errors:
      raise Exception(errors)
    if d:
      if  ("op_status" in d) and d["op_status"]["op_ret"] == 0:
        audit.audit("add_storage", d["audit_str"], request.META["REMOTE_ADDR"])
      else:
        err = 'Operation failed : Error number : %s, Error : %s, Output : %s, Additional info : %s'%(d['op_status']['op_errno'], d['op_status']['op_errstr'], d['op_status']['output'], d['op_status']['error_list'])
        raise Exception(err)
    else:
      raise Exception('Could not add the GRIDCell %s to the grid.'%node_name)

    return django.http.HttpResponseRedirect('/show/gridcells?action=added_to_storage_pool')
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

def remove_node_from_pool(request):

  return_dict = {}
  try:
    return_dict['base_template'] = "gridcell_base.html"
    return_dict["page_title"] = 'Remove a GRIDCell from the storage pool'
    return_dict['tab'] = 'gridcell_list_tab'
    return_dict["error"] = 'Error removing a GRIDCell from the storage pool'

    si, err = system_info.load_system_config()
    if err:
      raise Exception(err)
    '''
    vil, err = volume_info.get_volume_info_all()
    if err:
      raise Exception(err)
  
    return_dict['system_info'] = si
    nl = []
    localhost = socket.getfqdn().strip()
    for hostname in si.keys():
      if hostname == localhost:
        continue
      if si[hostname]["in_cluster"] and (not si[hostname]["volume_list"]):
        nl.append(hostname)
    return_dict['node_list'] = nl
    iv_logging.debug("Remove node node list %s"%' '.join(nl))
    '''
  
    if request.method == "GET":
      if 'node_name' not in request.GET:
        raise Exception('GRIDCell not chosen. Please use the menus')
      return_dict['node_name'] = request.GET['node_name']
      url = 'remove_node_from_grid_conf.html'
      
      '''
      form = trusted_pool_setup_forms.RemoveNodeForm(node_list = nl)
      url = 'remove_node_form.html'
      '''
    else:
      if 'node_name' not in request.POST:
        raise Exception('GRIDCell not specified. Please use the menus')
      node_name = request.POST['node_name']
      d, error = grid_ops.remove_a_node_from_storage_pool(si, node_name)
      #if error:
      #  raise Exception(error)
      return_dict['node_name'] = node_name
      return_dict['error'] = error
      return_dict['result_dict'] = d
      if not error:
        audit_str =  "Removed GRIDCell from the storage pool %s"%node_name
        audit.audit("remove_storage", audit_str, request.META["REMOTE_ADDR"])
      return_dict["result_dict"] = d
      url = 'remove_node_result.html'
      '''
      if "conf" in request.POST:
        #got final conf so process
        form = trusted_pool_setup_forms.RemoveNodeConfForm(request.POST)
        if form.is_valid():
          rd = {}
          cd = form.cleaned_data
          node = cd["node"]
          iv_logging.info("Removing node '%s'"%node)
          d, error = grid_ops.remove_a_node_from_storage_pool(si, node)
          print d, error

          return_dict['result_code'] = rc
          return_dict['node_name'] = node
          return_dict['result_dict'] = d
          if error:
            return_dict['errors'] = error
          if not error:
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
      '''
  
    #return_dict['form'] = form
    if settings.APP_DEBUG:
      return_dict['app_debug'] = True
    return django.shortcuts.render_to_response(url, return_dict, context_instance=django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


