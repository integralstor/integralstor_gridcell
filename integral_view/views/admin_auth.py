
import django
import django.template
from django.contrib import auth
from django.conf import settings

import json

import integral_view
from integral_view.forms import admin_forms
from integral_view.utils import audit, mail

def login(request):
  """ Used to login a user into the management utility"""

  return_dict = {}
  authSucceeded = False

  if request.method == 'POST':
    # Someone is submitting info so check it
    form = admin_forms.LoginForm(request.POST)
    if form.is_valid():
      # submitted form is valid so now try to authenticate
      # if not valid then fall out to end of function and return form to user
      # with existing data
      cd = form.cleaned_data
      username = cd['username']
      password = cd['password']
      # Try to authenticate
      user = django.contrib.auth.authenticate(username=username, password=password)
      if user is not None and user.is_active:
        # authentication succeeded! Login and send to home screen
        django.contrib.auth.login(request, user)
        authSucceeded = True
      else:
        return_dict['invalidUser'] = True
  else:
    # GET request so create a new form and send back to user
    form = admin_forms.LoginForm()

  return_dict['form'] = form

  if authSucceeded:
    return django.http.HttpResponseRedirect('/show/dashboard/')

  # For all other cases, return to login screen with return_dict 
  # appropriately populated
  return django.shortcuts.render_to_response('login_form.html', return_dict, context_instance = django.template.context.RequestContext(request))


def logout(request):
  """ Used to logout a user into the management utility"""
  django.contrib.auth.logout(request)
  return django.http.HttpResponseRedirect('/login/')

def change_admin_password(request):
  """ Used to change a user's password for the management utility"""

  return_dict = {}

  if request.user and request.user.is_authenticated():
    if request.method == 'POST':
      #user has submitted the password info
      form = admin_forms.ChangeAdminPasswordForm(request.POST)
      if form.is_valid():
        cd = form.cleaned_data
        oldPasswd = cd['oldPasswd']
        newPasswd1 = cd['newPasswd1']
        newPasswd2 = cd['newPasswd2']
        #Checking for old password is done in the form itself
        if request.user.check_password(oldPasswd):
          if newPasswd1 == newPasswd2:
            # all systems go so now change password
            request.user.set_password(newPasswd1);
            request.user.save()
            return_dict['success'] = True
            audit_str = "Changed admin password"
            audit.audit("modify_admin_password", audit_str, request.META["REMOTE_ADDR"])
          else:
	          return_dict['error'] = 'New passwords do not match'
      # else invalid form or error so existing form data to return_dict and 
      # fall through to redisplay the form
      if 'success' not in return_dict:
        return_dict['form'] = form
    else:
      form = admin_forms.ChangeAdminPasswordForm()
      return_dict['form'] = form

    return django.shortcuts.render_to_response('change_admin_password_form.html', return_dict, context_instance = django.template.context.RequestContext(request))
  else:
    #User not authenticated so return a login screen
    return django.http.HttpResponseRedirect('/login/')

def remove_email_settings(request):

  response = django.http.HttpResponse()
  try:
    mail.delete_email_settings()
    response.write("Deleted email settings")
  except Exception, e:
    response.write("Error deleteing email settings : %s"%str(e))
  return response
  ''' 
  co = None
  ecl = EmailConfig.objects.all()
  if ecl:
    co = EmailConfig.objects.filter(id=1)[0]
  if co:
    co.delete()
    response.write("Deleted object")
    response.write("Email configs in db = ")
    response.write(EmailConfig.objects.all())
    return response
  else:
    response.write("No Email config objects to remove")
  ''' 

  
def configure_email_settings(request):

  return_dict = {}
  url = "edit_email_settings.html"
  if request.method=="GET":
    d = mail.load_email_settings()
    if not d:
      form = admin_forms.ConfigureEmailForm()
    else:
      '''
    ecl = EmailConfig.objects.all()
    if not ecl:
      form = admin_forms.ConfigureEmailForm()
    else:
      co = EmailConfig.objects.filter(id=1)[0]
      d = {}
      d["email_server"] = co.server
      d["email_server_port"] = co.port
      d["username"] = co.username
      d["email_alerts"] = co.email_alerts
      d["tls"] = co.tls
      d["rcpt_list"] = co.rcpt_list
    '''

      if d["tls"]:
        d["tls"] = True
      else:
        d["tls"] = False
      if d["email_alerts"]:
        d["email_alerts"] = True
      else:
        d["email_alerts"] = False
      form = admin_forms.ConfigureEmailForm(initial = {'email_server':d["server"], 'email_server_port':d["port"], 'tls':d["tls"], 'username':d["username"], 'email_alerts':d["email_alerts"], 'rcpt_list':d["rcpt_list"]})
  else:
    form = admin_forms.ConfigureEmailForm(request.POST)
    if form.is_valid():
      cd = form.cleaned_data
      d = {}
      if "email_alerts" in cd:
        d["email_alerts"] = cd["email_alerts"]
      else:
        d["email_alerts"] = False
      d["server"] = cd["email_server"]
      d["port"] = cd["email_server_port"]
      d["username"] = cd["username"]
      d["pswd"] = cd["pswd"]
      d["rcpt_list"] = cd["rcpt_list"]
      if "tls" in cd:
        d["tls"] = cd["tls"]
      else:
        d["tls"] = False
      #print "Saving : "
      #print d
      try:
        mail.save_email_settings(d)
      except Exception, e:
        return django.http.HttpResponseRedirect("/show/email_settings?not_saved=1&err=%s"%str(e))

      '''
      ecl = EmailConfig.objects.all()
      if not ecl:
        ec = EmailConfig(server = cd["email_server"], port = cd["email_server_port"], username=cd["username"], pswd = cd["pswd"], email_alerts = cd["email_alerts"], tls = cd["tls"], rcpt_list = cd["rcpt_list"])
        ec.save()
      else:
        co = EmailConfig.objects.filter(id=1)[0]
        co.server = cd["email_server"]
        co.port = cd["email_server_port"]
        co.username = cd["username"]
        co.pswd = cd["pswd"]
        co.email_alerts = cd["email_alerts"]
        co.tls = cd["tls"]
        co.rcpt_list = cd["rcpt_list"]
        co.save()
      '''

      ret = mail.send_mail(cd["email_server"], cd["email_server_port"], cd["username"], cd["pswd"], cd["tls"], cd["rcpt_list"], "Test email from FractalView", "This is a test email sent by the Fractal View system in order to confirm that your email settings are working correctly.")
      if ret:
        return django.http.HttpResponseRedirect("/show/email_settings?saved=1&err=%s"%ret)
      else:
        return django.http.HttpResponseRedirect("/show/email_settings?saved=1")
      #url = "edit_email_settings.html"
  return_dict["form"] = form
  return django.shortcuts.render_to_response(url, return_dict, context_instance = django.template.context.RequestContext(request))

