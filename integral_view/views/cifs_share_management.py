
import django
import django.template

import salt.client

import integral_view
from integral_view.forms import cifs_shares_forms
from integralstor_gridcell import gluster_volumes, system_info, local_users, iscsi, gluster_gfapi
from integralstor_gridcell import cifs as cifs_gridcell
from integralstor_common import networking, audit, lock
from integralstor_common import cifs as cifs_common
from integralstor_common import common
import os.path


def view_cifs_shares(request):

    return_dict = {}
    try:
        return_dict['base_template'] = "shares_and_targets_base.html"
        return_dict["page_title"] = 'View CIFS shares'
        return_dict['tab'] = 'view_cifs_shares_tab'
        return_dict["error"] = 'Error viewing CIFS shares'

        shares_list, err = cifs_common.get_shares_list()
        if err:
            raise Exception(err)

        if "ack" in request.GET:
            if request.GET["ack"] == "saved":
                conf = "Share information successfully updated"
            elif request.GET["ack"] == "created":
                conf = "Share successfully created"
            elif request.GET["ack"] == "deleted":
                conf = "Share successfully removed. Please note that the underlying data has not been removed."
            return_dict["ack_message"] = conf
        return_dict["shares_list"] = shares_list
        return django.shortcuts.render_to_response('view_cifs_shares.html', return_dict, context_instance=django.template.context.RequestContext(request))
    except Exception, e:
        s = str(e)
        if "Another transaction is in progress".lower() in s.lower():
            return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
        else:
            return_dict["error_details"] = "An error occurred when processing your request : %s" % s
        return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


def view_cifs_share(request):

    return_dict = {}
    try:
        return_dict['base_template'] = "shares_and_targets_base.html"
        return_dict["page_title"] = 'View CIFS share details'
        return_dict['tab'] = 'view_cifs_shares_tab'
        return_dict["error"] = 'Error viewing CIFS share details'

        if request.method != "GET":
            raise Exception("Incorrect access method. Please use the menus")

        if "index" not in request.GET or "access_mode" not in request.GET:
            raise Exception("Unknown share")

        access_mode = request.GET["access_mode"]
        index = request.GET["index"]

        if "ack" in request.GET and request.GET["ack"] == "saved":
            return_dict["ack_message"] = "Share properties updated successfully"

        valid_users_list = None
        share, err = cifs_common.get_share_info(access_mode, index)
        if err:
            raise Exception(err)
        valid_users_list, err = cifs_common.get_valid_users_list(
            share["share_id"])
        if err:
            raise Exception(err)
        if not share:
            raise Exception(
                "Error retrieving share information for  %s" % share_name)
        return_dict["share"] = share
        if valid_users_list:
            return_dict["valid_users_list"] = valid_users_list

        return django.shortcuts.render_to_response('view_cifs_share.html', return_dict, context_instance=django.template.context.RequestContext(request))
    except Exception, e:
        s = str(e)
        if "Another transaction is in progress".lower() in s.lower():
            return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
        else:
            return_dict["error_details"] = "An error occurred when processing your request : %s" % s
        return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


