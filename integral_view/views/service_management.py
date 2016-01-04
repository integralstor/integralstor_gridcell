# Workflow : UI to select a node, query the node to get all the service details. And perform action accordingly on that node.
import django
import salt.client
from datetime import datetime
from integralstor_common import scheduler_utils,common
from integralstor_gridcell import services
from integralstor_gridcell.services import default_services


#Exception handlings to be written to all the code below
def get_service_status(request):
  return_dict = {}
  return_dict['service_status'] = {}
  try:
    service_status,err = services.get_service_status()
    if not err:
      return_dict['service_status'] = service_status
      return django.shortcuts.render_to_response("view_service_status.html", return_dict, context_instance=django.template.context.RequestContext(request))
    else:
      return_dict["error"] = 'Unable to retrive the status of services'
      return_dict["error_details"] = "An error occurred when processing your request : %s"%err
      return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
  except Exception, e:
    return_dict["error"] = 'Unable to retrive the status of services'
    return_dict["error_details"] = "An error occurred when processing your request : %s"%e
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


def node_service_action(request):
  return_dict = {}
  try:
    if request.method == "POST":
        service = request.POST.get('service')
        action = request.POST.get('action')
        node = request.POST.get('node')
        status,err = services.service_action(node,default_services[service],action)
        if err:
          return_dict["error"] = "%s %s failed."%(service,action)
          return_dict["error_details"] = "The system could not locate a service with name '%s' .Please redo the operation. If this problem persists, contact for support."%service
          return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

        return django.http.HttpResponseRedirect('/view_service_status/?status=success&service=%s&action=%s&node=%s'%(service,action,node))
    else:
      return_dict["error"] = "Please use the menus and screens to access this page"
      return_dict["error_details"] = "You seem to have accessed this page by changing the url. This will not work as intended. Please go back to the old screen and redo the operation"
      return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
  except Exception, e:
    return_dict["error"] = 'Unable to retrive the status of services'
    return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

def initiate_scrub(request):
  return_dict = {}
  try:
    if request.method == "GET":
      return django.shortcuts.render_to_response("initiate_scrub.html", return_dict, context_instance=django.template.context.RequestContext(request))
    elif request.method == "POST":
      dt = request.POST.get('timestamp')
      poolname = 'frzpool'
      db_path,err = common.get_db_path()
      status,err = scheduler_utils.schedule_a_job(db_path,'ZFS Scrub',[{'scrub':'zpool scrub frzpool'}],int(dt))
      if err:
        return_dict["error"] = "Scrub scheduling failed"
        return_dict["error_details"] = err
        return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
      return django.shortcuts.render_to_response("initiate_scrub.html", return_dict, context_instance=django.template.context.RequestContext(request))
  except Exception, e:
    return_dict["error"] = 'Unable to retrive the status of services'
    return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
