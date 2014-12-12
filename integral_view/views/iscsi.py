
from integral_view.iscsi import iscsi
from integral_view.forms import iscsi_forms
from integral_view.utils import audit, volume_info
import django.template, django

def iscsi_display_global_config():
  pass

def iscsi_display_initiators(request):

  return_dict = {}
  template = 'logged_in_error.html'
  try :
    initiators_list = iscsi.load_initiators_list()
  except Exception, e:
    return_dict["error"] = "Error loading initiators - %s" %e

  if not "error" in return_dict:
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
  
def iscsi_view_initiator(request):

  return_dict = {}
  template = 'logged_in_error.html'

  if request.method != "GET":
    return_dict["error"] = "Incorrect access method. Please use the menus"

  #if "id" not in request.GET or "access_mode" not in request.GET:
  if "id" not in request.GET :
    return_dict["error"] = "Unknown initiator"

  if not "error" in return_dict:

    #access_mode = request.GET["access_mode"]
    id = request.GET["id"]

    if "action" in request.GET and request.GET["action"] == "saved":
      return_dict["conf_message"] = "Information updated successfully"

    try:
      initiator = iscsi.load_initiator_info(int(id))
    except Exception, e:
      return_dict["error"] = "Error retrieving initiator information - %s" %e
    else:
      if not initiator:
        return_dict["error"] = "Error retrieving initiator information for  %s" %id
      else:
        return_dict["initiator"] = initiator
        template = 'view_iscsi_initiator.html'

  return django.shortcuts.render_to_response(template, return_dict, context_instance=django.template.context.RequestContext(request))

def iscsi_edit_initiator(request):

  return_dict = {}
  if "id" not in request.REQUEST:
    return_dict["error"] = "Unknown initiator specified"
    return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))
  id = int(request.REQUEST["id"])

  if request.method == "GET":
    # Shd be an edit request
    try :
      initiator = iscsi.load_initiator_info(int(id))
    except Exception, e:
      return_dict["error"] = "Error loading initiator information - %s" %e
      return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))

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
      try :
        iscsi.save_initiator(id, cd)
      except Exception, e:
        return_dict["error"] = "Error saving initiator information - %s" %e
        return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))

      audit_str = "Modified initiator %s"%id
      audit.audit("modify_initiator", audit_str, request.META["REMOTE_ADDR"])

      return django.http.HttpResponseRedirect('/iscsi_view_initiator?access_mode=by_id&id=%s&action=saved'%id)

    else:
      #Invalid form
      form.initial = form.data
      return_dict["form"] = form
      return django.shortcuts.render_to_response('edit_iscsi_initiator.html', return_dict, context_instance=django.template.context.RequestContext(request))

def iscsi_create_initiator(request):

  #vil = volume_info.get_volume_info_all()

  if request.method == "GET":
    #Return the form
    return_dict = {}
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
      try :
        iscsi.create_iscsi_initiator(cd["initiators"], cd["auth_network"], cd["comment"])
      except Exception, e:
        return_dict["error"] = "Error creating the initiator - %s" %e
        return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))

      audit_str = "Created an ISCSI initiator"
      audit.audit("create_iscsi_initiator", audit_str, request.META["REMOTE_ADDR"])
      return django.http.HttpResponseRedirect('/iscsi_display_initiators?action=created')
    else:
      return django.shortcuts.render_to_response("create_iscsi_initiator.html", return_dict, context_instance = django.template.context.RequestContext(request))

def iscsi_delete_initiator(request):

  return_dict = {}
  if request.method == "GET":
    #Return the conf page
    id = request.GET["id"]
    return_dict["id"] = id
    return django.shortcuts.render_to_response("delete_iscsi_initiator_conf.html", return_dict, context_instance = django.template.context.RequestContext(request))
  else:
    id = request.POST["id"]
    try :
      iscsi.delete_initiator(int(id))
    except Exception, e:
      return_dict["error"] = "Error deleting ISCSI initiator - %s" %e
      return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))

    audit_str = "Deleted ISCSI initiator %s"%id
    audit.audit("delete_iscsi_initiator", audit_str, request.META["REMOTE_ADDR"])
    return django.http.HttpResponseRedirect('/iscsi_display_initiators?action=deleted')


