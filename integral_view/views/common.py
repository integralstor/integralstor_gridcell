import json, time, os, shutil, tempfile, os.path, re, subprocess, sys

import salt.client, salt.wheel

import django.template, django
from django.conf import settings


import integral_view
from integral_view.utils import audit, batch, alerts, ntp, mail, gluster_commands, command, iv_logging,db
from integral_view.utils import volume_info, system_info
import logging
from integral_view.iscsi import iscsi
from integral_view.forms import common_forms
from integral_view.samba import samba_settings


    
def show(request, page, info = None):

    assert request.method == 'GET'

    vil = volume_info.get_volume_info_all()
    si = system_info.load_system_config()

    #assert False
    return_dict = {}
    return_dict['system_info'] = si
    return_dict['volume_info_list'] = vil

    #By default show error page
    template = "logged_in_error.html"

    if page == "dir_contents":
      dir_name = None
      error = False
      path_base = None
      vol_name = ""
      dir_list = []
      try: 
        if not "vol_name" in request.GET:
          raise Exception ("No volume Specified")
        else:
          vol_name = request.GET["vol_name"]
        if settings.PRODUCTION:
          path_base = "/tmp/vol/"
          #path_base = "/"
        else:
          path_base = "/home/bkrram"
        #if (not "dir" in request.GET) or (not "full_path" in request.GET):
        #if  (not "full_path" in request.GET):
        if  (not "dir" in request.GET):
          raise Exception ("No dir in request")
        else:
          dir_name = request.GET["dir"]
          #full_path = request.GET["full_path"]
          #print "walking %s. In reality will walk /%s"%(full_path, vol_name)
        dl = None
        #if full_path: 
        full_path="%s/%s"%(path_base, dir_name)
        full_path=os.path.abspath(full_path)
        iv_logging.debug("Full path %s"%full_path)
        if dir_name: 
          try:
            #print "walking %s. In reality will walk /%s"%(full_path, vol_name)
            #dl = gluster_commands.list_dir(vol_name, full_path)
            dl = os.walk(full_path).next()[1]
          except Exception, e:
            iv_logging.debug("Error walking path : %s"%e)
            raise Exception ("Error walking path : %s"%e)
        if dl:
          for l in dl:
            children = False
            try:
              if len(os.walk("%s/%s"%(full_path, l)).next()[1]) > 0:
                children = True
              else:
                children = False
            except Exception, e:
              iv_logging.debug("Error walking path : %s"%e)
              raise Exception ("Error walking path : %s"%e)
            #d = {"text":l, "children":children, 'data':{'full_path':"%s/%s"%(full_path, l), 'dir':"%s/%s"%(dir_name, l)}}
            print "dir_name is %s"%dir_name
            iv_logging.debug("Dir name is %s"%dir_name)
            if dir_name == "/":
              send_path = "%s"%(l)
            else:
              send_path = "%s/%s"%(dir_name, l)
            iv_logging.debug("Send path is %s"%send_path)
            d = {"text":l, "children":children, 'data':{'dir':send_path}}
            dir_list.append(d)
      except Exception as e:
        iv_logging.debug("Exception while getting dir listing : "%e)
        d = { "text":"_error_", "children":False}
        dir_list.append(d)
      dlist = django.utils.simplejson.dumps(dir_list)
      return django.http.HttpResponse(dlist,mimetype='application/json')

    elif page == "ntp_settings":

      template = "view_ntp_settings.html"
      try:
        ntp_servers = ntp.get_ntp_servers()
      except Exception, e:
        return_dict["error"] = str(e)
      else:
        return_dict["ntp_servers"] = ntp_servers
      if "saved" in request.REQUEST:
        return_dict["saved"] = request.REQUEST["saved"]

    elif page == "integral_view_log_level":

      template = "view_integral_view_log_level.html"
      try:
        log_level = iv_logging.get_log_level_str()
      except Exception, e:
        return_dict["error"] = str(e)
      else:
        return_dict["log_level_str"] = log_level
      if "saved" in request.REQUEST:
        return_dict["saved"] = request.REQUEST["saved"]

    elif page == "email_settings":

      #print "here"
      try:
        d = mail.load_email_settings()
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
        if "saved" in request.REQUEST:
          return_dict["saved"] = request.REQUEST["saved"]
        if "not_saved" in request.REQUEST:
          return_dict["not_saved"] = request.REQUEST["not_saved"]
        if "err" in request.REQUEST:
          return_dict["err"] = request.REQUEST["err"]
        template = "view_email_settings.html"
      except Exception, e:
        iv_logging.debug("error loading email settings %s"%e)
        return_dict["error"] = str(e)

    elif page == "audit_trail":

      al = None
      try:
        al = audit.get_lines()
      except Exception, e:
        return_dict["error"] = str(e)
      else:
        template = "view_audit_trail.html"
        return_dict["audit_list"] = al

    elif page == "batch_start_conf":

      #Display a confirmation that the batch job has been scheduled. info contains the filename of the batch job
      template = "batch_start_conf.html"
      return_dict["fname"] = info

    elif page == "batch_status":

      #Load the list of entries from all the files in the start and process directories
      try :
        file_list = batch.load_all_files("in_process")
      except Exception, e:
        return_dict["error"] = "Error loading batch files: %s"%e
      else:
        return_dict["file_list"] = file_list
        template = "view_batch_process_list.html"

    elif page == "batch_status_details":

      try:
        d = batch.load_specific_file(info)
      except Exception, e:
        return_dict["error"] = "Error reading batch file: %s"%e
      else:
        if not d:
          return_dict["error"] = "Unknown process specified"
        else:
          return_dict["process_info"] = d
          template = "view_batch_status_details.html"

    elif page == "volume_info":

      vol = volume_info.get_volume_info(vil, info)

      if vol:
        template = "view_volume_info.html"
        return_dict["vol"] = vol
        data_locations_list = volume_info.get_brick_hostname_list(vol)
        #print data_locations_list
        return_dict["data_locations_list"] = data_locations_list

        ivl = iscsi.load_iscsi_volumes_list(vil)
        if ivl and vol["name"] in ivl:
          return_dict["iscsi"] = True

        # To accomodate django template quirks
        if vol["type"] in ["Replicate", "Distributed-Replicate"]:
          return_dict["replicate"] = True
        elif vol["type"] in ["Distribute", "Distributed-Replicate"]:
          return_dict["distribute"] = True
      else:
        return_dict["error"] = "Could not locate information for volume %s"%info

    elif page == "volume_status":

      vol = volume_info.get_volume_info(vil, info)

      if vol:
        template = "view_volume_status.html"
        return_dict["vol"] = vol

        # To accomodate django template quirks
        if vol["type"] in ["Replicate", "Distributed-Replicate"]:
          return_dict["replicate"] = True
        elif vol["type"] in ["Distribute", "Distributed-Replicate"]:
          return_dict["distribute"] = True
      else:
        return_dict["error"] = "Could not locate information for volume %s"%info
          
    elif page == "node_status":

      template = "view_node_status.html"
      if "from" in request.GET:
        frm = request.GET["from"]
        return_dict['frm'] = frm
      vol_list = volume_info.get_volumes_on_node(info, vil)
      return_dict['node'] = si[info]
      return_dict['node_name'] = info

      return_dict['vol_list'] = vol_list

    elif page == "node_info":

      template = "view_node_info.html"
      if "from" in request.GET:
        frm = request.GET["from"]
        return_dict['frm'] = frm
      vol_list = volume_info.get_volumes_on_node(info, vil)
      return_dict['node'] = si[info]
      return_dict['vol_list'] = vol_list

    elif page=="refresh_status":
      if "file_name" not in request.REQUEST:
        return_dict['error'] = 'Invalid request. No status file specified'
        return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))
      file_name = request.REQUEST["file_name"]
      if not os.path.isfile("%s/status/%s"%(settings.BASE_FILE_PATH, file_name)):
        return_dict['error'] = 'The requested status file does not exist'
        return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))
      o = ""
      with open("%s/status/%s"%(settings.BASE_FILE_PATH, file_name), "r") as f:
        l = f.readline()
        #print l
        while l:
          tl = l.rstrip()
          if tl == "==done==":
            #print "done"
            o += '<script type="text/javascript">'
            o += 'window.done = 1;'
            o+= '</script>'
            break
          else:
            #print l
            o += l
            o += "<br>"
          l = f.readline()
      return django.http.HttpResponse(o)

    elif page=="manifest":
      #Basically read a generated manifest file and display the results.
      if "manifest" not in request.GET:
        return_dict['error'] = 'Invalid request. No manifest file specified'
        return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))
      manifest = request.GET["manifest"]
      try :
        with open("%s/manifest/%s"%(settings.BASE_FILE_PATH, manifest), "r") as f:
          nodes = json.load(f)
      except Exception, e:
        return_dict['error'] = 'Error loading the new configuratio : %s'%e
        return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))
      
      return_dict["manifest"] = nodes
      return_dict["manifest_file"] = manifest
      return django.shortcuts.render_to_response('view_manifest.html', return_dict, context_instance=django.template.context.RequestContext(request))
      
          
    elif page == "iscsi_auth_access_info":
      if 'id' not in request.GET:
        return_dict['error'] = 'Invalid request. No auth access id specified'
        return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))
      else:
        id = int(request.GET['id'])
        l = iscsi.load_auth_access_users_info(id)
        if l:
          str = "<b>Authorized access group users : </b>"
          for i in l:
            str += i["user"]
            str += ", "
          #return django.http.HttpResponse("<b>Authorized access details </b><br>User : %s, Peer user : %s"%(d["user"],d["peer_user"] ))
          return django.http.HttpResponse("%s"%str)
        else:
          return_dict['error'] = 'No auth access information for the id specified'
          return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))

    elif page == "iscsi_initiator_info":
      if 'id' not in request.GET:
        return_dict['error'] = 'Invalid request. No initiator access id specified'
        return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))
      else:
        id = int(request.GET['id'])
        d = iscsi.load_initiator_info(id)
        if d:
          return django.http.HttpResponse("<b>Initiator details</b><br>Initiators : %s, Auth network : %s, Comment : %s"%(d["initiators"],d["auth_network"], d["comment"] ))
        else:
          return_dict['error'] = 'No initiator information for the id specified'
          return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))

    elif page == "system_config":

      template = "view_system_config.html"

    elif page == "system_status":

      template = "view_system_status.html"

    elif page == "disk_status":

      #assert False
      template = "view_disk_status.html"

    elif page == "pool_status":

      template = "view_pool_status.html"
      num_free_nodes = 0
      for name, node in si.items():
        if node["node_status"] >= 0  and (not node["in_cluster"]):
          num_free_nodes += 1
      return_dict['num_free_nodes'] = num_free_nodes

    elif page == "dashboard":

      num_nodes_bad = 0
      num_pools_bad = 0
      num_vols_bad = 0
      total_pool = 0
      total_nodes = len(si)
      total_vols = len(vil)

      for k, v in si.items():
        if v["node_status"] != 0:
          num_nodes_bad += 1
        if v["in_cluster"] :
          total_pool += 1
          if v["cluster_status"] != 1:
            num_pools_bad += 1
          

      for vol in vil:
        if vol["status"] == 1 :
          if vol["data_access_status_code"] != 0 or (not vol["processes_ok"]):
            num_vols_bad += 1
          
      return_dict["num_nodes_bad"] = num_nodes_bad            
      return_dict["num_pools_bad"] = num_pools_bad            
      return_dict["num_vols_bad"] = num_vols_bad            
      return_dict["total_nodes"] = total_nodes            
      return_dict["total_pool"] = total_pool            
      return_dict["total_vols"] = total_vols            

      template = "view_dashboard.html"

    elif page == "alerts":

      template = "view_alerts.html"
      alerts_list = alerts.load_alerts()
      return_dict['alerts_list'] = alerts_list

    elif page == "volume_info_all":

      template = "view_volume_info_all.html"
      return_dict['volume_info_list'] = vil
      ivl = iscsi.load_iscsi_volumes_list(vil)
      return_dict['iscsi_volumes'] = ivl

    elif page == "volume_status_all":

      template = "view_volume_status_all.html"
      return_dict['volume_info_list'] = vil

    return django.shortcuts.render_to_response(template, return_dict, context_instance=django.template.context.RequestContext(request))

