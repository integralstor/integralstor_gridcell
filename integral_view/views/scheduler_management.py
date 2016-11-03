import django
from django.conf import settings
from integralstor_gridcell import system_info
from integralstor_common import scheduler_utils,common, lock

def schedule_scrub(request):
  return_dict = {}
  try:
    return_dict['base_template'] = "system_base.html"
    return_dict["page_title"] = 'Schedule filesystem scrub'
    return_dict['tab'] = 'initiate_scrub_tab'
    return_dict["error"] = 'Error scheduling filesystem scrub'
    gluster_lck, err = lock.get_lock('gluster_commands')
    if err:
      raise Exception(err)

    if not gluster_lck:
      raise Exception('This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')
    if "ack" in request.GET:
      if request.GET["ack"] == "success":
        return_dict['ack_message'] = "Filesystem scrub successfully scheduled."
    if request.method == "GET":
      return django.shortcuts.render_to_response("schedule_scrub.html", return_dict, context_instance=django.template.context.RequestContext(request))
    elif request.method == "POST":
      dt = request.POST.get('timestamp')
      poolname = 'frzpool'
      db_path,err = common.get_db_path()
      # Doing this to make sure each node has a zfs scrub scheduled
      si, err = system_info.load_system_config()
      if err:
        raise Exception(err)
      err_list = []
      success = 0
      for node in si.keys():
        status,err = scheduler_utils.schedule_a_job(db_path,'ZFS Scrub on %s'%node,[{'scrub':'/sbin/zpool scrub frzpool'}],node=node,execute_time=int(dt))
        if err:
          err_list.append(err)
        else:
          success += 1
      if err_list:
        if success > 0:
          #Some succeeded
          return django.http.HttpResponseRedirect('/view_scheduled_jobs?ack=scheduled&err=%s'%','.join(err_list))
        else:
          #All failed
          raise Exception(','.join(err_list))
      #All succeeded
      return django.http.HttpResponseRedirect('/view_scheduled_jobs?ack=scheduled')
  except Exception, e:
    return_dict["error"] = 'Unable to retrive the status of services'
    return_dict["error_details"] = "An error occurred when processing your request : %s"%e
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
  finally:
    lock.release_lock('gluster_commands')

def view_scheduled_jobs(request):
  return_dict = {}
  try:
    db_path = settings.DATABASES["default"]["NAME"]
    back_jobs,err = scheduler_utils.get_background_jobs(db_path)
    if err:
      raise Exception(err)
    if "ack" in request.GET:
      if request.GET["ack"] == "deleted":
        return_dict['ack_message'] = "Scheduled job successfully removed."
      elif request.GET["ack"] == "scheduled":
        if 'err' in request.GET:
          return_dict['ack_message'] = "Job successfully scheduled with the following errors : %s."%request.GET['err']
        else:
          return_dict['ack_message'] = "Job successfully scheduled."
    return_dict["back_jobs"] = back_jobs
    return django.shortcuts.render_to_response("view_scheduled_jobs.html", return_dict, context_instance=django.template.context.RequestContext(request))
  except Exception, e:
    return_dict['base_template'] = "batch_base.html"
    return_dict["page_title"] = 'Scheduled jobs'
    return_dict['tab'] = 'scheduled_jobs_tab'
    return_dict["error"] = 'Error retriving scheduled tasks'
    return_dict["error_details"] = str(e)
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

def view_scheduled_job(request, *args):
  return_dict = {}
  db_path = settings.DATABASES["default"]["NAME"]
  try:
    task_id = '-1'
    if args:
      task_id = args[0]
    task_name,err = scheduler_utils.get_background_job(db_path,int(task_id))
    return_dict["task"] = task_name[0]
    commands,err = scheduler_utils.get_task_details(db_path,int(task_id))
    if err:
      return_dict["error"] = "Error loading Backgorund jobs"
      return_dict["error_details"] = err
    return_dict["commands"] = commands 
    return django.shortcuts.render_to_response("view_scheduled_job.html", return_dict, context_instance=django.template.context.RequestContext(request))
  except Exception, e:
    return_dict['base_template'] = "batch_base.html"
    return_dict["page_title"] = 'View scheduled job details'
    return_dict['tab'] = 'scheduled_jobs_tab'
    return_dict["error"] = 'Error retriving scheduled job details'
    return_dict["error_details"] = str(e)
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

def remove_scheduled_job(request):
  return_dict = {}
  try:
    db_path = settings.DATABASES["default"]["NAME"]
    task_id = request.REQUEST.get('task_id')
    status,err = scheduler_utils.delete_task(int(task_id))
    if err:
      raise Exception(err)
    return django.http.HttpResponseRedirect('/view_scheduled_jobs?ack=deleted') 
  except Exception,e:
    return_dict['base_template'] = "batch_base.html"
    return_dict["page_title"] = 'Remove a scheduled job'
    return_dict['tab'] = 'view_background_tasks_tab'
    return_dict["error"] = 'Error removing schedued job'
    return_dict["error_details"] = str(e)
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
