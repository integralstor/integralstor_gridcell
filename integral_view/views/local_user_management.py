import django, django.template

from integral_view.forms import local_user_forms
from integralstor_gridcell import local_users
from integralstor_common import audit

def view_local_users(request):

  return_dict = {}
  try:
    return_dict['base_template'] = "users_base.html"
    return_dict["page_title"] = 'View local users'
    return_dict['tab'] = 'local_user_tab'
    return_dict["error"] = 'Error viewing local users'

    user_list, err = local_users.get_local_users()
    if err:
      raise Exception(err)
    return_dict["user_list"] = user_list
  
    if "ack" in request.GET:
      if request.GET["ack"] == "saved":
        return_dict['ack_message'] = "Local user password successfully updated"
      elif request.GET["ack"] == "created":
        return_dict['ack_message'] = "Local user successfully created"
      elif request.GET["ack"] == "deleted":
        return_dict['ack_message'] = "Local user successfully deleted"
      elif request.GET["ack"] == "changed_password":
        return_dict['ack_message'] = "Successfully update password"

    return django.shortcuts.render_to_response('view_local_users.html', return_dict, context_instance=django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

def create_local_user(request):
  return_dict = {}
  try:
    return_dict['base_template'] = "users_base.html"
    return_dict["page_title"] = 'Create a local user'
    return_dict['tab'] = 'create_local_user_tab'
    return_dict["error"] = 'Error creating local user'

    if request.method == "GET":
      #Return the form
      form = local_user_forms.LocalUserForm()
      return_dict["form"] = form
      return django.shortcuts.render_to_response("create_local_user.html", return_dict, context_instance = django.template.context.RequestContext(request))
    else:
      #Form submission so create
      return_dict = {}
      form = local_user_forms.LocalUserForm(request.POST)
      if form.is_valid():
        cd = form.cleaned_data
        ret, err = local_users.create_local_user(cd["userid"], cd["name"], cd["password"])
        if err:
          raise Exception(err)
        if not ret:
          raise Exception('Error creating local user')
        audit_str = "Created a local user %s"%cd["userid"]
        r, err = audit.audit("create_local_user", audit_str, request.META)
        if err:
          raise Exception(err)
        url = '/view_local_users?ack=created'
        return django.http.HttpResponseRedirect(url)
      else:
        return_dict["form"] = form
        return django.shortcuts.render_to_response("create_local_user.html", return_dict, context_instance = django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

def delete_local_user(request):

  return_dict = {}
  try:
    return_dict['base_template'] = "users_base.html"
    return_dict["page_title"] = 'Delete a local user'
    return_dict['tab'] = 'local_user_tab'
    return_dict["error"] = 'Error deleteing a local user'
    if "userid" not in request.REQUEST:
      raise Exception("Invalid request. No user name specified.")
    
    if request.method == "GET":
      #Return the form
      return_dict["userid"] = request.GET["userid"]
      return django.shortcuts.render_to_response("delete_local_user_conf.html", return_dict, context_instance = django.template.context.RequestContext(request))
    else:
      #Form submission so create
      return_dict = {}
      ret, err = local_users.delete_local_user(request.POST["userid"])
      if err:
        raise Exception(err)
      if not ret:
        raise Exception('Error deleting local user')
      audit_str = "Deleted a local user %s"%request.POST["userid"]
      ret, err = audit.audit("delete_local_user", audit_str, request.META)
      if err:
        raise Exception(err)
      url = '/view_local_users?ack=deleted'
      return django.http.HttpResponseRedirect(url)
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


def change_local_user_password(request):

  return_dict = {}
  try:
    return_dict['base_template'] = "users_base.html"
    return_dict["page_title"] = 'Change local user password'
    return_dict['tab'] = 'local_user_tab'
    return_dict["error"] = 'Error changing local user password'
    if request.method == "GET":
      #Return the form
      if "userid" not in request.GET:
        raise Exception("Invalid request. No user name specified.")
      d = {}
      d["userid"] = request.GET["userid"]
      form = local_user_forms.PasswordChangeForm(initial=d)
      return_dict["form"] = form
      return django.shortcuts.render_to_response("change_local_user_password.html", return_dict, context_instance = django.template.context.RequestContext(request))
    else:
      #Form submission so create
      return_dict = {}
      form = local_user_forms.PasswordChangeForm(request.POST)
      if form.is_valid():
        cd = form.cleaned_data
        ret, err = local_users.change_password(cd["userid"], cd["password"])
        if err:
          raise Exception(err)
        if not ret:
          raise Exception('Error changing local user password')
  
        audit_str = "Changed password for local user %s"%cd["userid"]
        ret, err = audit.audit("change_local_user_password", audit_str, request.META)
        if err:
          raise Exception(err)
        return django.http.HttpResponseRedirect('/view_local_users?ack=changed_password')
      else:
        return_dict["form"] = form
        return django.shortcuts.render_to_response("change_local_user_password.html", return_dict, context_instance = django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