def edit_cifs_share(request):

    return_dict = {}
    try:
        gluster_lck, err = lock.get_lock('gluster_commands')
        if err:
            raise Exception(err)

        if not gluster_lck:
            raise Exception(
                'This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')

        return_dict['base_template'] = "shares_and_targets_base.html"
        return_dict["page_title"] = 'Edit CIFS share details'
        return_dict['tab'] = 'view_cifs_shares_tab'
        return_dict["error"] = 'Error editing CIFS share details'

        vil, err = gluster_volumes.get_basic_volume_info_all()
        if err:
            raise Exception(err)
        if not vil:
            raise Exception('Could not load volume information')
        user_list, err = cifs_gridcell.get_user_list()
        if err:
            raise Exception(err)
        group_list, err = cifs_gridcell.get_group_list()
        if err:
            raise Exception(err)

        if request.method == "GET":
            # Shd be an edit request
            if "share_id" not in request.GET:
                raise Exception("Unknown share specified")
            share_id = request.GET["share_id"]
            share_dict, err = cifs_common.get_share_info("by_id", share_id)
            if err:
                raise Exception(err)
            valid_users_list, err = cifs_common.get_valid_users_list(
                share_dict["share_id"])
            if err:
                raise Exception(err)

            # Set initial form values
            initial = {}
            initial["share_id"] = share_dict["share_id"]
            initial["name"] = share_dict["name"]
            initial["path"] = share_dict["path"]
            initial["display_path"] = share_dict["display_path"]
            initial["vol"] = share_dict["vol"]
            if share_dict["guest_ok"]:
                initial["guest_ok"] = True
            else:
                initial["guest_ok"] = False
            if share_dict["browseable"]:
                initial["browseable"] = True
            else:
                initial["browseable"] = False
            if share_dict["read_only"]:
                initial["read_only"] = True
            else:
                initial["read_only"] = False
            initial["comment"] = share_dict["comment"]

            if valid_users_list:
                vgl = []
                vul = []
                for u in valid_users_list:
                    if u["grp"]:
                        vgl.append(u["name"])
                    else:
                        vul.append(u["name"])
                initial["users"] = vul
                initial["groups"] = vgl

            form = cifs_shares_forms.ShareForm(
                initial=initial, user_list=user_list, group_list=group_list, volume_list=vil)

            return_dict["form"] = form
            return django.shortcuts.render_to_response('edit_cifs_share.html', return_dict, context_instance=django.template.context.RequestContext(request))

        else:

            # Shd be an save request
            form = cifs_shares_forms.ShareForm(
                request.POST, user_list=user_list, group_list=group_list, volume_list=vil)
            return_dict["form"] = form
            if form.is_valid():
                cd = form.cleaned_data
                name = cd["name"]
                share_id = cd["share_id"]
                path = cd["path"]
                if "comment" in cd:
                    comment = cd["comment"]
                else:
                    comment = None
                if "read_only" in cd:
                    read_only = cd["read_only"]
                else:
                    read_only = False
                if "browseable" in cd:
                    browseable = cd["browseable"]
                else:
                    browseable = False
                if "guest_ok" in cd:
                    guest_ok = cd["guest_ok"]
                else:
                    guest_ok = False
                if "users" in cd:
                    users = cd["users"]
                else:
                    users = None
                if "groups" in cd:
                    groups = cd["groups"]
                else:
                    groups = None
                vol = cd["vol"]
                ret, err = cifs_common.update_share(
                    share_id, name, comment, guest_ok, read_only, path, browseable, users, groups)
                if err:
                    raise Exception(err)
                if not ret:
                    raise Exception('Error saving share')
                ret, err = cifs_gridcell.generate_smb_conf()
                if err:
                    raise Exception(err)
                if not ret:
                    raise Exception('Error generating CIFS configuration file')

                audit_str = "Modified share %s" % cd["name"]
                ret, err = audit.audit("modify_share", audit_str, request.META)
                if err:
                    raise Exception(err)

                return django.http.HttpResponseRedirect('/view_cifs_share?access_mode=by_id&index=%s&ack=saved' % cd["share_id"])

            else:
                # Invalid form
                return django.shortcuts.render_to_response('edit_cifs_share.html', return_dict, context_instance=django.template.context.RequestContext(request))
    except Exception, e:
        s = str(e)
        if "Another transaction is in progress".lower() in s.lower():
            return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
        else:
            return_dict["error_details"] = "An error occurred when processing your request : %s" % s
        return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
    finally:
        lock.release_lock('gluster_commands')


