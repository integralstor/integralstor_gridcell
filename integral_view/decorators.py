
import django
from integralstor_gridcell import grid_ops


def login_and_admin_vol_mountpoint_required(f):

    def decorated_view(request, *args):
        return_dict = {}
        try:
            return_dict['base_template'] = "dashboard_base.html"
            return_dict["page_title"] = 'Dashboard'
            return_dict['tab'] = 'dashboard_tab'
            ret, err = grid_ops.check_admin_volume_mountpoint()
            if err:
                raise Exception(err)
            if not ret:
                raise Exception(
                    'We could not access the admin volume in order to process this request. Please ensure that the admin volume is mounted and try again.')
            if request.user.is_authenticated:
                if args:
                    return f(request, *args)
                else:
                    return f(request)
            else:
                return django.http.HttpResponseRedirect('/login/')
        except Exception, e:
            s = str(e)
            return_dict["error"] = "An error occurred when processing your request : %s" % s
            return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))

    return decorated_view


# vim: tabstop=8 softtabstop=0 expandtab ai shiftwidth=4 smarttab
