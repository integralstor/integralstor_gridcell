# Workflow : UI to select a node, query the node to get all the service details. And perform action accordingly on that node.
import django
import salt.client

#Global Declaration of services so as to reused everywhere else
services = {'Gluster':'glusterd','CIFS-CTDB':'ctdb','CIFS-Smb':'smb','CIFS-Winbind':'winbind','NTP':'ntpd','NFS':'rpcbind'}

#Exception handlings to be written to all the code below 
def get_service_status(request):
  return_dict = {}
  return_dict['service_status'] = {}
  client = salt.client.LocalClient()
  for name,service in services.items():
     status = client.cmd('*','service.status',[service])
     if not status:
       return_dict["error"] = "Unable to get status of %s(%s)"%(name,service)
       return_dict["error_details"] = "You seem to have accessed this page by changing the url. This will not work as intended. Please go back to the old screen and redo the operation"
       return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
     return_dict['service_status'][name] = status
  return django.shortcuts.render_to_response("view_service_status.html", return_dict, context_instance=django.template.context.RequestContext(request))

def node_service_action(request):
  return_dict = {}
  if request.method == "POST":
    node = request.POST.get('node')
    action = 'service.'+request.POST.get('action')
    service = request.POST.get('service')
    service = services[service]
    client = salt.client.LocalClient()
    status = client.cmd(node,action,[service]) 
    if not False in status.values():
      return django.http.HttpResponseRedirect('/view_service_status/')
    else:
      return_dict["error"] = "%s %s failed."%(service,action)
      return_dict["error_details"] = "The system could not locate a service with name '%s' .Please redo the operation. If this problem persists, contact for support."%service
      return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

  else:
    return_dict["error"] = "Please use the menus and screens to access this page"
    return_dict["error_details"] = "You seem to have accessed this page by changing the url. This will not work as intended. Please go back to the old screen and redo the operation"
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
