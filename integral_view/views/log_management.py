import zipfile, datetime, os

import salt.client

import django, django.template
from  django.contrib import auth

import integralstor_gridcell
from integralstor_gridcell import volume_info, system_info

import integralstor_common
from integralstor_common import common, audit, alerts

import integral_view
from integral_view.forms import volume_management_forms, log_management_forms
from integral_view.utils import iv_logging


def edit_integral_view_log_level(request):

  return_dict = {}
  try:
    if request.method == 'POST':
      iv_logging.debug("Trying to change Integral View Log settings")
      form = log_management_forms.IntegralViewLoggingForm(request.POST)
      if form.is_valid():
        iv_logging.debug("Trying to change Integral View Log settings - form valid")
        cd = form.cleaned_data
        log_level = int(cd['log_level'])
        iv_logging.debug("Trying to change Integral View Log settings - log level is %d"%log_level)
        try:
          iv_logging.set_log_level(log_level)
        except Exception, e:
          return_dict['error'] = 'Error setting log level : %s'%e
          return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))
        iv_logging.debug("Trying to change Integral View Log settings - changed log level")
        return django.http.HttpResponseRedirect("/show/integral_view_log_level?saved=1")
    else:
      init = {}
      init['log_level'] = iv_logging.get_log_level()
      form = log_management_forms.IntegralViewLoggingForm(initial=init)
      return_dict['form'] = form
      return django.shortcuts.render_to_response('edit_integral_view_log_level.html', return_dict, context_instance=django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

def download_vol_log(request):
  """ Used to download the volume log of a particular volume whose name is in the vol_name post parameter"""

  return_dict = {}
  try:
    vil, err = volume_info.get_volume_info_all()
    if err:
      raise Exception(err)
    if not vil:
      raise Exception('No volumes detected')

    l = []
    for v in vil:
      l.append(v["name"])
  
    if request.method == 'POST':
      form = volume_management_forms.VolumeNameForm(request.POST, vol_list = l)
      if form.is_valid():
        cd = form.cleaned_data
        vol_name = cd['vol_name']
        iv_logging.debug("Got volume log download request for %s"%vol_name)
        file_name = None
        production, err = common.is_production()
        if err:
          raise Exception(err)
        if production:
          v, err = volume_info.get_volume_info(vil, vol_name)
          if err:
            raise Exception(err)
          if not v:
            return_dict["error"] = "Could not retrieve volume info"
            return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))
          brick = v["bricks"][0][0]
          if not brick:
            return_dict["error"] = "Could not retrieve volume log location - no brick"
            return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))
          l = brick.split(':')
          if not l:
            return_dict["error"] = "Could not retrieve volume log location - malformed brick 1"
            return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))
          l1 = l[1].split('/')
          if not l1:
            return_dict["error"] = "Could not retrieve volume log location - malformed brick 2"
            return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))
          file_name = '/var/log/glusterfs/bricks/%s-%s-%s.log'%(l1[1], l1[2], vol_name)
        else:
          # this will return the same file that you are viewing now for download.
          # doing this so as to remove the dependency of the absolute path problem.
          # As this is also just for testing, any file that is rendered is just fine.Later the same can be changed as per requirement.
          
          file_name = os.path.join(os.path.join(__file__))        
  
        
        display_name = 'integralstor_gridcell-%s.log'%vol_name
  
        #Formulate the zip file name
        zf_name = '/tmp/integralstor_gridcell_volume_%s_log'%vol_name
        dt = datetime.datetime.now()
        dt_str = dt.strftime("%d%m%Y%H%M%S")
        zf_name = zf_name + dt_str +".zip"
  
        try:
          zf = zipfile.ZipFile(zf_name, 'w')
          zf.write(file_name, arcname = display_name)
          zf.close()
        except Exception as e:
          return_dict["error"] = "Error generating zip file : %s"%str(e)
          return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))
  
        response = django.http.HttpResponse()
        response['Content-disposition'] = 'attachment; filename=integralstor_gridcell_volume_%s_log_%s.zip'%(vol_name, dt_str)
        response['Content-type'] = 'application/x-compressed'
        try:
          with open(zf_name, 'rb') as f:
            byte = f.read(1)
            while byte:
             response.write(byte)
             byte = f.read(1)
          response.flush()
        except Exception as e:
          raise Exception("Error compressing remote log file : %s"%str(e))
        return response
  
    else:
      form = volume_management_forms.VolumeNameForm(vol_list = l)
    # either a get or an invalid form so send back form
    return_dict['form'] = form
    return_dict['base_template'] = 'volume_log_base.html'
    return_dict['op'] = 'download_log'
    return django.shortcuts.render_to_response('download_vol_log_form.html', return_dict, context_instance=django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))