def iscsi_display_auth_access_group_list(request):

  return_dict = {}
  template = 'logged_in_error.html'
  auth_access_list = None
  try :
    auth_access_list = iscsi.load_auth_access_group_list()
  except Exception, e:
    return_dict["error"] = "Error loading authorized accesses group - %s" %e

  d = {}
  if auth_access_list:
    for i in auth_access_list:
      l = iscsi.load_auth_access_users_info(i["id"])
      d[i["id"]] =l

  if not "error" in return_dict:
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

def iscsi_create_auth_access_group(request):

  #vil = volume_info.get_volume_info_all()

  auth_access_group_id = 0
  return_dict = {}


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
      try :
        auth_access_group_id = iscsi.create_auth_access_group()
        iscsi.create_auth_access_user(auth_access_group_id, cd["user"], cd["secret"])
      except Exception, e:
        return_dict["error"] = "Error creating the authorized access user within the group - %s" %e
        return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))

      audit_str = "Created an ISCSI authorized access group"
      audit.audit("create_iscsi_auth_access_group", audit_str, request.META["REMOTE_ADDR"])
      return django.http.HttpResponseRedirect('/iscsi_display_auth_access_group_list?action=created')
    else:
      return django.shortcuts.render_to_response("create_iscsi_auth_access_group.html", return_dict, context_instance = django.template.context.RequestContext(request))

def iscsi_create_auth_access_user(request):

  #vil = volume_info.get_volume_info_all()

  auth_access_group_id = 0
  return_dict = {}


  if request.method == "GET":
    #Return the form
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
      try :
        iscsi.create_auth_access_user(cd["auth_access_group_id"], cd["user"], cd["secret"])
      except Exception, e:
        return_dict["error"] = "Error creating the authorized access user within the group - %s" %e
        return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))

      audit_str = "Created an ISCSI authorized access user in group %s"%cd["auth_access_group_id"]
      audit.audit("create_iscsi_auth_access_group", audit_str, request.META["REMOTE_ADDR"])
      return django.http.HttpResponseRedirect('/iscsi_display_auth_access_group_list?action=user_created')
    else:
      return django.shortcuts.render_to_response("create_iscsi_auth_access_user.html", return_dict, context_instance = django.template.context.RequestContext(request))

def iscsi_view_auth_access_group(request):

  return_dict = {}
  template = 'logged_in_error.html'

  if request.method != "GET":
    return_dict["error"] = "Incorrect access method. Please use the menus"

  #if "id" not in request.GET or "access_mode" not in request.GET:
  if "id" not in request.GET :
    return_dict["error"] = "Unknown authorized access group id"

  if not "error" in return_dict:

    #access_mode = request.GET["access_mode"]
    id = request.GET["id"]

    if "action" in request.GET and request.GET["action"] == "saved":
      return_dict["conf_message"] = "Information updated successfully"

    try:
      aa = iscsi.load_auth_access_group_info(int(id))
    except Exception, e:
      return_dict["error"] = "Error retrieving authorized access group information - %s" %e
    else:
      if not aa:
        return_dict["error"] = "Error retrieving authorized access group information for  %s" %id
      else:
        return_dict["auth_access"] = aa
        template = 'view_iscsi_auth_access_group.html'

  return django.shortcuts.render_to_response(template, return_dict, context_instance=django.template.context.RequestContext(request))

def iscsi_delete_auth_access_group(request):

  return_dict = {}
  if request.method == "GET":
    #Return the conf page
    auth_access_group_id = request.GET["auth_access_group_id"]
    return_dict["auth_access_group_id"] = auth_access_group_id
    return django.shortcuts.render_to_response("delete_iscsi_auth_access_group_conf.html", return_dict, context_instance = django.template.context.RequestContext(request))
  else:
    auth_access_group_id = request.POST["auth_access_group_id"]
    try :
      iscsi.delete_auth_access_group(int(auth_access_group_id))
    except Exception, e:
      return_dict["error"] = "Error deleting ISCSI authorized access group - %s" %e
      return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))

    audit_str = "Deleted ISCSI authorized access group %s"%auth_access_group_id
    audit.audit("delete_iscsi_auth_access_group", audit_str, request.META["REMOTE_ADDR"])
    return django.http.HttpResponseRedirect('/iscsi_display_auth_access_group_list?action=deleted')

