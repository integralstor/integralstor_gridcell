
import django
import django.template
from django.contrib import auth
from django.contrib.sessions.models import Session

from integral_view.forms import admin_forms
#from integral_view.utils import iv_logging

import integralstor_common
from integralstor_common import audit, mail


def login(request):
    """ Used to login a user into the management utility"""

    return_dict = {}
    try:
        return_dict['base_template'] = "base.html"
        return_dict["page_title"] = 'Login'
        return_dict['tab'] = 'create_volume_tab'
        return_dict["error"] = 'Error logging in.'
        authSucceeded = False

        if request.method == 'POST':
            #iv_logging.info("Login request posted")
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
                user = django.contrib.auth.authenticate(
                    username=username, password=password)
                if user is not None and user.is_active:
                    production, err = integralstor_common.common.is_production()
                    if err:
                        raise Exception(err)
                    if production:
                        # Clear the session if the user has been logged in
                        # anywhere else.
                        sessions = Session.objects.all()
                        for s in sessions:
                            if s.get_decoded() and (s.get_decoded()['_auth_user_id'] == user.id):
                                # s.delete()
                                pass
                    # authentication succeeded! Login and send to home screen
                    django.contrib.auth.login(request, user)
                    #iv_logging.info("Login request from user '%s' succeeded"%username)
                    authSucceeded = True
                else:
                    #iv_logging.info("Login request from user '%s' failed"%username)
                    return_dict['invalidUser'] = True
            else:
                # Invalid form
                #iv_logging.debug("Invalid login information posted")
                pass
        else:
            # GET request so create a new form and send back to user
            form = admin_forms.LoginForm()
            # Clear the session if the user has been logged in anywhere else.
            sessions = Session.objects.all()
            for s in sessions:
                if s.get_decoded() is not None and s.get_decoded().get('_auth_user_id') is not None:
                    return_dict['session_active'] = True

        return_dict['form'] = form

        if authSucceeded:
            return django.http.HttpResponseRedirect('/dashboard')

        # For all other cases, return to login screen with return_dict
        # appropriately populated
        return django.shortcuts.render_to_response('login_form.html', return_dict, context_instance=django.template.context.RequestContext(request))
    except Exception, e:
        s = str(e)
        return_dict["error"] = "An error occurred when processing your request : %s" % s
        return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))


def logout(request):
    """ Used to logout a user into the management utility"""
    return_dict = {}
    try:
        #iv_logging.info("User '%s' logged out"%request.user)
        # Clear the session if the user has been logged in anywhere else.
        sessions = Session.objects.all()
        for s in sessions:
            if (s.get_decoded() and int(s.get_decoded()['_auth_user_id']) == request.user.id) or not s.get_decoded():
                s.delete()
        django.contrib.auth.logout(request)
        return django.http.HttpResponseRedirect('/login/')
    except Exception, e:
        return_dict['base_template'] = "dashboard_base.html"
        return_dict["page_title"] = 'Logout'
        return_dict['tab'] = 'disks_tab'
        return_dict["error"] = 'Error logging out'
        return_dict["error_details"] = str(e)
        return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))


def change_admin_password(request):
    """ Used to change a user's password for the management utility"""

    try:
        return_dict = {}

        if request.user and request.user.is_authenticated():
            if "ack" in request.GET:
                if request.GET["ack"] == "modified":
                    return_dict['ack_message'] = "Password successfully modified."
                elif request.GET["ack"] == "bad_password":
                    return_dict['ack_message'] = "Invalid current password. Please try again."
                elif request.GET["ack"] == "passwd_mismatch":
                    return_dict['ack_message'] = "The new passwords do not match. Please try again."
            if request.method == 'GET':
                form = admin_forms.ChangeAdminPasswordForm()
                return_dict['form'] = form
                return django.shortcuts.render_to_response('change_admin_password_form.html', return_dict, context_instance=django.template.context.RequestContext(request))
            else:
                #iv_logging.debug("Admin password change posted")
                # user has submitted the password info
                form = admin_forms.ChangeAdminPasswordForm(request.POST)
                if form.is_valid():
                    print 'valid'
                    cd = form.cleaned_data
                    oldPasswd = cd['oldPasswd']
                    newPasswd1 = cd['newPasswd1']
                    # Checking for old password is done in the form itself
                    if request.user.check_password(oldPasswd):
                        if cd['newPasswd1'] != cd['newPasswd2']:
                            return django.http.HttpResponseRedirect('/change_admin_password?ack=passwd_mismatch')
                        # all systems go so now change password
                        request.user.set_password(newPasswd1)
                        request.user.save()
                        #iv_logging.info("Admin password change request successful.")
                        audit_str = "Changed admin password"
                        audit.audit("modify_admin_password",
                                    audit_str, request.META["REMOTE_ADDR"])
                        return django.http.HttpResponseRedirect('/change_admin_password?ack=modified')
                    else:
                        # Invalid old password
                        return django.http.HttpResponseRedirect('/change_admin_password?ack=bad_password')
                else:
                    # invalid form
                    return_dict['form'] = form
                    return django.shortcuts.render_to_response('change_admin_password_form.html', return_dict, context_instance=django.template.context.RequestContext(request))
        else:
            # User not authenticated so return a login screen
            return django.http.HttpResponseRedirect('/login/')
    except Exception, e:
        return_dict['base_template'] = "admin_base.html"
        return_dict["page_title"] = 'Change admininistrator password'
        return_dict['tab'] = 'admin_change_pass_tab'
        return_dict["error"] = 'Error changing administrator password'
        return_dict["error_details"] = str(e)
        return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))


