import json, time, os, shutil, tempfile, os.path, re, subprocess, sys, shutil, socket, zipfile

import salt.client, salt.wheel

import django.template, django
from django.conf import settings
from django.contrib.auth.decorators import login_required

import integralstor_common
from integralstor_common import db, common, audit, alerts, ntp, mail
from integralstor_common import cifs as cifs_common

import integralstor_gridcell
from integralstor_gridcell import batch, gluster_commands, volume_info, system_info, grid_ops, xml_parse, iscsi, ctdb, iscsi_stgt


import integral_view
from integral_view.forms import common_forms
from integral_view.utils import iv_logging

from glusterfs import gfapi


@login_required
def show(request, page, info = None):

  return_dict = {}
  try:

    assert request.method == 'GET'

    vil, err  = volume_info.get_volume_info_all()
    if err:
      raise Exception(err)
    si, err = system_info.load_system_config()
    if err:
      raise Exception(err)
    if not si:
      raise Exception('Could not obtain system information')

    #assert False
    return_dict['system_info'] = si
    return_dict['volume_info_list'] = vil

    #By default show error page

    if page == "dir_contents":
      dir_name = None
      error = False
      path_base = None
      vol_name = ""
      dir_list = []
      try:
        if ("vol_name" in request.GET) and ("dir" in request.GET):
          vol_name = request.GET.get("vol_name")
          dir_name = request.GET.get("dir")
          first = request.GET.get("first")
          #print first
        else:
          raise Exception ("No volume or Directory Specified")
        if first:
            dirs, err  = gluster_commands.get_gluster_dir_list(vol_name ,"")
        else:
          dirs, err  = gluster_commands.get_gluster_dir_list(vol_name ,dir_name)
        if err:
          raise Exception(err)

        dir_list = json.dumps(dirs)

      except Exception as e:
        return django.http.HttpResponse("Exception Occured : %s"%str(e))
        #iv_logging.debug("Exception while getting dir listing : "%e)
      return django.http.HttpResponse(dir_list,mimetype='application/json')

    elif page == "ntp_settings":

      return_dict['base_template'] = "services_base.html"
      return_dict["page_title"] = 'View NTP settings'
      return_dict['tab'] = 'service_ntp_tab'
      return_dict["error"] = 'Error viewing NTP settings'
      template = "view_ntp_settings.html"
      ntp_servers, err = ntp.get_ntp_servers()
      if err:
        raise Exception(err)
      return_dict["ntp_servers"] = ntp_servers
      if "saved" in request.REQUEST:
        return_dict["saved"] = request.REQUEST["saved"]

    elif page == "integral_view_log_level":

      template = "view_integral_view_log_level.html"
      log_level, err = iv_logging.get_log_level_str()
      if err:
        raise Exception(err)
      return_dict["log_level_str"] = log_level
      if "saved" in request.REQUEST:
        return_dict["saved"] = request.REQUEST["saved"]

    elif page == "email_settings":

      #print "here"
      d, err = mail.load_email_settings()
      if err:
        return_dict['base_template'] = "services_base.html"
        return_dict["page_title"] = 'View Email settings'
        return_dict['tab'] = 'service_config_email_tab'
        return_dict["error"] = 'Error loading Email settings'
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
      if "saved" in request.REQUEST:
        return_dict["saved"] = request.REQUEST["saved"]
      if "not_saved" in request.REQUEST:
        return_dict["not_saved"] = request.REQUEST["not_saved"]
      if "err" in request.REQUEST:
        return_dict["err"] = request.REQUEST["err"]
      template = "view_email_settings.html"

    elif page == "audit_trail":

      al = None
      al, err = audit.get_lines()
      if err:
        return_dict['base_template'] = "system_log_base.html"
        return_dict["page_title"] = 'View audit trail'
        return_dict['tab'] = 'system_log_view_current_audit_tab'
        return_dict["error"] = 'Error loading audit trail'
        raise Exception(err)
      template = "view_audit_trail.html"
      return_dict["audit_list"] = al

    elif page == "batch_start_conf":

      return_dict['base_template'] = "volume_base.html"
      return_dict["page_title"] = 'View batch job'
      return_dict['tab'] = 'volume_background_tab'
      return_dict["error"] = 'Error displaying batch job creation confirmation'

      #Display a confirmation that the batch job has been scheduled. info contains the filename of the batch job
      template = "batch_start_conf.html"
      return_dict["fname"] = info

    elif page == "batch_status":

      return_dict['base_template'] = "volume_base.html"
      return_dict["page_title"] = 'View batch jobs'
      return_dict['tab'] = 'volume_background_tab'
      return_dict["error"] = 'Error loading batch jobs'

      #Load the list of entries from all the files in the start and process directories
      file_list, err = batch.load_all_files()
      if err:
        raise Exception(err)
      return_dict["file_list"] = file_list
      template = "view_batch_process_list.html"

    elif page == "batch_status_details":

      return_dict['base_template'] = "volume_base.html"
      return_dict["page_title"] = 'View batch job status'
      return_dict['tab'] = 'volume_background_tab'
      return_dict["error"] = 'Error loading batch job status'

      d, err = batch.load_specific_file(info)
      if err:
        raise Exception(err)
      if not d:
        raise Exception('Unknown batch job specified')
      else:
        return_dict["process_info"] = d
        template = "view_batch_status_details.html"

    elif page == "volume_info":

      return_dict['base_template'] = "volume_base.html"
      return_dict["page_title"] = 'View volume information'
      return_dict['tab'] = 'volume_configuration_tab'
      return_dict["error"] = 'Error loading volume information'

      vol, err = volume_info.get_volume_info(vil, info)
      if err:
        raise Exception(err)

      if not vol:
        raise Exception("Could not locate information for volume %s"%info)

      template = "view_volume_info.html"
      return_dict["vol"] = vol
      data_locations_list, err = volume_info.get_brick_hostname_list(vol)
      if err:
        raise Exception(err)
      #print data_locations_list
      return_dict["data_locations_list"] = data_locations_list

      ivl, err = iscsi.load_iscsi_volumes_list(vil)
      if err:
        raise Exception(err)
      if ivl and vol["name"] in ivl:
        return_dict["iscsi"] = True

      # To accomodate django template quirks
      #if vol["type"] in ["Replicate", "Distributed-Replicate"]:
      #elif vol["type"] in ["Distribute", "Distributed-Replicate"]:
      if 'replicate' in vol["type"].lower():
        return_dict["replicate"] = True
      if 'distribute' in vol["type"].lower():
        return_dict["distribute"] = True

    elif page == "volume_status":

      return_dict['base_template'] = "volume_base.html"
      return_dict["page_title"] = 'View volume status'
      return_dict['tab'] = 'volume_configuration_tab'
      return_dict["error"] = 'Error loading volume status'

      vol, err = volume_info.get_volume_info(vil, info)
      if err:
        raise Exception(err)

      if not vol:
        raise Exception("Could not locate information for volume %s"%info)

      template = "view_volume_status.html"
      return_dict["vol"] = vol

      # To accomodate django template quirks
      if vol["type"] in ["Replicate", "Distributed-Replicate"]:
        return_dict["replicate"] = True
      if vol["type"] in ["Distribute", "Distributed-Replicate"]:
        return_dict["distribute"] = True

    elif page == "node_status":

      return_dict['base_template'] = "gridcell_base.html"
      return_dict["page_title"] = 'View GRIDCell status'
      return_dict['tab'] = 'gridcell_list_tab'
      return_dict["error"] = 'Error loading GRIDCell status'

      template = "view_node_status.html"

      if "from" in request.GET:
        frm = request.GET["from"]
        return_dict['frm'] = frm

      vol_list, err = volume_info.get_volumes_on_node(info, vil)
      if err:
        raise Exception(err)

      return_dict['node'] = si[info]
      if 'disks' in si[info] and si[info]['disks']:
        for sn, disk in si[info]['disks'].items():
          pos = disk['scsi_info'][0]*6+disk['scsi_info'][2]
          #print pos, sn, disk['scsi_info']
          disk['chassis_pos_indicator'] = pos
      return_dict['ctdb'] = si[info]['services']['ctdb'][1]
      return_dict['winbind'] = si[info]['services']['winbind'][1]
      return_dict['gluster'] = si[info]['services']['glusterd'][1]
      return_dict['node_name'] = info
      return_dict['vol_list'] = vol_list

    elif page == "node_info":

      return_dict['base_template'] = "gridcell_base.html"
      return_dict["page_title"] = 'View GRIDCell information'
      return_dict['tab'] = 'gridcell_list_tab'
      return_dict["error"] = 'Error loading GRIDCell information'

      template = "view_node_info.html"
      if "from" in request.GET:
        frm = request.GET["from"]
        return_dict['frm'] = frm

      vol_list, err = volume_info.get_volumes_on_node(info, vil)
      if err:
        raise Exception(err)

      return_dict['node'] = si[info]
      return_dict['vol_list'] = vol_list


    elif page=="manifest":
      #Read a generated manifest file and display the results.
      if "manifest" not in request.GET:
        raise Exception('Invalid request. No manifest file specified')
      manifest = request.GET["manifest"]
      ss_path, err = common.get_system_status_path()
      if err:
        raise Exception(err)
      with open("%s/%s"%(ss_path, manifest), "r") as f:
        nodes = json.load(f)

      return_dict["manifest"] = nodes
      return_dict["manifest_file"] = manifest
      return django.shortcuts.render_to_response('view_manifest.html', return_dict, context_instance=django.template.context.RequestContext(request))


    elif page == "iscsi_auth_access_info":
      return_dict['base_template'] = "shares_and_targets_base.html"
      return_dict["page_title"] = 'View ISCSI authorized access info'
      return_dict['tab'] = 'volume_configuration_tab'
      return_dict["error"] = 'Error loading ISCSI authorized access info'

      if 'id' not in request.GET:
        raise Exception('Invalid request. No auth access id specified')

      id = int(request.GET['id'])
      l, err = iscsi.load_auth_access_users_info(id)
      if err:
        raise Exception(err)

      if not l:
        raise Exception('No auth access information for the id specified')

      istr = "<b>Authorized access group users : </b>"
      for i in l:
        istr += i["user"]
        istr += ", "
      #return django.http.HttpResponse("<b>Authorized access details </b><br>User : %s, Peer user : %s"%(d["user"],d["peer_user"] ))
      return django.http.HttpResponse("%s"%istr)

    elif page == "iscsi_initiator_info":
      return_dict['base_template'] = "shares_and_targets_base.html"
      return_dict["page_title"] = 'View ISCSI initiator info'
      return_dict['tab'] = 'volume_configuration_tab'
      return_dict["error"] = 'Error loading ISCSI initiator info'
      if 'id' not in request.GET:
        raise Exception('Invalid request. No initiator access id specified')

      id = int(request.GET['id'])
      d, err = iscsi.load_initiator_info(id)
      if err:
        raise Exception(err)
      if not d:
        raise Exception('No initiator information for the id specified')

      return django.http.HttpResponse("<b>Initiator details</b><br>Initiators : %s, Auth network : %s, Comment : %s"%(d["initiators"],d["auth_network"], d["comment"] ))

    elif page == "system_config":

      template = "view_system_config.html"

    elif page == 'gridcells':

      return_dict['base_template'] = "gridcell_base.html"
      return_dict["page_title"] = 'View GRIDCell information'
      return_dict['tab'] = 'gridcell_list_tab'
      return_dict["error"] = 'Error loading GRIDCell information'

      if 'action' in request.GET:
        if request.REQUEST['action'] == 'added_to_storage_pool':
          return_dict['message'] = 'Successfully added GRIDCell to the storage pool'
      nl, err = system_info.get_available_node_list(si)
      if err:
        raise Exception(err)
      if nl:
        anl = []
        for n in nl:
          anl.append(n['hostname'])
        return_dict['gluster_addable_nodes'] = anl
      rnl = []
      localhost = socket.getfqdn().strip()
      for hostname in si.keys():
        if hostname == localhost:
          continue
        if si[hostname]["in_cluster"] and (not si[hostname]["volume_list"]):
          rnl.append(hostname)
      if rnl:
        if 'gridcell-sec.integralstor.lan' in rnl:
          rnl.remove('gridcell-sec.integralstor.lan')
        if 'gridcell-pri.integralstor.lan' in rnl:
          rnl.remove('gridcell-pri.integralstor.lan')
        return_dict['gluster_removable_nodes'] = rnl
      pending_minions, err = grid_ops.get_pending_minions()
      if err:
        raise Exception(err)
      if pending_minions:
        return_dict['pending_minions'] = pending_minions
      template = 'view_gridcells.html'

    elif page == "system_status":

      return_dict['base_template'] = "gridcell_base.html"
      return_dict["page_title"] = 'View system status'
      return_dict['tab'] = 'gridcell_list_tab'
      return_dict["error"] = 'Error loading system status'
      #Disk Status page and system status page has been integrated.

      #Get the disk status
      disk_status = {}
      disk_new = {}

      if request.GET.get("node_id") is not None:
        disk_status = si[request.GET.get("node_id")]
        return_dict["disk_status"] = {}
        return_dict["disk_status"][request.GET.get("node_id")] = disk_status
        template = "view_disk_status_details.html"

      else:
        """
          Iterate the system information, and get the following data :
            1. The status of every disk
            2. The status of the pool
            3. The name of the pool
            4. Calcualte the background_color
            Format : {'node_id':{'name':'pool_name','background_color':'background_color','disks':{disks_pool}}}

        """
        for key, value in si.iteritems():
          #count the failures in case of Offline or degraded
          disk_failures = 0
          #Default background color
          background_color = "bg-green"
          if not si[key]["in_cluster"]:
            disk_new[key] = {}
            disk_new[key]["disks"] = {}
            disk_new[key]["in_cluster"] = si[key]["in_cluster"]
            for disk_key, disk_value in si[key]["disks"].iteritems():
              #print disk_key, disk_value
              if disk_value["rotational"]:
                disk_new[key]["disks"][disk_key] = disk_value["status"]
              #print disk_value["status"]
              if disk_value["status"] != "PASSED":
                disk_failures += 1
              if disk_failures >= 1:
                background_color = "bg-yellow"
              if disk_failures >= 4:
                background_color == "bg-red"

            if si[key]['node_status_str'] == "Degraded":
              background_color = "bg-yellow"
            #print type(si[key]["pools"][0]["state"])
            if si[key]["pools"][0]["state"] == unicode("ONLINE"):
              background_color == "bg-red"
            disk_new[key]["background_color"] = background_color
            disk_new[key]["name"] = si[key]["pools"][0]["pool_name"]
            sorted_disks = []
            for key1,value1 in sorted(si[key]["disks"].iteritems(), key=lambda (k,v):v["position"]):
              sorted_disks.append(key1)
            disk_new[key]["disk_pos"] = sorted_disks
            #print disk_new
            #disk_new[key]["info"] = pool_status
          else:
            disk_status[key] = {}
            if si[key]["node_status"] != -1:
              disk_status[key]["disks"] = {}
              disk_status[key]["in_cluster"] = si[key]["in_cluster"]
              for disk_key, disk_value in si[key]["disks"].iteritems():
                #print disk_key, disk_value
                if disk_value["rotational"]:
                  disk_status[key]["disks"][disk_key] = disk_value["status"]
                #print disk_value["status"]
                if disk_value["status"] != "PASSED":
                  disk_failures += 1
                if disk_failures >= 1:
                  background_color = "bg-yellow"
                if disk_failures >= 4:
                  background_color == "bg-red"

              if si[key]['node_status_str'] == "Degraded":
                background_color = "bg-yellow"
              #print type(si[key]["pools"][0]["state"])
              if si[key]["pools"][0]["state"] == unicode("ONLINE"):
                background_color == "bg-red"
              disk_status[key]["background_color"] = background_color
              disk_status[key]["name"] = si[key]["pools"][0]["pool_name"]
              sorted_disks = []
              for key1,value1 in sorted(si[key]["disks"].iteritems(), key=lambda (k,v):v["position"]):
                sorted_disks.append(key1)
              disk_status[key]["disk_pos"] = sorted_disks
              #print disk_status
              #disk_status[key]["info"] = pool_status
            else:
              disk_status[key] = {}
              disk_status[key]["background_color"] = "bg-red"
              disk_status[key]["disk_pos"] = {}
              disk_status[key]["name"] = "Unknown"

        template = "view_disk_status.html"
        return_dict["disk_status"] = disk_status
        return_dict["disk_new"] = disk_new


    elif page == "pool_status":

      template = "view_pool_status.html"
      num_free_nodes = 0
      for name, node in si.items():
        if node["node_status"] >= 0  and (not node["in_cluster"]):
          num_free_nodes += 1
      return_dict['num_free_nodes'] = num_free_nodes

    elif page == "dashboard":
      return_dict['base_template'] = "dashboard_base.html"
      return_dict["page_title"] = 'Dashboard'
      return_dict['tab'] = 'dashboard_tab'
      return_dict["error"] = 'Error loading dashboard'
      num_nodes_bad = 0
      num_pools_bad = 0
      num_vols_bad = 0
      total_pool = 0
      total_nodes = len(si)
      total_vols = len(vil)
      nodes = {}
      storage_pool = {}
      bad_nodes = []
      bad_node_pools = []
      bad_volumes = []
      num_bad_ctdb_nodes = 0
      bad_ctdb_nodes = []
      num_quotas_exceeded = 0
      quota_exceeded_vols = []
      num_shares = 0

      for k, v in si.items():
        nodes[k] = v["node_status"]
        if v["node_status"] != 0:
          num_nodes_bad += 1
          bad_nodes.append(k)
        if v["in_cluster"] :
          total_pool += 1
          if v["cluster_status"] != 1:
            num_pools_bad += 1
            bad_node_pools.append(k)
        storage_pool[k] = v["cluster_status_str"]



      for vol in vil:
        if vol["status"] == 1 :
          if vol["data_access_status_code"] != 0 or (not vol["processes_ok"]):
            bad_volumes.append(vol['name'])
            num_vols_bad += 1
        if 'quotas' in vol and vol['quotas']:
          for k,v in vol['quotas'].items():
            if k.lower() in ['soft limit exceeded', 'hard limit exceeded'] and v.lower() == 'yes':
              num_quotas_exceeded += 1
              quota_exceeded_vols.append(vol['name'])
              break

      shares_list, err = cifs_common.load_shares_list()
      if err:
        raise Exception(err)
      if shares_list:
        return_dict['num_shares'] = len(shares_list)

      targets_list, err = iscsi_stgt.get_targets()
      if err:
        raise Exception(err)
      if targets_list:
        return_dict['num_targets'] = len(targets_list)
      else:
        return_dict['num_targets'] = 0

      ctdb_status, err = ctdb.get_status()
      print ctdb_status, err
      if err:
        raise Exception(err)
      if ctdb_status:
        num_ctdb_nodes = len(ctdb_status)
        for n, v in ctdb_status.items():
          if v.lower() != 'ok':
            bad_ctdb_nodes.append((n,v))
            num_bad_ctdb_nodes += 1

      return_dict["ctdb_status"] = ctdb_status
      return_dict["num_quotas_exceeded"] = num_quotas_exceeded
      return_dict["quota_exceeded_vols"] = quota_exceeded_vols
      return_dict["num_ctdb_nodes"] = num_ctdb_nodes
      return_dict["bad_ctdb_nodes"] = bad_ctdb_nodes
      return_dict["num_bad_ctdb_nodes"] = num_bad_ctdb_nodes
      return_dict["num_nodes_bad"] = num_nodes_bad
      return_dict["bad_nodes"] = bad_nodes
      return_dict["bad_node_pools"] = bad_node_pools
      return_dict["num_pools_bad"] = num_pools_bad
      return_dict["num_vols_bad"] = num_vols_bad
      return_dict["total_nodes"] = total_nodes
      return_dict["total_pool"] = total_pool
      return_dict["total_vols"] = total_vols
      return_dict["nodes"] = nodes
      return_dict["storage_pool"] = storage_pool
      template = "view_dashboard.html"

    elif page == "alerts":

      return_dict['base_template'] = "system_log_base.html"
      return_dict["page_title"] = 'View alerts'
      return_dict['tab'] = 'system_log_alert_tab'
      return_dict["error"] = 'Error loading system alerts'

      template = "view_alerts.html"
      alerts_list, err = alerts.load_alerts()
      if err:
        raise Exception(err)
      return_dict['alerts_list'] = alerts_list

    elif page == "volume_info_all":
      return_dict['base_template'] = "volume_base.html"
      return_dict["page_title"] = 'View volume info'
      return_dict['tab'] = 'volume_configuration_tab'
      return_dict["error"] = 'Error loading volume info'

      template = "view_volume_info_all.html"
      return_dict['volume_info_list'] = vil
      ivl, err = iscsi.load_iscsi_volumes_list(vil)
      if err:
        raise Exception(err)
      return_dict['iscsi_volumes'] = ivl

    elif page == "volume_status_all":

      return_dict['base_template'] = "volume_base.html"
      return_dict["page_title"] = 'View volume status'
      return_dict['tab'] = 'volume_configuration_tab'
      return_dict["error"] = 'Error loading volume status'

      template = "view_volume_status_all.html"
      return_dict['volume_info_list'] = vil

    return django.shortcuts.render_to_response(template, return_dict, context_instance=django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


def admin_login_required(view):

  def new_view(request, *args, **kwargs):
    if request.user.is_superuser:
      return view(request, *args, **kwargs)
    else:
      return django.http.HttpResponseRedirect('/login')

  return new_view

def refresh_alerts(request, random=None):
  ret = None
  return_dict = {}
  try:
    from datetime import datetime
    cmd_list = []
    #this command will insert or update the row value if the row with the user exists.
    cmd = ["INSERT OR REPLACE INTO admin_alerts (user, last_refresh_time) values (?,?);", (request.user.username, datetime.now())]
    cmd_list.append(cmd)
    db_path, err = common.get_db_path()
    if err:
      raise Exception(err)
    test, err = db.execute_iud("%s"%db_path, cmd_list)
    if err:
      raise Exception(err)
    ret, err = alerts.new_alerts()
    if err:
      raise Exception(err)
    if ret:
      alerts_list, err = alerts.load_alerts()
      if err:
        raise Exception(err)
      new_alerts = json.dumps([dict(alert=pn) for pn in alerts_list])
      return  django.http.HttpResponse(new_alerts, mimetype='application/json')
    else:
      clss = "btn btn-default btn-sm"
      message = "View alerts"
      return  django.http.HttpResponse("No New Alerts")
  except Exception, e:
    return_dict["error_details"] = "An error occurred when processing your request : %s"%str(e)
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

@login_required
def raise_alert(request):

  try:
    return_dict = {}
    if "msg" not in request.REQUEST:
      raise Exception('No alert message specified.')
    msg = request.REQUEST["msg"]
    ret, err = alerts.raise_alert(msg)
    if err:
      raise Exception(err)
    return django.http.HttpResponse("Raised alert")

  except Exception, e:
    return_dict["error"] = "An error occurred when processing your request : %s"%str(e)
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


@login_required
def configure_ntp_settings(request):

  return_dict = {}
  try:
    return_dict['base_template'] = "services_base.html"
    return_dict["page_title"] = 'Configure NTP settings'
    return_dict['tab'] = 'service_ntp_tab'
    return_dict["error"] = 'Error configuring NTP settings'

    admin_vol_mountpoint, err = common.get_config_dir()
    if err:
      raise Exception(err)
    if err:
      raise Exception(err)
    if request.method=="GET":
      ntp_servers, err = ntp.get_ntp_servers()
      if err:
        raise Exception(err)
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
        si, err = system_info.load_system_config()
        if err:
          raise Exception(err)
        if not si:
          raise Exception('Error loading system configuration. System config missing?')
        server_list = cd["server_list"]
        if ',' in server_list:
          slist = server_list.split(',')
        else:
          slist = server_list.split(' ')
        primary_server = "gridcell-pri.integralstor.lan"
        secondary_server = "gridcell-sec.integralstor.lan"
        #First create the ntp.conf file for the primary and secondary nodes
        temp = tempfile.NamedTemporaryFile(mode="w")
        temp.write("driftfile /var/lib/ntp/drift\n")
        temp.write("restrict default kod nomodify notrap nopeer noquery\n")
        temp.write("restrict -6 default kod nomodify notrap nopeer noquery\n")
        temp.write("includefile /etc/ntp/crypto/pw\n")
        temp.write("keys /etc/ntp/keys\n")
        temp.write("\n")
        for server in slist:
          temp.write("server %s iburst\n"%server)
        temp.flush()
        shutil.move(temp.name, "%s/ntp/primary_ntp.conf"%admin_vol_mountpoint)
        temp1 = tempfile.NamedTemporaryFile(mode="w")
        temp1.write("server %s iburst\n"%primary_server)
        temp1.write("server %s iburst\n"%secondary_server)
        for s in si.keys():
          temp1.write("peer %s iburst\n"%s)
        temp1.write("server 127.127.1.0\n")
        temp1.write("fudge 127.127.1.0 stratum 10\n")
        temp1.flush()
        shutil.move(temp1.name, "%s/ntp/secondary_ntp.conf"%admin_vol_mountpoint)
        return django.http.HttpResponseRedirect("/show/ntp_settings?saved=1")
      else:
        #invalid form
        iv_logging.debug("Got invalid request to change NTP settings")
        url = "edit_ntp_settings.html"
    return_dict["form"] = form
    return django.shortcuts.render_to_response(url, return_dict, context_instance = django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))