def download_sys_log(request):
  """ Download the system log of the type specified in sys_log_type POST param for the node specified in the hostname POST parameter. 
  This calls the /sys_log via an http request on that node to get the info"""

  return_dict = {}
  try:
    si, err = system_info.load_system_config()
    if err:
      raise Exception(err)
    if not si:
      raise Exception('Could not load system configuration')
    form = log_management_forms.SystemLogsForm(request.POST or None, system_config = si)
  
    if request.method == 'POST':
      if form.is_valid():
        cd = form.cleaned_data
        sys_log_type = cd['sys_log_type']
        hostname = cd["hostname"]
  
        iv_logging.debug("Got sys log download request for type %s hostname %s"%(sys_log_type, hostname))
  
        fn = {'boot':'/var/log/boot.log', 'dmesg':'/var/log/dmesg', 'message':'/var/log/messages', 'smb':'/var/log/smblog.vfs', 'winbind':'/var/log/samba/log.winbindd','ctdb':'/var/log/log.ctdb'}
        dn = {'boot':'boot.log', 'dmesg':'dmesg', 'message':'messages','smb':'samba_logs','winbind':'winbind_logs','ctdb':'ctdb_logs'}
  
        file_name = fn[sys_log_type]
        display_name = dn[sys_log_type]
  
        client = salt.client.LocalClient()
  
        ret = client.cmd('%s'%(hostname),'cp.push',[file_name])
  
        # This has been maintained for reference purposes.
        # dt = datetime.datetime.now()
        # dt_str = dt.strftime("%d%m%Y%H%M%S")
  
        # lfn = "/tmp/%s_%s"%(sys_log_type, dt_str)
        # cmd = "/opt/fractal/bin/client %s get_file %s %s"%(hostname, file_name, lfn)
        # print "command is "+cmd
  
        # try :
        #   ret, rc = command.execute_with_rc(cmd)
        # except Exception, e:
        #   return_dict["error"] = "Error retrieving remote log file : %s"%e
        #   return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))
  
        # if rc != 0 :
        #   return_dict["error"] = "Error retrieving remote log file. Retrieval returned an error code of %d"%rc
        #   return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))
  
        zf_name = '%s.zip'%display_name
  
        try:
          zf = zipfile.ZipFile(zf_name, 'w')
          zf.write("/var/cache/salt/master/minions/%s/files/%s"%(hostname,file_name), arcname = display_name)
          zf.close()
        except Exception as e:
          raise Exception("Error compressing remote log file : %s"%str(e))
  
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
    return_dict['form'] = form
    return django.shortcuts.render_to_response('download_sys_log_form.html', return_dict, context_instance=django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

  
def rotate_log(request, log_type=None):
  return_dict = {}
  try:
    if log_type not in ["alerts", "audit_trail"]:
      raise Exception("Unknown log type")
      return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))
    if log_type == "alerts":
      return_dict['tab'] = 'view_current_alerts_tab'
      return_dict["page_title"] = 'Rotate system alerts log'
      ret, err = alerts.rotate_alerts()
      if err:
        raise Exception(err)
      return_dict["message"] = "Alerts log successfully rotated."
      return django.http.HttpResponseRedirect("/view_rotated_log_list/alerts?success=true")
    elif log_type == "audit_trail":
      return_dict['tab'] = 'view_current_audit_tab'
      return_dict["page_title"] = 'Rotate system audit trail'
      ret, err = audit.rotate_audit_trail()
      if err:
        raise Exception(err)
      return_dict["message"] = "Audit trail successfully rotated."
      return django.http.HttpResponseRedirect("/view_rotated_log_list/audit_trail/?success=true")
  except Exception, e:
    return_dict['base_template'] = "logging_base.html"
    return_dict["error"] = 'Error rotating log'
    return_dict["error_details"] = str(e)
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
  
  
def view_rotated_log_list(request, log_type):

  return_dict = {}
  try:
    if log_type not in ["alerts", "audit_trail"]:
      raise Exception("Unknown log type")
    l = None
    if log_type == "alerts":
      return_dict["page_title"] = 'View rotated alerts logs'
      return_dict['tab'] = 'view_rotated_alert_log_list_tab'
      return_dict["page_header"] = "Logging"
      return_dict["page_sub_header"] = "View historical alerts log"
      l, err = alerts.get_log_file_list()
      if err:
        raise Exception(err)
    elif log_type == "audit_trail":
      return_dict["page_title"] = 'View rotated audit trail logs'
      return_dict['tab'] = 'view_rotated_audit_log_list_tab'
      return_dict["page_header"] = "Logging"
      return_dict["page_sub_header"] = "View historical audit log"
      l, err = audit.get_log_file_list()
      if err:
        raise Exception(err)

    return_dict["type"] = log_type
    return_dict["log_file_list"] = l
    return django.shortcuts.render_to_response('view_rolled_log_list.html', return_dict, context_instance = django.template.context.RequestContext(request))
  except Exception, e:
    return_dict['base_template'] = "logging_base.html"
    return_dict["error"] = 'Error displaying rotated log list'
    return_dict["error_details"] = str(e)
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