#this function takes a user argument checks if the user has administrator rights and then returns True.
#If he does not have the correct permissions, then then it returns a HTttpResponse stating No Permission to access this page.
#Takes user object as a parameter: request.user
def admin_login_required(user):
  if user.is_superuser:
    return True
  else:
    return False

def refresh_alerts(request, random=None):
    from datetime import datetime
    cmd_list = []
    #this command will insert or update the row value if the row with the user exists.
    cmd = ["INSERT OR REPLACE INTO admin_alerts (user, last_refresh_time) values (?,?);", (request.user.username, datetime.now())]
    cmd_list.append(cmd)
    test = db.execute_iud(cmd_list)
    if alerts.new_alerts():
      import json
      new_alerts = json.dumps([dict(alert=pn) for pn in alerts.load_alerts()])
      return django.http.HttpResponse(new_alerts, mimetype='application/json')
    else:
      clss = "btn btn-default btn-sm"
      message = "View alerts"
      return django.http.HttpResponse("No New Alerts")

def raise_alert(request):

  return_dict = {}
  template = "logged_in_error.html"
  if "msg" not in request.REQUEST:
    return_dict["error"] = "No alert message specified."
  else:
    try:
      msg = request.REQUEST["msg"]
      alerts.raise_alert(msg)
    except Exception, e:
      return_dict["error"] = "Error logging alert : %s"%e
      iv_logging.info("Error logging alert %s"%str(e))
    else:
      return django.http.HttpResponse("Raised alert")

    return django.shortcuts.render_to_response(template, return_dict, context_instance=django.template.context.RequestContext(request))

    