@login_required
#@django.views.decorators.csrf.csrf_exempt
def flag_node(request):

  try:
    return_dict = {}
    return_dict['base_template'] = "gridcell_base.html"
    return_dict["page_title"] = 'Activate GRIDCell identification light'
    return_dict['tab'] = 'gridcell_list_tab'
    return_dict["error"] = 'Error activating GRIDCell identification light'

    if "node" not in request.GET:
      raise Exception("Error flagging node. No node specified")

    node_name = request.GET["node"]

    client = salt.client.LocalClient()
    blink_time = 255
    ret = client.cmd(node_name,'cmd.run',['ipmitool chassis identify %s' %(blink_time)])
    #print ret
    if ret and ret[node_name] == 'Chassis identify interval: %s seconds'%(blink_time):
      return django.shortcuts.render_to_response("node_flagged.html", return_dict, context_instance = django.template.context.RequestContext(request))
    else:
      raise Exception('Error flagging GRIDCell %s'%node_name)
  except Exception, e:
    s = str(e)
    return_dict["error_details"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


@admin_login_required
def reset_to_factory_defaults(request):
  return_dict = {}
  try:
    defaults_path, err = common.get_factory_defaults_path()
    if err:
      raise Exception(err)
    ntp_conf_path, err = common.get_ntp_conf_path()
    if err:
      raise Exception(err)
    alerts_path, err = common.get_alerts_path()
    if err:
      raise Exception(err)
    batch_files_path, err = common.get_batch_files_path()
    if err:
      raise Exception(err)
    if request.method == "GET":
      #Send a confirmation screen
      return django.shortcuts.render_to_response('reset_factory_defaults_conf.html', return_dict, context_instance = django.template.context.RequestContext(request))
    else:
      iv_logging.info("Got a request to reset to factory defaults")
      #Post request so from conf screen

      #Reset the ntp config file
      try :
        shutil.copyfile("%s/factory_defaults/ntp.conf"%defaults_path, '%s/ntp.conf'%ntp_conf_path)
      except Exception, e:
        raise Exception("Error reseting NTP configuration : %s"%e)

      #Remove email settings
      ret, err = mail.delete_email_settings()
      if err:
        raise Exception(err)

      ret, err = audit.rotate_audit_trail()
      if err:
        raise Exception(err)

      #Remove all shares
      try:
        cifs_common.delete_all_shares()
      except Exception, e:
        #print str(e)
        raise Exception("Error deleting shares : %s."%e)

      try:
        cifs_common.delete_auth_settings()
      except Exception, e:
        raise Exception("Error deleting CIFS authentication settings : %s."%e)
      try:
        request.user.set_password("admin");
        request.user.save()
      except Exception, e:
        raise Exception("Error resetting admin password: %s."%e)


      #Reset the alerts file
      try :
        shutil.copyfile("%s/factory_defaults/alerts.log"%defaults_path, '%s/alerts.log'%alerts_path)
      except Exception, e:
        raise Exception("Error reseting alerts : %s."%e)

      #Reset all batch jobs
      try :
        l = os.listdir("%s"%batch_files_path)
        for fname in l:
          os.remove("%s/%s"%(batch_files_path, fname))
      except Exception, e:
        raise Exception("Error removing scheduled batch jobs : %s."%e)

      try:
        iscsi.reset_global_target_conf()
        iscsi.delete_all_targets()
        iscsi.delete_all_initiators()
        iscsi.delete_all_auth_access_groups()
        iscsi.delete_all_auth_access_users()
      except Exception, e:
        raise Exception("Error resetting ISCSI configuration : %s."%e)

      try:
        # Create commands to stop and delete volumes. Remove peers from cluster.
        vil, err = volume_info.get_volume_info_all()
        if err:
          raise Exception(err)
        scl, err = system_info.load_system_config()
        if err:
          raise Exception(err)
        d, err = gluster_commands.create_factory_defaults_reset_file(scl, vil)
        if err:
          raise Exception(err)
        if not "error" in d:
          ret, err = audit.audit("factory_defaults_reset_start", "Scheduled reset of the system to factory defaults.",  request.META["REMOTE_ADDR"])
          if err:
            raise Exception(err)
          return django.http.HttpResponseRedirect('/show/batch_start_conf/%s'%d["file_name"])
        else:
          return_dict["error"] = "Error initiating a reset to system factory defaults : %s"%d["error"]
          return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))
      except Exception, e:
        raise Exception("Error creating factory defaults reset batch file : %s."%e)
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


