import django
from django.conf import settings
import salt.client
from integralstor_gridcell import services, system_info

from integralstor_gridcell.services import default_services
from integralstor_common import db, common, audit, ntp
from integral_view.forms import common_forms

def view_services(request):
  return_dict = {}
  return_dict['service_status'] = {}
  try:
    return_dict['base_template'] = "services_base.html"
    return_dict["page_title"] = 'View services'
    return_dict['tab'] = 'service_status_tab'
    return_dict["error"] = 'Error loading services'

    if "ack" in request.GET:
      if 'service' in request.GET:
        sn = request.GET['service']
      else:
        sn = ''
      if 'gridcell' in request.GET:
        gridcell = request.GET['gridcell']
      else:
        gridcell = ''
      if request.GET["ack"] == "start":
        return_dict['ack_message'] = 'Service "%s" started on GRIDCell %s. The status will reflect on this screen after one minute.'%(sn, gridcell)
      elif request.GET["ack"] == "stop":
        return_dict['ack_message'] = 'Service "%s" stopped on GRIDCell %s. The status will reflect on this screen after one minute.'%(sn, gridcell)
      if request.GET["ack"] == "restart":
        return_dict['ack_message'] = 'Service "%s" restarted on GRIDCell %s. The status will reflect on this screen after one minute.'%(sn, gridcell)

    si, err = system_info.load_system_config()
    if err:
      raise Exception(err)
    if not si:
      raise Exception('Could not obtain system information')
    return_dict['system_info'] = si
    return django.shortcuts.render_to_response("view_services.html", return_dict, context_instance=django.template.context.RequestContext(request))
  except Exception, e:
    return_dict["error_details"] = str(e)
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


def change_service_status_on_gridcell(request):
  return_dict = {}
  try:
    return_dict['base_template'] = "services_base.html"
    return_dict["page_title"] = 'Modify service status'
    return_dict['tab'] = 'service_status_tab'
    return_dict["error"] = 'Error modifying service status'

    service = request.REQUEST.get('service')
    action = request.REQUEST.get('action')
    gridcell = request.REQUEST.get('gridcell')

    status,err = services.service_action(gridcell,service,action)
    if err:
      raise Exception(err)

    return django.http.HttpResponseRedirect('/view_services?ack=%s&service=%s&gridcell=%s'%(action,service,gridcell))
  except Exception, e:
    return_dict["error_details"] = "An error occurred when processing your request : %s"%str(e)
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

def view_ntp_settings(request):
  return_dict = {}
  try:
    return_dict['base_template'] = "services_base.html"
    return_dict["page_title"] = 'View NTP settings'
    return_dict['tab'] = 'service_ntp_tab'
    return_dict["error"] = 'Error viewing NTP settings'

    ntp_servers, err = ntp.get_ntp_servers()
    if err:
      raise Exception(err)
    return_dict["ntp_servers"] = ntp_servers

    if 'ack' in request.REQUEST:
      if request.REQUEST['ack'] == 'saved':
        return_dict["ack_message"] = 'NTP settings have successfully been updated.'

    return django.shortcuts.render_to_response('view_ntp_settings.html', return_dict, context_instance=django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error_details"] = s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

def edit_ntp_settings(request):

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
        #iv_logging.debug("Got valid request to change NTP settings")
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
        return django.http.HttpResponseRedirect("/view_ntp_settings?saved=1")
      else:
        #invalid form
        #iv_logging.debug("Got invalid request to change NTP settings")
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