def configure_ntp_settings(request):

  return_dict = {}
  if request.method=="GET":
    ntp_servers = ntp.get_ntp_servers()
    if not ntp_servers:
      form = common_forms.ConfigureNTPForm()
    else:
      form = common_forms.ConfigureNTPForm(initial={'server_list': ','.join(ntp_servers)})
    url = "edit_ntp_settings.html"
  else:
    form = common_forms.ConfigureNTPForm(request.POST)
    if form.is_valid():
      iv_logging.debug("Got valid request to change NTP settings")
      cd = form.cleaned_data
      si = system_info.load_system_config()
      server_list = cd["server_list"]
      if ',' in server_list:
        slist = server_list.split(',')
      else:
        slist = server_list.split(' ')
      try:
        primary_server = "fractalio-primary"
        secondary_server = "fractalio-secondary"
        #First create the ntp.conf file for the primary and secondary nodes
        temp = tempfile.NamedTemporaryFile(mode="w", dir="/srv/salt/tmp")
        temp.write("driftfile /var/lib/ntp/drift\n")
        temp.write("restrict default kod nomodify notrap nopeer noquery\n")
        temp.write("restrict -6 default kod nomodify notrap nopeer noquery\n")
        temp.write("includefile /etc/ntp/crypto/pw\n")
        temp.write("keys /etc/ntp/keys\n")
        temp.write("\n")
        for server in slist:
          temp.write("server %s iburst\n"%server)
        temp.flush()
        client = salt.client.LocalClient()
        client.cmd('role:master', 'cp.get_file', ["salt://tmp/%s"%os.path.basename(temp.name), '%s/ntp.conf'%settings.NTP_CONF_PATH])
        client.cmd('role:master', 'service.restart', ["ntpd"])
        #shutil.copyfile(temp.name, '%s/ntp.conf'%settings.NTP_CONF_PATH)
        temp.close()
        temp = tempfile.NamedTemporaryFile(mode="w")
        temp.write("server %s iburst\n"%primary_server)
        temp.write("server %s iburst\n"%secondary_server)
        for s in si.keys():
          temp.write("peer %s iburst\n"%s)
        temp.write("server 127.127.1.0\n")
        temp.write("fudge 127.127.1.0 stratum 10\n")
        temp.flush()
        client.cmd('role:secondary', 'cp.get_file', ["salt://tmp/%s"%os.path.basename(temp.name), '%s/ntp.conf'%settings.NTP_CONF_PATH])
        client.cmd('role:secondary', 'service.restart', ["ntpd"])
        #shutil.copyfile(temp.name, '/tmp/ntp.conf')

        '''
        lines = ntp.get_non_server_lines()
        if lines:
          for line in lines:
            temp.write("%s\n"%line)
        '''
        #ntp.restart_ntp_service()
      except Exception, e:
        return_dict["error"] = "Error updating NTP information : %s"%e
        return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance = django.template.context.RequestContext(request))
      else:
        return django.http.HttpResponseRedirect("/show/ntp_settings?saved=1")
    else:
      #invalid form
      iv_logging.debug("Got invalid request to change NTP settings")
      url = "edit_ntp_settings.html"
  return_dict["form"] = form
  return django.shortcuts.render_to_response(url, return_dict, context_instance = django.template.context.RequestContext(request))
      
