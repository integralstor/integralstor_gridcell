"""Views that allow for viewing the status of gluster related batch jobs that require multiple steps to perform.

These include :
  view_batch_processes - Get the info related to all the batch processes.
  view_batch_process - Get the info related to a specific batch process.

"""

import django.template
import django

from integralstor_gridcell import batch


def view_batch_processes(request):
    """ Display the list of all gluster batch processes. This is done by loading all the json batch command files and sending the structures to the template."""
    return_dict = {}
    try:
        return_dict['base_template'] = "batch_base.html"
        return_dict["page_title"] = 'View batch jobs'
        return_dict['tab'] = 'volume_background_tab'
        return_dict["error"] = 'Error loading batch jobs'

        # Load the list of entries from all the files in batch directories
        file_list, err = batch.load_all_files()
        if err:
            raise Exception(err)
        return_dict["file_list"] = file_list
        return django.shortcuts.render_to_response('view_batch_processes.html', return_dict, context_instance=django.template.context.RequestContext(request))
    except Exception, e:
        s = str(e)
        if "Another transaction is in progress".lower() in s.lower():
            return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
        else:
            return_dict["error_details"] = "An error occurred when processing your request : %s" % s
        return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


def view_batch_process(request):
    """ Display the list of all volume batch processes"""
    return_dict = {}
    try:
        return_dict['base_template'] = "volume_base.html"
        return_dict["page_title"] = 'View batch job status'
        return_dict['tab'] = 'volume_background_tab'
        return_dict["error"] = 'Error loading batch job status'

        if 'file_name' not in request.REQUEST:
            raise Exception('Invalud request. Please use the menus.')
        file_name = request.REQUEST['file_name']

        d, err = batch.load_specific_file(file_name)
        if err:
            raise Exception(err)
        if not d:
            raise Exception('Unknown batch job specified')

        return_dict["process_info"] = d
        return django.shortcuts.render_to_response("view_batch_process.html", return_dict, context_instance=django.template.context.RequestContext(request))
    except Exception, e:
        s = str(e)
        if "Another transaction is in progress".lower() in s.lower():
            return_dict["error_details"] = "An underlying storage operation has locked a volume so we are unable to process this request. Please try after a couple of seconds"
        else:
            return_dict["error_details"] = "An error occurred when processing your request : %s" % s
        return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

# vim: tabstop=8 softtabstop=0 expandtab ai shiftwidth=4 smarttab
