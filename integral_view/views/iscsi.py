
from integral_view.forms import iscsi_forms

import integralstor_common
from integralstor_common import audit
import integralstor_gridcell
from integralstor_gridcell import volume_info, iscsi

import django.template, django

def iscsi_display_global_config():
  pass

def iscsi_display_initiators(request):

  return_dict = {}
  try:
    template = 'logged_in_error.html'
    initiators_list, err = iscsi.load_initiators_list()
    if err:
      raise Exception(err)

    if "action" in request.GET:
      if request.GET["action"] == "saved":
        conf = "Initiator information successfully updated"
      elif request.GET["action"] == "created":
        conf = "Initiator successfully created"
      elif request.GET["action"] == "deleted":
        conf = "Initiator successfully delete"
      return_dict["conf"] = conf
    return_dict["initiators_list"] = initiators_list
    template = "view_iscsi_initiators_list.html"
    return django.shortcuts.render_to_response(template, return_dict, context_instance = django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
  
def iscsi_view_initiator(request):

  return_dict = {}
  try:
    if request.method != "GET":
      raise Exception("Incorrect access method. Please use the menus")

    if "id" not in request.GET :
      raise Exception("Unknown initiator")

    id = request.GET["id"]

    if "action" in request.GET and request.GET["action"] == "saved":
      return_dict["conf_message"] = "Information updated successfully"

    initiator, err = iscsi.load_initiator_info(int(id))
    if err:
      raise Exception(err)

    if not initiator:
      raise Exception("Error retrieving initiator information for  %s" %id)

    return_dict["initiator"] = initiator
    template = 'view_iscsi_initiator.html'

    return django.shortcuts.render_to_response(template, return_dict, context_instance=django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


def iscsi_edit_initiator(request):

  return_dict = {}
  try:
    if "id" not in request.REQUEST:
    raise Exception("Unknown initiator specified")

    id = int(request.REQUEST["id"])

    if request.method == "GET":
      # Shd be an edit request
      initiator, err = iscsi.load_initiator_info(int(id))
      if err:
        raise Exception(err)
      if not initiator:
        raise Exception("Specified initiator not found")

      # Set initial form values
      initial = {}
      initial["id"] = initiator["id"]
      initial["initiators"] = initiator["initiators"]
      initial["auth_network"] = initiator["auth_network"]
      initial["comment"] = initiator["comment"]

      form = iscsi_forms.InitiatorForm(initial = initial)

      return_dict["form"] = form
      return django.shortcuts.render_to_response('edit_iscsi_initiator.html', return_dict, context_instance=django.template.context.RequestContext(request))

    else:

      # Shd be an save request
      form = iscsi_forms.InitiatorForm(request.POST)
      if form.is_valid():
        cd = form.cleaned_data
        ret, err = iscsi.save_initiator(id, cd)
        if err:
          raise Exception(err)
        if not ret:
          raise Exception('Could not save initiator information')

        audit_str = "Modified initiator %s"%id
        ret, err = audit.audit("modify_initiator", audit_str, request.META["REMOTE_ADDR"])
        if err:
          raise Exception(err)
        return django.http.HttpResponseRedirect('/iscsi_view_initiator?access_mode=by_id&id=%s&action=saved'%id)
      else:
        #Invalid form
        form.initial = form.data
        return_dict["form"] = form
        return django.shortcuts.render_to_response('edit_iscsi_initiator.html', return_dict, context_instance=django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


def iscsi_create_initiator(request):


  return_dict = {}
  try:
    if request.method == "GET":
      #Return the form
      form = iscsi_forms.InitiatorForm()
      return_dict["form"] = form
      return django.shortcuts.render_to_response("create_iscsi_initiator.html", return_dict, context_instance = django.template.context.RequestContext(request))
    else:
      #Form submission so create
      return_dict = {}
      form = iscsi_forms.InitiatorForm(request.POST)
      return_dict["form"] = form
      if form.is_valid():
        cd = form.cleaned_data
        ret, err = iscsi.create_iscsi_initiator(cd["initiators"], cd["auth_network"], cd["comment"])
        if err:
          raise Exception(err)
        if not ret:  
          raise Exception('Error creating initiator')
  
        audit_str = "Created an ISCSI initiator"
        ret, err = audit.audit("create_iscsi_initiator", audit_str, request.META["REMOTE_ADDR"])
        if err:
          raise Exception(err)
        return django.http.HttpResponseRedirect('/iscsi_display_initiators?action=created')
      else:
        return django.shortcuts.render_to_response("create_iscsi_initiator.html", return_dict, context_instance = django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


def iscsi_delete_initiator(request):

  return_dict = {}
  try:
    if 'id' not in request.REQUEST:
      raise Exception('No initiator ID specified. Please use the menus')
    id = request.REQUEST["id"]

    if request.method == "GET":
      #Return the conf page
      return_dict["id"] = id
      return django.shortcuts.render_to_response("delete_iscsi_initiator_conf.html", return_dict, context_instance = django.template.context.RequestContext(request))
    else:
      ret, err = iscsi.delete_initiator(int(id))
      if err:
        raise Exception(err)
      if not ret:
        raise Exception('Error deleting initiator')

      audit_str = "Deleted ISCSI initiator %s"%id
      ret, err = audit.audit("delete_iscsi_initiator", audit_str, request.META["REMOTE_ADDR"])
      if err:
        raise Exception(err)
      return django.http.HttpResponseRedirect('/iscsi_display_initiators?action=deleted')
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


def iscsi_display_auth_access_group_list(request):

  return_dict = {}
  try:
    auth_access_list = None
    auth_access_list, err = iscsi.load_auth_access_group_list()
    if err:
      raise Exception(err)

    d = {}
    if auth_access_list:
      for i in auth_access_list:
        l, err = iscsi.load_auth_access_users_info(i["id"])
        if err:
          raise Exception(err)
        d[i["id"]] =l

    if "action" in request.GET:
      if request.GET["action"] == "user_saved":
        conf = "Authorized access user information successfully updated"
      elif request.GET["action"] == "created":
        conf = "Authorized access group successfully created"
      elif request.GET["action"] == "user_created":
        conf = "Authorized access user successfully created"
      elif request.GET["action"] == "deleted":
        conf = "Authorized access group successfully deleted"
      elif request.GET["action"] == "user_deleted":
        conf = "Authorized access user successfully deleted"
      return_dict["conf"] = conf
    return_dict["auth_access_info"] = d
    template = "view_iscsi_auth_access_group_list.html"
    return django.shortcuts.render_to_response(template, return_dict, context_instance = django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


def iscsi_create_auth_access_group(request):

  return_dict = {}
  try:
    if request.method == "GET":
      #Return the form
      form = iscsi_forms.AuthorizedAccessUserForm()
      return_dict["form"] = form
      return django.shortcuts.render_to_response("create_iscsi_auth_access_group.html", return_dict, context_instance = django.template.context.RequestContext(request))
    else:
      #Form submission so create
      return_dict = {}
      form = iscsi_forms.AuthorizedAccessUserForm(request.POST)
      return_dict["form"] = form
      if form.is_valid():
        cd = form.cleaned_data
        auth_access_group_id, err = iscsi.create_auth_access_group()
        if err:
          raise Exception(err)
        if not auth_access_group_id:
          raise Exception('Error creating authorized access group')
        ret, err = iscsi.create_auth_access_user(auth_access_group_id, cd["user"], cd["secret"])
        if err:
          raise Exception(err)
        if not ret:
          raise Exception('Error creating authorized access user within the group')
        audit_str = "Created an ISCSI authorized access group"
        ret, err = audit.audit("create_iscsi_auth_access_group", audit_str, request.META["REMOTE_ADDR"])
        if err:
          raise Exception(err)
        return django.http.HttpResponseRedirect('/iscsi_display_auth_access_group_list?action=created')
      else:
        return django.shortcuts.render_to_response("create_iscsi_auth_access_group.html", return_dict, context_instance = django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

def iscsi_create_auth_access_user(request):


  return_dict = {}
  try:
    if request.method == "GET":
      #Return the form
      if 'auth_access_group_id' not in request.GET:
        raise Exception('No group ID provided. Please use the menus')
      auth_access_group_id = int(request.GET["auth_access_group_id"])
      init = {}
      init["auth_access_group_id"] = auth_access_group_id
      form = iscsi_forms.AuthorizedAccessUserForm(initial = init)
      return_dict["form"] = form
      return django.shortcuts.render_to_response("create_iscsi_auth_access_group.html", return_dict, context_instance = django.template.context.RequestContext(request))
    else:
      #Form submission so create
      return_dict = {}
      form = iscsi_forms.AuthorizedAccessUserForm(request.POST)
      return_dict["form"] = form
      if form.is_valid():
        cd = form.cleaned_data
        ret, err = iscsi.create_auth_access_user(cd["auth_access_group_id"], cd["user"], cd["secret"])
        if err:
          raise Exception(err)
        if not ret:
          raise Exception('Error creating authorized access user')

        audit_str = "Created an ISCSI authorized access user in group %s"%cd["auth_access_group_id"]
        ret, err = audit.audit("create_iscsi_auth_access_group", audit_str, request.META["REMOTE_ADDR"])
        if err:
          raise Exception(err)
        return django.http.HttpResponseRedirect('/iscsi_display_auth_access_group_list?action=user_created')
      else:
        return django.shortcuts.render_to_response("create_iscsi_auth_access_user.html", return_dict, context_instance = django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))



def iscsi_view_auth_access_group(request):

  return_dict = {}
  try:
    if request.method != "GET":
      raise Exception("Incorrect access method. Please use the menus")

    if "id" not in request.GET :
      raise Exception("Unknown authorized access group id")

    id = request.GET["id"]

    if "action" in request.GET and request.GET["action"] == "saved":
      return_dict["conf_message"] = "Information updated successfully"

    aa, err = iscsi.load_auth_access_group_info(int(id))
    if err:
      raise Exception(err)
    if not aa:
      raise Exception("Error retrieving authorized access group information for  %s" %id)
    return_dict["auth_access"] = aa
    template = 'view_iscsi_auth_access_group.html'

    return django.shortcuts.render_to_response(template, return_dict, context_instance=django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


def iscsi_delete_auth_access_group(request):

  return_dict = {}

  try:
    if auth_access_group_id not in request.REQUEST:
      raise Exception('Group ID not specified. Please use the menus')
    auth_access_group_id = request.REQUEST["auth_access_group_id"]
    if request.method == "GET":
      #Return the conf page
      return_dict["auth_access_group_id"] = auth_access_group_id
      return django.shortcuts.render_to_response("delete_iscsi_auth_access_group_conf.html", return_dict, context_instance = django.template.context.RequestContext(request))
    else:
      ret, err = iscsi.delete_auth_access_group(int(auth_access_group_id))
      if err:
        raise Exception(err)
      if not ret:
        raise Exception('Error deleting group')
      audit_str = "Deleted ISCSI authorized access group %s"%auth_access_group_id
      ret, err = audit.audit("delete_iscsi_auth_access_group", audit_str, request.META["REMOTE_ADDR"])
      if err:
        raise Exception(err)
      return django.http.HttpResponseRedirect('/iscsi_display_auth_access_group_list?action=deleted')
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

def iscsi_delete_auth_access_user(request):

  return_dict = {}
  try:
    if 'user_id' not in request.REQUEST:
      raise Exception('User ID not specified. Please use the menus')
    user_id = request.REQUEST["user_id"]
    if request.method == "GET":
      #Return the conf page
      d, err = iscsi.load_auth_access_user_info(int(user_id))
      if err:
        raise Exception(err)
      if not d:
        raise Exception("Could not find information about ISCSI authorized access user")
      return_dict["user_id"] = user_id
      return_dict["user"] = d["user"]
      return django.shortcuts.render_to_response("delete_iscsi_auth_access_user_conf.html", return_dict, context_instance = django.template.context.RequestContext(request))
    else:
      ret, err = iscsi.delete_auth_access_user(int(user_id))
      if err:
        raise Exception(err)
      if not ret:
        raise Exception('Error deleting user')

      audit_str = "Deleted ISCSI authorized access user %s"%user_id
      ret, err = audit.audit("delete_iscsi_auth_access_user", audit_str, request.META["REMOTE_ADDR"])
      if err:
        raise Exception(err)
      return django.http.HttpResponseRedirect('/iscsi_display_auth_access_group_list?action=user_deleted')
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

def iscsi_edit_auth_access_user(request):

  return_dict = {}
  try:
    if "user_id" not in request.REQUEST:
      raise Exception("Unknown authorized access user specified")
      return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))

    user_id = int(request.REQUEST["user_id"])
    return_dict["user_id"] = user_id

    auth_access = iscsi.load_auth_access_user_info(int(user_id))
    if err:
      raise Exception(err)
    if not auth_access:
      raise Exception("authorized access user information not found")

    if request.method == "GET":
      # Shd be an edit request

      # Set initial form values
      initial = {}
      initial["auth_access_group_id"] = auth_access["auth_access_group_id"]
      initial["user_id"] = auth_access["id"]
      initial["user"] = auth_access["user"]

      form = iscsi_forms.AuthorizedAccessUserForm(initial = initial)

      return_dict["form"] = form
      return django.shortcuts.render_to_response('edit_iscsi_auth_access_user.html', return_dict, context_instance=django.template.context.RequestContext(request))

    else:

      # Shd be an save request
      form = iscsi_forms.AuthorizedAccessUserForm(request.POST)
      return_dict["form"] = form
  
      if form.is_valid():
        cd = form.cleaned_data
        user = cd["user"]
        auth_access_group_id = cd["auth_access_group_id"]
        user_id = cd["user_id"]
        secret = cd["secret"]
        ret, err = iscsi.save_auth_access_user(auth_access_group_id, user_id, user, secret)
        if err:
          raise Exception(err)
        if not ret:
          raise Exception("Error saving authorized access user information")

        audit_str = "Modified authorized access user in auth group %s"%auth_access_group_id
        ret, err = audit.audit("modify_iscsi_auth_access_user", audit_str, request.META["REMOTE_ADDR"])
        if err:
          raise Exception(err)

        return django.http.HttpResponseRedirect('/iscsi_display_auth_access_group_list?action=user_saved')

      else:
        #Invalid form
        form.initial = form.data
        return django.shortcuts.render_to_response('edit_iscsi_auth_access_user.html', return_dict, context_instance=django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


def iscsi_view_target_global_config(request):
  return_dict = {}
  try:
    if request.method != "GET":
      raise Exception("Incorrect access method. Please use the menus")

    igt = None
    igt, err = iscsi.load_global_target_conf()
    if err:
      raise Exception(err)
    if not igt:
      raise Exception('Specified target global configuration not found')
    return_dict["igt"] = igt
    return django.shortcuts.render_to_response('view_iscsi_target_global_config.html', return_dict, context_instance=django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

    
def iscsi_edit_target_global_config(request):

  return_dict = {}
  try:
    aal, err = iscsi.load_auth_access_group_list()
    if err:
      raise Exception(err)
    if request.method == 'GET':
      #Display the form
      init, err = iscsi.load_global_target_conf()
      if err:
        raise Exception(err)
      if not init:
        init = {}
      if "base_name" not in init or not init["base_name"]:
        init["base_name"] = "iqn.2014-15.com.fractalio.istgt"
      if "discovery_auth_method" not in init or not init["discovery_auth_method"]:
        init["discovery_auth_method"] = "None"
      form = iscsi_forms.TargetGlobalConfigForm(initial=init, auth_access_group_list = aal)
      print init
      return_dict["form"] = form
      return django.shortcuts.render_to_response('edit_iscsi_target_global_config.html', return_dict, context_instance=django.template.context.RequestContext(request))
    else:
      # Save request
      form = iscsi_forms.TargetGlobalConfigForm(request.POST, auth_access_group_list = aal)
      return_dict["form"] = form

      if form.is_valid():
        cd = form.cleaned_data
        ret, err = iscsi.save_global_target_conf(cd)
        if err:
          raise Exception(err)
        if not ret:
          raise Exception("Error saving ISCSI global target configuration")

        audit_str = "Modified ISCSI global targets configuration%s"%id
        ret, err = audit.audit("modify_iscsi_global_target_conf", audit_str, request.META["REMOTE_ADDR"])
        if err:
          raise Exception(err)

        return django.http.HttpResponseRedirect('/iscsi_view_target_global_config?action=saved')

      else:
        #Invalid form
        form.initial = form.data
        return django.shortcuts.render_to_response('edit_iscsi_target_global_config.html', return_dict, context_instance=django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

def iscsi_display_targets(request):

  return_dict = {}
  try:
    targets_list, err = iscsi.load_targets_list()
    if err:
      raise Exception(err)

    if "action" in request.GET:
      if request.GET["action"] == "saved":
        conf = "Target information successfully updated"
      elif request.GET["action"] == "created":
        conf = "Target successfully created"
      elif request.GET["action"] == "deleted":
        conf = "Target successfully delete"
      return_dict["conf"] = conf
    return_dict["targets_list"] = targets_list
    template = "view_iscsi_targets_list.html"
    return django.shortcuts.render_to_response(template, return_dict, context_instance = django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

def iscsi_create_target(request):

  return_dict = {}
  try:
    vil, err = volume_info.get_volume_info_all()
    if err:
      raise Exception(err)
    vl, err = iscsi.load_iscsi_volumes_list(vil)
    if err:
      raise Exception(err)
    aal, err = iscsi.load_auth_access_group_list()
    if err:
      raise Exception(err)
    igl, err = iscsi.load_initiators_list()
    if err:
      raise Exception(err)

    if not igl  or not aal or not vl:
      if not igl:
        raise Exception("Please create an initiator before creating a target"
      if not vl:
        raise Exception("Please create an ISCSI access enabled volume before creating a target"
      if not aal:
        raise Exception("Please create an authorized access before creating a target"

    if request.method == "GET":
      #Return the form
      return_dict = {}
      form = iscsi_forms.TargetForm(auth_access_group_list = aal, initiator_group_list = igl, volumes_list = vl)
      return_dict["form"] = form
      return django.shortcuts.render_to_response("create_iscsi_target.html", return_dict, context_instance = django.template.context.RequestContext(request))
    else:
      #Form submission so create
      return_dict = {}
      form = iscsi_forms.TargetForm(request.POST, auth_access_group_list = aal, initiator_group_list = igl, volumes_list = vl)
      return_dict["form"] = form
      if form.is_valid():
        cd = form.cleaned_data
        ret, err = iscsi.create_iscsi_target(cd["vol_name"],  cd["target_alias"], cd["lun_size"], cd["auth_method"], cd["queue_depth"], cd["auth_group_id"], cd["init_group_id"])
        if err:
          raise Exception(err)
        if not ret:
          raise Exception('Error creating ISCSI target')

        audit_str = "Created an ISCSI target"
        ret, err = audit.audit("create_iscsi_target", audit_str, request.META["REMOTE_ADDR"])
        if err:
          raise Exception(err)
        return django.http.HttpResponseRedirect('/iscsi_display_targets?action=created')
      else:
        return django.shortcuts.render_to_response("create_iscsi_target.html", return_dict, context_instance = django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

def iscsi_edit_target(request):

  return_dict = {}
  try:
    vil, err = volume_info.get_volume_info_all()
    if err:
      raise Exception(err)
    vl, err = iscsi.load_iscsi_volumes_list(vil)
    if err:
      raise Exception(err)
    aal, err = iscsi.load_auth_access_group_list()
    if err:
      raise Exception(err)
    igl, err = iscsi.load_initiators_list()
    if err:
      raise Exception(err)

    if "id" not in request.REQUEST:
      raise Exception("Unknown target specified")

    id = int(request.REQUEST["id"])

    if request.method == "GET":
      # Shd be an edit request
      target, err = iscsi.load_target_info(int(id))
      if err:
        raise Exception(err)
      if not target:
        raise Exception('Specified target not found')

      # Set initial form values
      initial = {}
      initial["id"] = target["id"]
      initial["vol_name"] = target["vol_name"]
      initial["target_alias"] = target["target_alias"]
      initial["lun_size"] = target["lun_size"]
      initial["auth_method"] = target["auth_method"]
      initial["queue_depth"] = target["queue_depth"]
      initial["auth_group_id"] = int(target["auth_group_id"])
      initial["init_group_id"] = int(target["init_group_id"])
  

      form = iscsi_forms.TargetForm(auth_access_group_list = aal, initiator_group_list = igl, volumes_list = vl, initial = initial)

      return_dict["form"] = form
      return django.shortcuts.render_to_response('edit_iscsi_target.html', return_dict, context_instance=django.template.context.RequestContext(request))

    else:
  
      # Shd be an save request
      form = iscsi_forms.TargetForm(request.POST, auth_access_group_list = aal, initiator_group_list = igl, volumes_list = vl)
      return_dict["form"] = form
      if form.is_valid():
        cd = form.cleaned_data
        ret, err = iscsi.save_target(id, cd)
        if err:
          raise Exception(err)
        if not ret:
          raise Exception('Error saving the specified target')
        ret, err = iscsi.generate_istgt_conf()
        if err:
          raise Exception(err)
        if not ret:
          raise Exception('Error generating the ISCSI configuration file')
        audit_str = "Modified target %s"%id
        ret, err = audit.audit("modify_target", audit_str, request.META["REMOTE_ADDR"])
        if err:
          raise Exception(err)

        return django.http.HttpResponseRedirect('/iscsi_view_target?access_mode=by_id&id=%s&action=saved'%id)

      else:
        #Invalid form
        return django.shortcuts.render_to_response('edit_iscsi_target.html', return_dict, context_instance=django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

def iscsi_view_target(request):

  return_dict = {}
  try:
    if request.method != "GET":
      raise Exception("Incorrect access method. Please use the menus")

    if "id" not in request.GET :
      raise Exception("Unknown target")

    id = request.GET["id"]

    if "action" in request.GET and request.GET["action"] == "saved":
      return_dict["conf_message"] = "Information updated successfully"

    target, err = iscsi.load_target_info(int(id))
    if err:
      raise Exception(err)
    if not target:
      raise Exception('Error retrieving target information for %s'%id)
    return_dict["target"] = target
    template = 'view_iscsi_target.html'

    return django.shortcuts.render_to_response(template, return_dict, context_instance=django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


def iscsi_delete_target(request):

  return_dict = {}
  try:
    if 'id' not in request.REQUEST:
      raise Exception('Target ID not specified. Please use the menus')
    id = request.REQUEST["id"]
    if request.method == "GET":
      #Return the conf page
      return_dict["id"] = id
      return django.shortcuts.render_to_response("delete_iscsi_target_conf.html", return_dict, context_instance = django.template.context.RequestContext(request))
    else:
      ret, err = iscsi.delete_target(int(id))
      if err:
        raise Exception(err)
      if not ret:
        raise Exception("Error deleting ISCSI target")
      audit_str = "Deleted ISCSI target %s"%id
      ret, err = audit.audit("delete_iscsi_target", audit_str, request.META["REMOTE_ADDR"])
      if err:
        raise Exception(err)
      return django.http.HttpResponseRedirect('/iscsi_display_targets?action=deleted')
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