def flag_node(request):

  return_dict = {}
  if "node" not in request.GET:
    return_dict["error"] = "Error flagging node. No node specified"
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance = django.template.context.RequestContext(request))

  node_name = request.GET["node"]
  str = "/opt/fractal/bin/client %s ipmitool chassis identify 255"%node_name
  iv_logging.debug("Flagging node %s using %s"%(node_name,str))
  r, rc = command.execute_with_rc("/opt/fractal/bin/client %s ipmitool chassis identify 255"%node_name)
  err = ""
  if rc == 0:
    l = command.get_output_list(r)
    if l:
      for ln in l:
        if ln.find("Success"):
          return django.shortcuts.render_to_response("node_flagged.html", return_dict, context_instance = django.template.context.RequestContext(request))
        err += ln
        err += "."
  else:
    err = "Error contacting node. Node down?"

  return_dict["error"] = err
  return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance = django.template.context.RequestContext(request))
    

def reset_to_factory_defaults(request):
  return_dict = {}
  if request.method == "GET":
    #Send a confirmation screen
    return django.shortcuts.render_to_response('reset_factory_defaults_conf.html', return_dict, context_instance = django.template.context.RequestContext(request))
  else:
    iv_logging.info("Got a request to reset to factory defaults")
    #Post request so from conf screen

    #Reset the ntp config file
    try :
      shutil.copyfile("%s/factory_defaults/ntp.conf"%settings.BASE_CONF_PATH, '%s/ntp.conf'%settings.NTP_CONF_PATH)
      pass
    except Exception, e:
      return_dict["error"] = "Error reseting NTP configuration : %s"%e
      return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))

    #Remove email settings
    try:
      mail.delete_email_settings()
    except Exception, e:
      #print str(e)
      return_dict["error"] = "Error reseting mail configuration : %s."%e
      return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))

    try:
      audit.rotate_audit_trail()
    except Exception, e:
      #print str(e)
      return_dict["error"] = "Error rotating the audit trail : %s."%e
      return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))

    #Remove all shares 
    try:
      samba_settings.delete_all_shares()
    except Exception, e:
      #print str(e)
      return_dict["error"] = "Error deleting shares : %s."%e
      return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))

    try:
      samba_settings.delete_auth_settings()
    except Exception, e:
      return_dict["error"] = "Error deleting CIFS authentication settings : %s."%e
      return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))
    try:
      request.user.set_password("admin");
      request.user.save()
    except Exception, e:
      return_dict["error"] = "Error resetting admin password: %s."%e
      return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))


    #Reset the alerts file
    try :
      shutil.copyfile("%s/factory_defaults/alerts.log"%settings.BASE_CONF_PATH, '%s/alerts.log'%settings.ALERTS_DIR)
    except Exception, e:
      return_dict["error"] = "Error reseting alerts : %s."%e
      return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))

    #Reset all batch jobs
    try :
      l = os.listdir("%s/in_process"%settings.BATCH_COMMANDS_DIR)
      for fname in l:
        os.remove("%s/in_process/%s"%(settings.BATCH_COMMANDS_DIR, fname))
    except Exception, e:
      return_dict["error"] = "Error removing scheduled batch jobs : %s."%e
      return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))

    try:
      iscsi.reset_global_target_conf()
      iscsi.delete_all_targets()
      iscsi.delete_all_initiators()
      iscsi.delete_all_auth_access_groups()
      iscsi.delete_all_auth_access_users()
    except Exception, e:
      return_dict["error"] = "Error resetting ISCSI configuration : %s."%e
      return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))

    try:
      # Create commands to stop and delete volumes. Remove peers from cluster.
      d = gluster_commands.create_factory_defaults_reset_file()
      if not "error" in d:
        audit.audit("factory_defaults_reset_start", "Scheduled reset of the system to factory defaults.",  request.META["REMOTE_ADDR"])
        return django.http.HttpResponseRedirect('/show/batch_start_conf/%s'%d["file_name"])
      else:
        return_dict["error"] = "Error initiating a reset to system factory defaults : %s"%d["error"]
        return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))
    except Exception, e:
      return_dict["error"] = "Error creating factory defaults reset batch file : %s."%e
      return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))