def view_rotated_log_file(request, log_type):

  return_dict = {}
  try:
    if not log_type:
      raise Exception('Unspecified log type')

    if log_type not in ["alerts", "audit_trail"]:
      raise Exception('Unrecognized log type')

    if request.method != "POST":
      raise Exception('Unsupported request type')
      
    if "file_name" not in request.POST:
      raise Exception('Filename not specified')
  
    file_name = request.POST["file_name"]
  
    if log_type == "alerts":
      l, err = alerts.load_alerts(file_name)
      if err:
        raise Exception(err)
      return_dict["alerts_list"] = l
      return_dict["historical"] = True
      return django.shortcuts.render_to_response('view_alerts.html', return_dict, context_instance = django.template.context.RequestContext(request))
    else:
      d, err = audit.get_lines(file_name)
      if err:
        raise Exception(err)
      return_dict["audit_list"] = d
      return_dict["historical"] = True
      return django.shortcuts.render_to_response('view_audit_trail.html', return_dict, context_instance = django.template.context.RequestContext(request))
  except Exception, e:
    s = str(e)
    if "Another transaction is in progress".lower() in s.lower():
      return_dict["error"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
    else:
      return_dict["error"] = "An error occurred when processing your request : %s"%s
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

  








'''
def sys_log(request, log_type = None):
  """ Invoked by a node in order to deliver the sys log to the remote node.  Shd not normally be called from a browser """

  if not log_type:
    return None

  fn = {'boot':'/var/log/boot.log', 'dmesg':'/var/log/dmesg', 'message':'/var/log/messages'}
  dn = {'boot':'boot.log', 'dmesg':'dmesg', 'message':'messages'}

  file_name = fn[log_type]
  display_name = dn[log_type]
  zf_name = '/tmp/%s'%log_type

  dt = datetime.datetime.now()
  dt_str = dt.strftime("%d%m%Y%H%M%S")
  zf_name = zf_name + dt_str +".zip"
  try:
    zf = zipfile.ZipFile(zf_name, 'w')
    zf.write(file_name, arcname = display_name)
    zf.close()
  except Exception as e:
    return None

  try:
    response = django.http.HttpResponse()
    response['Content-disposition'] = 'attachment; filename=%s%s.zip'%(log_type, dt_str)
    response['Content-type'] = 'application/x-compressed'
    with open(zf_name, 'rb') as f:
      byte = f.read(1)
      while byte:
        response.write(byte)
        byte = f.read(1)
    response.flush()
  except Exception as e:
    return None

  return response


      url = "http://%s:8000/sys_log/%s"%(hostname, sys_log_type)
      d = download.url_download(url)
      if d["error"]:
        return_dict["error"] = d["error"]
        return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))
      
      fn = {'boot':'/var/log/boot.log', 'dmesg':'/var/log/dmesg', 'message':'/var/log/messages'}
      dn = {'boot':'boot.log', 'dmesg':'dmesg', 'message':'messages'}

      file_name = fn[sys_log_type]
      display_name = dn[sys_log_type]
      zf_name = '/tmp/%s'%sys_log_type

      try:
        response = django.http.HttpResponse()
        response['Content-disposition'] = d["content-disposition"]
        response['Content-type'] = 'application/x-compressed'
        response.write(d["content"])
        response.flush()
      except Exception as e:
        return_dict["error"] = "Error requesting log file: %s"%str(e)
        return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance = django.template.context.RequestContext(request))

      return response
'''