def iscsi_delete_auth_access_user(request):

  return_dict = {}
  if request.method == "GET":
    #Return the conf page
    user_id = request.GET["user_id"]
    d = iscsi.load_auth_access_user_info(int(user_id))
    return_dict["user_id"] = user_id
    return_dict["user"] = d["user"]
    if not d:
      return_dict["error"] = "Could not find information about ISCSI authorized access user - %s" %str(e)
      return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))
    return django.shortcuts.render_to_response("delete_iscsi_auth_access_user_conf.html", return_dict, context_instance = django.template.context.RequestContext(request))
  else:
    user_id = request.POST["user_id"]
    try :
      iscsi.delete_auth_access_user(int(user_id))
    except Exception, e:
      return_dict["error"] = "Error deleting ISCSI authorized access user - %s" %e
      return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))

    audit_str = "Deleted ISCSI authorized access user %s"%user_id
    audit.audit("delete_iscsi_auth_access_user", audit_str, request.META["REMOTE_ADDR"])
    return django.http.HttpResponseRedirect('/iscsi_display_auth_access_group_list?action=user_deleted')

def iscsi_edit_auth_access_user(request):

  return_dict = {}
  #vil = volume_info.get_volume_info_all()
  #user_list = samba_settings.get_user_list()
  #group_list = samba_settings.get_group_list()

  if "user_id" not in request.REQUEST:
    return_dict["error"] = "Unknown authorized access user specified"
    return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))

  user_id = int(request.REQUEST["user_id"])
  return_dict["user_id"] = user_id

  try :
    auth_access = iscsi.load_auth_access_user_info(int(user_id))
  except Exception, e:
    return_dict["error"] = "Error loading authorized access user information - %s" %e
    return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))

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
      try :
        user = cd["user"]
        auth_access_group_id = cd["auth_access_group_id"]
        user_id = cd["user_id"]
        secret = cd["secret"]
        iscsi.save_auth_access_user(auth_access_group_id, user_id, user, secret)
      except Exception, e:
        return_dict["error"] = "Error saving authorized access user information - %s" %e
        return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))

      audit_str = "Modified authorized access user in auth group %s"%auth_access_group_id
      audit.audit("modify_iscsi_auth_access_user", audit_str, request.META["REMOTE_ADDR"])

      return django.http.HttpResponseRedirect('/iscsi_display_auth_access_group_list?action=user_saved')

    else:
      #Invalid form
      form.initial = form.data
      return django.shortcuts.render_to_response('edit_iscsi_auth_access_user.html', return_dict, context_instance=django.template.context.RequestContext(request))

def iscsi_view_target_global_config(request):
  return_dict = {}
  template = 'logged_in_error.html'

  if request.method != "GET":
    return_dict["error"] = "Incorrect access method. Please use the menus"

  igt = None

  try:
    igt = iscsi.load_global_target_conf()
  except Exception, e:
    return_dict["error"] = "Error retrieving authorized access information - %s" %e
    return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))

  if igt:
    return_dict["igt"] = igt

  return django.shortcuts.render_to_response('view_iscsi_target_global_config.html', return_dict, context_instance=django.template.context.RequestContext(request))
    
def iscsi_edit_target_global_config(request):

  return_dict = {}
  aal = iscsi.load_auth_access_group_list()
  if request.method == 'GET':
    #Display the form
    init = iscsi.load_global_target_conf()
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
      try :
        iscsi.save_global_target_conf(cd)
      except Exception, e:
        return_dict["error"] = "Error saving ISCSI global target configuration- %s" %e
        return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))

      audit_str = "Modified ISCSI global targets configuration%s"%id
      audit.audit("modify_iscsi_global_target_conf", audit_str, request.META["REMOTE_ADDR"])

      return django.http.HttpResponseRedirect('/iscsi_view_target_global_config?action=saved')

    else:
      #Invalid form
      form.initial = form.data
      return django.shortcuts.render_to_response('edit_iscsi_target_global_config.html', return_dict, context_instance=django.template.context.RequestContext(request))

def iscsi_display_targets(request):

  return_dict = {}
  template = 'logged_in_error.html'
  try :
    targets_list = iscsi.load_targets_list()
  except Exception, e:
    return_dict["error"] = "Error loading targets - %s" %e

  if not "error" in return_dict:
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