def hardware_scan(request):

  return_dict = {}
  url = 'add_nodes_form.html'
  local = salt.client.LocalClient()
  opts = salt.config.master_config(settings.SALT_MASTER_CONFIG)
  iv_logging.info("Hardware scan initiated")
  wheel = salt.wheel.Wheel(opts)
  keys = wheel.call_func('key.list_all')
  client = salt.client.LocalClient()
  pending_minions = keys['minions_pre']
  if request.method == 'GET':
    # Return a list of new nodes available to be pulled into the grid
    if pending_minions:
      form = common_forms.AddNodesForm(pending_minions_list = pending_minions)
      return_dict["form"] = form
    else:
      return_dict["no_new_nodes"] = True
  else:
    form = common_forms.AddNodesForm(request.POST, pending_minions_list = pending_minions)
    if form.is_valid():
      # User has chosed some nodes to be added so add them.
      cd = form.cleaned_data
      pending_minions = cd["nodes"]
      nodes = {}
      success = []
      failed = []
      if pending_minions:
        for m in pending_minions:
          #print "Accepting %s"%m
          if wheel.call_func('key.accept', match=('%s'%m,)):
            r = client.cmd(m, 'grains.get')
            if r:
              if 'bond0' in r[m] and r[m]['bond0']:
                ip = r[m]['bond0'][0]
            if ip:
              r1 = client.cmd('role:master', 'hosts.set_host', [ip, m])
              if not r1:
                errors = "Error adding the DNS information for %s"%m
            else:
                errors = "Error adding the DNS information for %s. No IP address information found."%m
            audit.audit("hardware_scan_node_added", "Added a new node %s to the grid"%m, request.META["REMOTE_ADDR"])
            success.append(m)
          else:
            failed.append(m)
      nodes["success"] = success
      nodes["failed"] = failed
      url = 'add_nodes_result.html'
      ret, rc = _regenrate_manifest()
      if rc != 0:
        if errors:
          errors += "Error regenerating the new configuration : "
        else:
          errors = "Error regenerating the new configuration : "
        errors += ",".join(command.get_output_list(ret))
        errors += ",".join(command.get_error_list(ret))
        return_dict["errors"] = errors
        
  return django.shortcuts.render_to_response(url, return_dict, context_instance = django.template.context.RequestContext(request))