def delete_cifs_share(request):

    return_dict = {}
    try:
        return_dict['base_template'] = "shares_and_targets_base.html"
        return_dict["page_title"] = 'Delete a CIFS share'
        return_dict['tab'] = 'view_cifs_shares_tab'
        return_dict["error"] = 'Error deleteing a CIFS share'

        print request.REQUEST.keys()
        if 'share_id' not in request.REQUEST or 'name' not in request.REQUEST:
            raise Exception(
                'Invalid request. Required parameters not passed. Please use the menus.')

        share_id = request.REQUEST["share_id"]
        name = request.REQUEST["name"]
        if request.method == "GET":
            # Return the conf page
            return_dict["share_id"] = share_id
            return_dict["name"] = name
            return django.shortcuts.render_to_response("delete_cifs_share_conf.html", return_dict, context_instance=django.template.context.RequestContext(request))
        else:
            ret, err = cifs_common.delete_share(share_id)
            if err:
                raise Exception(err)
            if not ret:
                raise Exception('Error deleting share')
            ret, err = cifs_gridcell.generate_smb_conf()
            if err:
                raise Exception(err)
            if not ret:
                raise Exception('Error generating CIFS configuration file')

            audit_str = "Deleted Windows share %s" % name
            ret, err = audit.audit("delete_share", audit_str, request.META)
            if err:
                raise Exception(err)
            return django.http.HttpResponseRedirect('/view_cifs_shares?ack=deleted')
    except Exception, e:
        s = str(e)
        if "Another transaction is in progress".lower() in s.lower():
            return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
        else:
            return_dict["error_details"] = "An error occurred when processing your request : %s" % s
        return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


def create_cifs_share(request):

    return_dict = {}
    try:
        return_dict['base_template'] = "shares_and_targets_base.html"
        return_dict["page_title"] = 'Create a Windows share'
        return_dict['tab'] = 'view_cifs_shares_tab'
        return_dict["error"] = 'Error creating a Windows share'

        gluster_lck, err = lock.get_lock('gluster_commands')
        if err:
            raise Exception(err)

        if not gluster_lck:
            raise Exception(
                'This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')

        user_list, err = cifs_gridcell.get_user_list()
        if err:
            raise Exception(err)
        group_list, err = cifs_gridcell.get_group_list()
        if err:
            raise Exception(err)

        if 'vol_name' in request.REQUEST:
            return_dict['vol_name'] = request.REQUEST['vol_name']

        vil, err = gluster_volumes.get_basic_volume_info_all()
        if err:
            raise Exception(err)
        if not vil:
            raise Exception(
                'No volumes have been created. Please create a volume before creating shares.')

        il, err = iscsi.load_iscsi_volumes_list(vil)
        if err:
            raise Exception(err)
        vl = []
        for v in vil:
            # Get only file based volumes that have been started
            if il and v["name"] in il:
                continue
            if v['status'] != 1:
                continue
            vl.append(v)
        if not vl:
            raise Exception(
                'Shares can only be created on volumes that are file based and that are started. No volumes seem to match these criteria.')

        if request.method == "GET":
            # Return the form
            form = cifs_shares_forms.CreateShareForm(
                user_list=user_list, group_list=group_list, volume_list=vl)
            return_dict["form"] = form
            return django.shortcuts.render_to_response("create_cifs_share.html", return_dict, context_instance=django.template.context.RequestContext(request))
        else:
            # Form submission so create
            form = cifs_shares_forms.CreateShareForm(
                request.POST, user_list=user_list, group_list=group_list, volume_list=vl)
            return_dict["form"] = form
            # print request.POST
            if form.is_valid():
                # print return_dict
                cd = form.cleaned_data
                # print cd
                name = cd["name"]
                path = "%s" % cd["path"]

                if "comment" in cd:
                    comment = cd["comment"]
                else:
                    comment = None
                if "read_only" in cd:
                    read_only = cd["read_only"]
                else:
                    read_only = None
                if "browseable" in cd:
                    browseable = cd["browseable"]
                else:
                    browseable = None
                if "guest_ok" in cd:
                    guest_ok = cd["guest_ok"]
                else:
                    guest_ok = None
                if "users" in cd:
                    users = cd["users"]
                else:
                    users = None
                if "groups" in cd:
                    groups = cd["groups"]
                else:
                    groups = None
                vol = cd["vol"]
                if 'new_dir_name' in cd and cd['new_dir_name'].strip():
                    path = os.path.join(path, cd['new_dir_name'])
                    # print path
                    ret, err = gluster_gfapi.create_gluster_dir(vol, path)
                    if err:
                        raise Exception(err)
                # print users, groups
                ret, err = cifs_common.create_share(
                    name, comment, guest_ok, read_only, path, "", browseable, users, groups, vol)
                if err:
                    raise Exception(err)
                if not ret:
                    raise Exception('Error creating share')
                ret, err = cifs_gridcell.generate_smb_conf()
                if err:
                    raise Exception(err)
                if not ret:
                    raise Exception('Error generating CIFS configuration file')

                audit_str = "Created Windows share %s" % name
                ret, err = audit.audit("create_share", audit_str, request.META)
                if err:
                    raise Exception(err)
                return django.http.HttpResponseRedirect('/view_cifs_shares?ack=created')
            else:
                return django.shortcuts.render_to_response("create_cifs_share.html", return_dict, context_instance=django.template.context.RequestContext(request))
    except Exception, e:
        s = str(e)
        if "Another transaction is in progress".lower() in s.lower():
            return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
        else:
            return_dict["error_details"] = "An error occurred when processing your request : %s" % s
        return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
    finally:
        lock.release_lock('gluster_commands')