def iscsi_create_target(request):

  vil = volume_info.get_volume_info_all()

  vl = iscsi.load_iscsi_volumes_list(vil)
  aal = iscsi.load_auth_access_group_list()
  igl = iscsi.load_initiators_list()
  return_dict = {}

  if not igl  or not aal or not vl:
    if not igl:
      return_dict["error"] = "Please create an initiator before creating a target"
    if not vl:
      return_dict["error"] = "Please create an ISCSI access enabled volume before creating a target"
    if not aal:
      return_dict["error"] = "Please create an authorized access before creating a target"
    return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))

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
      try :
        iscsi.create_iscsi_target(cd["vol_name"],  cd["target_alias"], cd["lun_size"], cd["auth_method"], cd["queue_depth"], cd["auth_group_id"], cd["init_group_id"])
      except Exception, e:
        return_dict["error"] = "Error creating the target - %s" %e
        return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))

      audit_str = "Created an ISCSI target"
      audit.audit("create_iscsi_target", audit_str, request.META["REMOTE_ADDR"])
      return django.http.HttpResponseRedirect('/iscsi_display_targets?action=created')
    else:
      return django.shortcuts.render_to_response("create_iscsi_target.html", return_dict, context_instance = django.template.context.RequestContext(request))

def iscsi_edit_target(request):

  return_dict = {}
  vil = volume_info.get_volume_info_all()
  vl = iscsi.load_iscsi_volumes_list(vil)
  aal = iscsi.load_auth_access_group_list()
  igl = iscsi.load_initiators_list()

  if "id" not in request.REQUEST:
    return_dict["error"] = "Unknown target specified"
    return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))
  id = int(request.REQUEST["id"])

  if request.method == "GET":
    # Shd be an edit request
    try :
      target = iscsi.load_target_info(int(id))
    except Exception, e:
      return_dict["error"] = "Error loading target information - %s" %e
      return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))

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
      try :
        iscsi.save_target(id, cd)
      except Exception, e:
        return_dict["error"] = "Error saving target information - %s" %e
        return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))
      try :
        iscsi.generate_istgt_conf()
      except Exception, e:
        return_dict["error"] = "Error generating ISCSI config file- %s" %e
        return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))

      audit_str = "Modified target %s"%id
      audit.audit("modify_target", audit_str, request.META["REMOTE_ADDR"])

      return django.http.HttpResponseRedirect('/iscsi_view_target?access_mode=by_id&id=%s&action=saved'%id)

    else:
      #Invalid form
      return django.shortcuts.render_to_response('edit_iscsi_target.html', return_dict, context_instance=django.template.context.RequestContext(request))

def iscsi_view_target(request):

  return_dict = {}
  template = 'logged_in_error.html'

  if request.method != "GET":
    return_dict["error"] = "Incorrect access method. Please use the menus"

  #if "id" not in request.GET or "access_mode" not in request.GET:
  if "id" not in request.GET :
    return_dict["error"] = "Unknown target"

  if not "error" in return_dict:

    id = request.GET["id"]

    if "action" in request.GET and request.GET["action"] == "saved":
      return_dict["conf_message"] = "Information updated successfully"

    try:
      target = iscsi.load_target_info(int(id))
    except Exception, e:
      return_dict["error"] = "Error retrieving target information - %s" %e
    else:
      if not target:
        return_dict["error"] = "Error retrieving target information for  %s" %id
      else:
        return_dict["target"] = target
        template = 'view_iscsi_target.html'

  return django.shortcuts.render_to_response(template, return_dict, context_instance=django.template.context.RequestContext(request))

def iscsi_delete_target(request):

  return_dict = {}
  if request.method == "GET":
    #Return the conf page
    id = request.GET["id"]
    return_dict["id"] = id
    return django.shortcuts.render_to_response("delete_iscsi_target_conf.html", return_dict, context_instance = django.template.context.RequestContext(request))
  else:
    id = request.POST["id"]
    try :
      iscsi.delete_target(int(id))
    except Exception, e:
      return_dict["error"] = "Error deleting ISCSI target - %s" %e
      return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))

    audit_str = "Deleted ISCSI target %s"%id
    audit.audit("delete_iscsi_target", audit_str, request.META["REMOTE_ADDR"])
    return django.http.HttpResponseRedirect('/iscsi_display_targets?action=deleted')