def _regenerate_manifest():
  cmd_to_execute = "/etc/generate_manifest.py %s"%settings.CONFIG_DIR
  return (command.execute_with_rc(cmd_to_execute))

def internal_audit(request):

  response = django.http.HttpResponse()
  if request.method == "GET":
    response.write("Error!")
  else:
    if not "who" in request.POST or request.POST["who"] != "batch":
      response.write("Unknown requester")
      return response
    if (not "audit_action" in request.POST) or (not "audit_str" in request.POST):
      response.write("Insufficient information!")
    else:
      audit.audit(request.POST["audit_action"], request.POST["audit_str"], "0.0.0.0")
    response.write("Success")
  return response






###  THE CODES BELOW ARE MAINTAINED FOR EITER HISTORICAL PURPOSES OR AS A PART OF BACKUP PROCESS.
###  PLEASE DO CONFIRM BELOW DELETING OR DELETE WHEN PUSHING THE DEVELOP TO MASTER AS A PROCESS OF CODE CLEANUP.

'''
def accept_manifest(request):
  if request.method == "GET":
    return_dict["error"] = "Invalid access. Please use the GUI."
    return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))
  return_dict = {}
  try:
    dir = settings.BATCH_COMMANDS_DIR
  except:
    dir = "."
  manifest = request.POST["manifest"]
  if not os.path.isfile("%s/manifest/%s"%(settings.BASE_FILE_PATH, manifest)):
    return_dict["error"] = "Specified configuration does not exist. Please use the GUI."
    return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))
  try :
    shutil.move("%s/manifest/%s"%(settings.BASE_FILE_PATH, manifest), "%s/master.manifest"%settings.SYSTEM_INFO_DIR)
  except Exception, e:
    return_dict['error'] = 'Error updating to the new configuratio : %s'%e
    return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))

  return django.shortcuts.render_to_response('accept_manifest_conf.html', return_dict, context_instance=django.template.context.RequestContext(request))



def del_email_settings(request):

  try:
    mail.delete_email_settings()
    return django.http.HttpResponse("Successfully cleared email settings.")
  except Exception, e:
    iv_logging.debug("Error clearing email settings %s"%e)
    return django.http.HttpResponse("Problem clearing email settings %s"%str(e))

def require_login(view):

  def new_view(request, *args, **kwargs):
    if request.user.is_authenticated():
      return view(request, *args, **kwargs)
    else:
      return django.http.HttpResponseRedirect('/login')

  return new_view

def require_admin_login(view):

  def new_view(request, *args, **kwargs):
    if request.user.is_authenticated() and request.user.username == 'dlcadmin':
      return view(request, *args, **kwargs)
    else:
      return django.http.HttpResponseRedirect('/login')

  return new_view
'''