def view_cifs_authentication_settings(request):

    return_dict = {}
    try:
        return_dict['base_template'] = "services_base.html"
        return_dict["page_title"] = 'Configure CIFS access'
        return_dict['tab'] = 'service_cifs_access_tab'
        return_dict["error"] = 'Error configuring CIFS access'

        d, err = cifs_common.get_auth_settings()
        if err:
            raise Exception(err)

        return_dict["auth_settings_dict"] = d

        if "ack" in request.REQUEST and request.REQUEST["ack"] == "saved":
            return_dict["ack_message"] = "Information updated successfully"
        return django.shortcuts.render_to_response('view_cifs_authentication_settings.html', return_dict, context_instance=django.template.context.RequestContext(request))
    except Exception, e:
        s = str(e)
        if "Another transaction is in progress".lower() in s.lower():
            return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
        else:
            return_dict["error_details"] = "An error occurred when processing your request : %s" % s
        return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


def edit_cifs_authentication_settings(request):

    return_dict = {}
    try:
        return_dict['base_template'] = "services_base.html"
        return_dict["page_title"] = 'Configure CIFS access'
        return_dict['tab'] = 'service_cifs_access_tab'
        return_dict["error"] = 'Error configuring CIFS access'

        if request.method == 'GET':
            d, err = cifs_common.get_auth_settings()
            if err:
                raise Exception(err)

            ini = {}
            if d:
                for k in d.keys():
                    ini[k] = d[k]
            if d and d["security"] == "ads":
                form = cifs_shares_forms.ADAuthenticationSettingsForm(
                    initial=ini)
            else:
                form = cifs_shares_forms.LocalUsersAuthenticationSettingsForm(
                    initial=ini)
            return_dict["form"] = form
            return django.shortcuts.render_to_response('edit_cifs_authentication_settings.html', return_dict, context_instance=django.template.context.RequestContext(request))
        else:
            # Save request
            if "security" not in request.POST:
                raise Exception(
                    "Invalid security specification. Please try again using the menus")

            if request.POST["security"] == "ads":
                form = cifs_shares_forms.ADAuthenticationSettingsForm(
                    request.POST)
            elif request.POST["security"] == "users":
                form = cifs_shares_forms.LocalUsersAuthenticationSettingsForm(
                    request.POST)
            else:
                raise Exception(
                    "Invalid security specification. Please try again using the menus")

            return_dict["form"] = form
            return_dict["action"] = "edit"

            if form.is_valid():
                # print 'valid form!'
                cd = form.cleaned_data

                ret, err = cifs_common.update_auth_settings(cd)
                if err:
                    raise Exception(err)
                # print '1'

                if cd["security"] == "ads":
                    client = salt.client.LocalClient()
                    results = client.cmd(
                        '*', 'integralstor.configure_name_servers', [cd['password_server_ip']])
                    if results:
                        for node, ret in results.items():
                            if not ret[0]:
                                raise Exception(
                                    "Error updating the DNS configuration on GRIDCell %s" % node)
                '''
        # We now need to add the AD server as the forwarder in our DNS config on the primary...
        nsl, err = networking.get_name_servers()
        if err:
          raise Exception(err)
        if not nsl:
          raise Exception("Could not detect the IP addresses of the primary and secondary GRIDCells")
        if len(nsl) < 2:
          raise Exception("Could not detect the IP addresses of the primary and secondary GRIDCells")
        ipinfo, err = networking.get_ip_info('bond0')
        if err:
          raise Exception(err)
        if cd["security"] == "ads":
          rc, err = networking.generate_default_primary_named_conf(nsl[0], ipinfo['netmask'], nsl[1], True, cd['password_server_ip'], False)
          if err:
            raise Exception(err)
          if not rc:
            raise Exception("Error updating the DNS configuration on the primary GRIDCell")

          # ... and on the secondary
          client = salt.client.LocalClient()
          python_scripts_path, err = common.get_python_scripts_path()
          if err:
            raise Exception(err)
          r2 = client.cmd('roles:secondary', 'cmd.run_all', ['python %s/create_secondary_named_config.py %s %s %s %s'%(python_scripts_path, nsl[0], nsl[1], ipinfo['netmask'], cd['password_server_ip'])], expr_form='grain')
          if r2:
            for node, ret in r2.items():
              if ret["retcode"] != 0:
                raise Exception("Error updating the DNS configuration on the primary GRIDCell")
        '''

                # print '2'
                if cd["security"] == "ads":
                    ret, err = cifs_common.generate_krb5_conf()
                    if err:
                        raise Exception(err)
                    if not ret:
                        raise Exception(
                            'Error generating the kerberos config file')
                ret, err = cifs_gridcell.generate_smb_conf()
                if err:
                    raise Exception(err)
                if not ret:
                    raise Exception('Error generating CIFS configuration file')
                if cd["security"] == "ads":
                    rc, err = cifs_gridcell.kinit(
                        "administrator", cd["password"], cd["realm"])
                    if err:
                        raise Exception(err)
                    if not rc:
                        raise Exception("Kerberos init failure")
                print cd
                if cd["security"] == "ads":
                    rc, err = cifs_gridcell.net_ads_join(
                        "administrator", cd["password"], cd["password_server"])
                    if err:
                        raise Exception(err)
                    if not rc:
                        raise Exception("AD join failure")
                ret, err = cifs_gridcell.restart_samba_services()
                if err:
                    raise Exception(err)
                if not ret:
                    raise Exception('Error restarting the CIFS service')
            else:
                return django.shortcuts.render_to_response('edit_cifs_authentication_settings.html', return_dict, context_instance=django.template.context.RequestContext(request))

            # print '7'
            audit_str = "Modified share authentication settings"
            ret, err = audit.audit(
                "modify_samba_settings", audit_str, request.META)
            if err:
                raise Exception(err)
            #return_dict["conf_message"] = "Information successfully updated"
            # print '8'
            return django.http.HttpResponseRedirect('/view_cifs_authentication_settings?ack=saved')

    except Exception, e:
        s = str(e)
        if "Another transaction is in progress".lower() in s.lower():
            return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
        else:
            return_dict["error_details"] = "An error occurred when processing your request : %s" % s
        return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


