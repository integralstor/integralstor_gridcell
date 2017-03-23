import django
from django.conf import settings
from integralstor_gridcell import system_info
from integralstor_utils import scheduler_utils, config, lock, command
import os


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
            raise Exception(
                'This action cannot be performed as an underlying storage command is being run. Please retry this operation after a few seconds.')
        if "ack" in request.GET:
            if request.GET["ack"] == "success":
                return_dict['ack_message'] = "Filesystem scrub successfully scheduled."
        if request.method == "GET":
            return django.shortcuts.render_to_response("schedule_scrub.html", return_dict, context_instance=django.template.context.RequestContext(request))
        elif request.method == "POST":
            dt = request.POST.get('timestamp')
            poolname = 'frzpool'
            db_path, err = config.get_db_path()
            # Doing this to make sure each node has a zfs scrub scheduled
            si, err = system_info.load_system_config()
            if err:
                raise Exception(err)
            err_list = []
            success = 0
            for node in si.keys():
                status, err = scheduler_utils.add_task('ZFS Scrub on %s' % node, [
                                                       {'scrub': '/sbin/zpool scrub frzpool'}], task_type_id=3, node=node, initiate_time=int(dt))
                if err:
                    err_list.append(err)
                else:
                    success += 1
            if err_list:
                if success > 0:
                    # Some succeeded
                    return django.http.HttpResponseRedirect('/view_tasks?ack=scheduled&err=%s' % ','.join(err_list))
                else:
                    # All failed
                    raise Exception(','.join(err_list))
            # All succeeded
            return django.http.HttpResponseRedirect('/view_tasks?ack=scheduled')
    except Exception, e:
        return_dict["error"] = 'Unable to retrive the status of services'
        return_dict["error_details"] = "An error occurred when processing your request : %s" % e
        return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
    finally:
        lock.release_lock('gluster_commands')


def view_tasks(request):
    return_dict = {}
    try:
        tasks, err = scheduler_utils.get_tasks()
        if err:
            raise Exception(err)
        if "ack" in request.GET:
            if request.GET["ack"] == "deleted":
                return_dict['ack_message'] = "Task successfully removed."
            elif request.GET["ack"] == "scheduled":
                if 'err' in request.GET:
                    return_dict['ack_message'] = "Task successfully scheduled with the following errors : %s." % request.GET['err']
                else:
                    return_dict['ack_message'] = "Job successfully scheduled."
        return_dict["tasks"] = tasks
        return django.shortcuts.render_to_response("view_tasks.html", return_dict, context_instance=django.template.context.RequestContext(request))
    except Exception, e:
        return_dict['base_template'] = "batch_base.html"
        return_dict["page_title"] = 'Background tasks'
        return_dict['tab'] = 'scheduled_jobs_tab'
        return_dict["error"] = 'Error retrieving background tasks'
        return_dict["error_details"] = str(e)
        return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


def view_task(request, *args):
    return_dict = {}
    try:
        task_id = '-1'
        if args:
            task_id = args[0]
        task, err = scheduler_utils.get_task(int(task_id))
        return_dict["task"] = task
        subtasks, err = scheduler_utils.get_subtasks(int(task_id))
        if err:
            raise Exception(err)
        return_dict["subtasks"] = subtasks
        task_output = ""
        log_path, err = config.get_log_folder_path()
        if err:
            raise Exception(err)
        log_dir = '%s/task_logs' % log_path
        log_file_path = '%s/%d.log' % (log_dir, int(task_id))
        if os.path.isfile(log_file_path):
            lines, err = command.get_command_output("wc -l %s" % log_file_path)
            no_of_lines = lines[0].split()[0]
            # print no_of_lines
            if int(no_of_lines) <= 41:
                # This code always updates the 0th element of the command list.
                # This is assuming that we will only have one long running
                # command.
                with open(log_file_path) as output:
                    task_output = task_output + ''.join(output.readlines())
            else:
                first, err = command.get_command_output(
                    "head -n 5 %s" % log_file_path, shell=True)
                if err:
                    print err
                last, err = command.get_command_output(
                    "tail -n 20 %s" % log_file_path, shell=True)
                if err:
                    print err
                # print last
                task_output = task_output + '\n'.join(first)
                task_output = task_output + "\n.... \n ....\n"
                task_output = task_output + '\n'.join(last)
        return_dict['task_output'] = task_output
        return django.shortcuts.render_to_response("view_task.html", return_dict, context_instance=django.template.context.RequestContext(request))
    except Exception, e:
        return_dict['base_template'] = "batch_base.html"
        return_dict["page_title"] = 'View scheduled job details'
        return_dict['tab'] = 'scheduled_jobs_tab'
        return_dict["error"] = 'Error retrieving scheduled job details'
        return_dict["error_details"] = str(e)
        return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


def remove_task(request):
    return_dict = {}
    try:
        task_id = request.REQUEST.get('task_id')
        status, err = scheduler_utils.remove_task(int(task_id))
        if err:
            raise Exception(err)
        return django.http.HttpResponseRedirect('/view_tasks?ack=deleted')
    except Exception, e:
        return_dict['base_template'] = "batch_base.html"
        return_dict["page_title"] = 'Remove a task'
        return_dict['tab'] = 'view_background_tasks_tab'
        return_dict["error"] = 'Error removing task'
        return_dict["error_details"] = str(e)
        return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

# vim: tabstop=8 softtabstop=0 expandtab ai shiftwidth=4 smarttab