@login_required
def hardware_scan(request):

  return_dict = {}
  try:
    return_dict['base_template'] = "gridcell_base.html"
    return_dict["page_title"] = 'Scan for new GRIDCells'
    return_dict['tab'] = 'gridcell_list_tab'
    return_dict["error"] = 'Error scanning for new GRIDCells'
    url = 'add_nodes_form.html'
    iv_logging.info("Hardware scan initiated")

    pending_minions, err = grid_ops.get_pending_minions()
    if err:
      raise Exception(err)

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
        #print 'form valid'
        # User has chosed some nodes to be added so add them.
        cd = form.cleaned_data
        iv_logging.info("Hardware scan initiated")
        (success, failed), errors = grid_ops.add_nodes_to_grid(request.META["REMOTE_ADDR"],cd["nodes"])
        #print 'done adding'
        #print success, failed, errors
        url = 'add_nodes_result.html'
        return_dict["success"] = success
        return_dict["failed"] = failed
        return_dict["errors"] = errors

    return django.shortcuts.render_to_response(url, return_dict, context_instance = django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

@login_required
def remove_gridcell(request):
  return_dict = {}
  try:
    return_dict['base_template'] = "gridcell_base.html"
    return_dict["page_title"] = 'Remove GRIDCells'
    return_dict['tab'] = 'remove_gridcell_tab'
    return_dict["error"] = 'Error removing GRIDCells'
    if request.method == "GET":
      gridcells = []
      si, err = system_info.load_system_config()
      for name,status in si.items():
        if not ('gridcell-pri.integralstor.lan' in name or 'gridcell-sec.integralstor.lan' in name) and not (si[name]['in_cluster']):
          gridcells.append(name)
      return_dict['gridcells'] = gridcells
      return django.shortcuts.render_to_response("remove_gridcell.html", return_dict, context_instance=django.template.context.RequestContext(request))
    if request.method == "POST":
      gridcell  = request.POST.get('gridcell')
      status,err = grid_ops.delete_salt_key(gridcell)
      time.sleep(30)
      status,err = grid_ops._regenerate_manifest_and_status()
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
  else:
      return django.http.HttpResponseRedirect('/show/gridcells/')



@login_required
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


def download_configuration(request):
  """ Download the complete configuration stored in get_config_dir()"""

  return_dict = {}
  try:
    return_dict['base_template'] = "admin_base.html"
    return_dict["page_title"] = 'Download system configuration'
    return_dict['tab'] = 'download_config_tab'
    return_dict["error"] = 'Error downloading system configuration'

    if request.method == 'POST':

      config_dir, err = common.get_config_dir()
      if err:
        raise Exception(err)
      #Remove trailing '/'
      if config_dir[len(config_dir)-1] == '/':
        config_dir = config_dir[:len(config_dir)-1]

      display_name = 'integralstor_config'
      zf_name = '/tmp/integralstor_config.zip'
      zf = zipfile.ZipFile(zf_name, 'w')
      top_component = config_dir[config_dir.rfind('/')+1:]
      for dirname, subdirs, files in os.walk(config_dir):
        for filename in files:
          #print os.path.join(dirname, filename)
          absname = os.path.abspath(os.path.join(dirname, filename))
          arcname = '%s/%s'%(top_component,absname[len(config_dir) + 1:])
          #print arcname
          zf.write(absname, arcname)
      zf.close()


      response = django.http.HttpResponse()
      response['Content-disposition'] = 'attachment; filename=%s.zip'%(display_name)
      response['Content-type'] = 'application/x-compressed'
      with open(zf_name, 'rb') as f:
        byte = f.read(1)
        while byte:
          response.write(byte)
          byte = f.read(1)
      response.flush()

      return response

    # either a get or an invalid form so send back form
    return django.shortcuts.render_to_response('download_config.html', return_dict, context_instance=django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))




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
    ret, err = mail.delete_email_settings()
    if err:
      raise Exception(err)
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
'''