def edit_cifs_authentication_method(request):
    return_dict = {}
    try:
        return_dict['base_template'] = "services_base.html"
        return_dict["page_title"] = 'Configure CIFS access method'
        return_dict['tab'] = 'service_cifs_access_tab'
        return_dict["error"] = 'Error configuring CIFS access method'
        d, err = cifs_common.get_auth_settings()
        if err:
            raise Exception(err)
        return_dict["samba_global_dict"] = d

        if request.method == "GET":
            return django.shortcuts.render_to_response('edit_cifs_authentication_method.html', return_dict, context_instance=django.template.context.RequestContext(request))
        else:
            # Save request
            if "auth_method" not in request.POST:
                raise Exception("Please select an authentication method")
            security = request.POST["auth_method"]
            if security == d["security"]:
                raise Exception(
                    "Selected authentication method is the same as before.")

            ret, err = cifs_common.update_auth_method(security)
            if err:
                raise Exception(err)
            if not ret:
                raise Exception('Error changing authentication method')
            ret, err = cifs_gridcell.generate_smb_conf()
            if err:
                raise Exception(err)
            if not ret:
                raise Exception('Error generating CIFS configuration file')

        return django.http.HttpResponseRedirect('/edit_cifs_authentication_settings')
    except Exception, e:
        s = str(e)
        if "Another transaction is in progress".lower() in s.lower():
            return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
        else:
            return_dict["error_details"] = "An error occurred when processing your request : %s" % s
        return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