def view_email_settings(request):
    return_dict = {}
    try:
        return_dict['base_template'] = "system_base.html"
        return_dict["page_title"] = 'View Email settings'
        return_dict['tab'] = 'email_settings_tab'
        return_dict["error"] = 'Error loading Email settings'
        d, err = mail.load_email_settings()
        if err:
            raise Exception(err)
        if not d:
            return_dict["email_not_configured"] = True
        else:
            if d["tls"]:
                d["tls"] = True
            else:
                d["tls"] = False
            if d["email_alerts"]:
                d["email_alerts"] = True
            else:
                d["email_alerts"] = False
            return_dict["email_settings"] = d
        ack_msg = ''
        if "ack" in request.GET:
            if request.GET["ack"] == "saved":
                ack_message = "Email settings have been saved. "
        if "err" in request.REQUEST:
            ack_message += 'The following errors were reported : %s' % request.REQUEST["err"]
        return django.shortcuts.render_to_response('view_email_settings.html', return_dict, context_instance=django.template.context.RequestContext(request))
    except Exception, e:
        return_dict["error_details"] = str(e)
        return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))


def configure_email_settings(request):

    return_dict = {}
    try:
        return_dict['base_template'] = "system_base.html"
        return_dict["page_title"] = 'Configure email settings'
        return_dict['tab'] = 'email_settings_tab'
        return_dict["error"] = 'Error configuring email settings'
        if request.method == "GET":
            d, err = mail.load_email_settings()
            if err:
                raise Exception(err)
            if not d:
                form = admin_forms.ConfigureEmailForm()
            else:
                if d["tls"]:
                    d["tls"] = True
                else:
                    d["tls"] = False
                if d["email_alerts"]:
                    d["email_alerts"] = True
                else:
                    d["email_alerts"] = False
                form = admin_forms.ConfigureEmailForm(initial={'email_server': d["server"], 'email_server_port': d["port"], 'tls': d["tls"], 'username': d[
                                                      "username"], 'email_alerts': d["email_alerts"], 'rcpt_list': d["rcpt_list"], "email_audit": True, "email_quota": True})
        else:
            form = admin_forms.ConfigureEmailForm(request.POST)
            if form.is_valid():
                print 'valid'
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
                if "email_audit" in cd:
                    d["email_audit"] = cd["email_audit"]
                else:
                    d["email_audit"] = False
                if "email_quota" in cd:
                    d["email_quota"] = cd["email_quota"]
                else:
                    d["email_quota"] = False
                # print "Saving : "
                # print d
                ret, err = mail.save_email_settings(d)
                if err:
                    raise Exception(err)

                ret, err = mail.send_mail(cd["email_server"], cd["email_server_port"], cd["username"], cd["pswd"], cd["tls"], cd["rcpt_list"], "Test email from IntegralStor",
                                          "This is a test email sent by the IntegralStor system in order to confirm that your email settings are working correctly.")
                print ret, err
                if err:
                    raise Exception(err)
                if ret:
                    return django.http.HttpResponseRedirect("/view_email_settings?ack=saved")
                else:
                    return django.http.HttpResponseRedirect("/view_email_settings?ack=saved&err=%s" % err)
            else:
                # print 'invalid form'
                pass
        return_dict["form"] = form
        return django.shortcuts.render_to_response('edit_email_settings.html', return_dict, context_instance=django.template.context.RequestContext(request))
    except Exception, e:
        return_dict["error_details"] = str(e)
        return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))


'''

def remove_email_settings(request):

  response = django.http.HttpResponse()
  #iv_logging.info("Email settings deleted")
  try:
    mail.delete_email_settings()
    response.write("Deleted email settings")
  except Exception, e:
    response.write("Error deleteing email settings : %s"%e)
  return response


'''

# vim: tabstop=8 softtabstop=0 expandtab ai shiftwidth=4 smarttab