'''
def save_samba_server_settings(request):

  return_dict = {}
  try:
    return_dict['base_template'] = "services_base.html"
    return_dict["page_title"] = 'Configure CIFS access'
    return_dict['tab'] = 'service_cifs_access_tab'
    return_dict["error"] = 'Error configuring CIFS access'
    if request.method != "POST":
      raise Exception("Invalid access method. Please try again using the menus")
  
    if "security" not in request.POST:
      raise Exception("Invalid security specification. Please try again using the menus")
  
    if request.POST["security"] == "ads":
      form = samba_shares_forms.ADAuthenticationSettingsForm(request.POST)
    elif request.POST["security"] == "users":
      form = samba_shares_forms.LocalUsersAuthenticationSettingsForm(request.POST)
    else:
      raise Exception("Invalid security specification. Please try again using the menus")
  
    return_dict["form"] = form
    return_dict["action"] = "edit"
  
    if form.is_valid():
      cd = form.cleaned_data
  
      ret, err = cifs_common.update_auth_settings(cd)
      if err:
        raise Exception(err)
      #print '1'

      # We now need to add the AD server as the forwarder in our DNS config on the primary...
      nsl, err = networking.get_name_servers()
      if err:
        raise Exception(err)
      if not nsl:
        raise Exception("Could not detect the IP addresses of the primary and secondary GRIDCells")
      if len(nsl) < 2:
        raise Exception("Could not detect the IP addresses of the primary and secondary GRIDCells")
      ipinfo, err = networking.get_ip_info('bond0')
      if err:
        raise Exception(err)
      if cd["security"] == "ads":
        rc, err = networking.generate_default_primary_named_conf(nsl[0], ipinfo['netmask'], nsl[1], True, cd['password_server_ip'], False)
        if err:
          raise Exception(err)
        if not rc:
          raise Exception("Error updating the DNS configuration on the primary GRIDCell")

        # ... and on the secondary
        client = salt.client.LocalClient()
        python_scripts_path, err = common.get_python_scripts_path()
        if err:
          raise Exception(err)
        r2 = client.cmd('roles:secondary', 'cmd.run_all', ['python %s/create_secondary_named_config.py %s %s %s %s'%(python_scripts_path, nsl[0], nsl[1], ipinfo['netmask'], cd['password_server_ip'])], expr_form='grain')
        if r2:
          for node, ret in r2.items():
            if ret["retcode"] != 0:
              raise Exception("Error updating the DNS configuration on the primary GRIDCell")

      #print '2'
      if cd["security"] == "ads":
        ret, err = cifs_common.generate_krb5_conf()
        if err:
          raise Exception(err)
        if not ret:
          raise Exception('Error generating the kerberos config file')
      ret, err = cifs_gridcell.generate_smb_conf()
      if err:
        raise Exception(err)
      if not ret:
        raise Exception('Error generating CIFS configuration file')
      if cd["security"] == "ads":
        rc, err = cifs_gridcell.kinit("administrator", cd["password"], cd["realm"])
        if err:
          raise Exception(err)
        if not rc:
          raise Exception("Kerberos init failure")
      if cd["security"] == "ads":
        rc, err = cifs_gridcell.net_ads_join("administrator", cd["password"], cd["password_server"])
        if err:
          raise Exception(err)
        if not rc:
          raise Exception("AD join failure")
      ret, err = cifs_gridcell.restart_samba_services()
      if err:
        raise Exception(err)
      if not ret:
        raise Exception('Error restarting the CIFS service')
    return django.shortcuts.render_to_response('edit_samba_server_settings.html', return_dict, context_instance=django.template.context.RequestContext(request))
  
    #print '7'
    audit_str = "Modified share authentication settings"
    ret, err = audit.audit("modify_samba_settings", audit_str, request.META)
    if err:
      raise Exception(err)
    return_dict["form"] = form
    return_dict["conf_message"] = "Information successfully updated"
    #print '8'
    return django.http.HttpResponseRedirect('/auth_server_settings?ack=saved')
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))



'''

# vim: tabstop=8 softtabstop=0 expandtab ai shiftwidth=4 smarttab
