from django.conf.urls import patterns, include, url
from integral_view.views.iscsi import iscsi_display_global_config, iscsi_display_initiators, iscsi_display_targets, iscsi_view_initiator, iscsi_edit_initiator, iscsi_create_initiator, iscsi_delete_initiator, iscsi_display_auth_access_group_list, iscsi_create_auth_access_group, iscsi_view_auth_access_group, iscsi_delete_auth_access_group, iscsi_edit_auth_access_user, iscsi_edit_target_global_config, iscsi_view_target_global_config, iscsi_create_target,iscsi_view_target , iscsi_edit_target, iscsi_delete_target, iscsi_delete_auth_access_user, iscsi_create_auth_access_user
from integral_view.views.admin_auth  import login, logout, change_admin_password, configure_email_settings 
from integral_view.views.trusted_pool_setup  import add_nodes, remove_node
from integral_view.views.volume_creation import volume_creation_wizard, create_volume, create_volume_conf
from integral_view.views.volume_management import volume_specific_op , expand_volume, replace_node, set_volume_options, set_volume_quota, delete_volume, replace_disk, deactivate_snapshot, activate_snapshot
from integral_view.views import perform_op
from integral_view.views.common import require_login, show, refresh_alerts, raise_alert, internal_audit, configure_ntp_settings, del_email_settings, reset_to_factory_defaults, flag_node, hardware_scan, accept_manifest
from integral_view.views.log_management import download_vol_log, download_sys_log, rotate_log, view_rotated_log_list, view_rotated_log_file, edit_integral_view_log_level
#from integral_view.views.node_management import pull_node_status, node_status
#from integral_view.views.share_management import samba_server_settings_basic, save_samba_server_settings_basic, samba_server_settings_security, save_samba_server_settings_security, display_shares, create_share, view_samba_share, edit_samba_share, display_users, edit_samba_user, create_user, create_unix_user, samba_server_settings, save_samba_server_settings, samba_server_settings, view_share, edit_share
from integral_view.views.share_management import display_shares, create_share, samba_server_settings, save_samba_server_settings, view_share, edit_share, delete_share, edit_auth_method, view_local_users, create_local_user, change_local_user_password, delete_local_user

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'integral_view.views.home', name='home'),
    # url(r'^integral_view/', include('integral_view.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^login/', login),
    url(r'^$', login),
    url(r'^raise_alert/', raise_alert),
    url(r'^flag_node/', flag_node),
    url(r'^del_email_settings/', require_login(del_email_settings)),
    url(r'^internal_audit/', internal_audit),
    url(r'^change_admin_password/', require_login(change_admin_password)),
    url(r'^deactivate_snapshot/', require_login(deactivate_snapshot)),
    url(r'^activate_snapshot/', require_login(activate_snapshot)),
    url(r'^hardware_scan/', require_login(hardware_scan)),
    url(r'^accept_manifest/', require_login(accept_manifest)),
    url(r'^configure_email_settings/', require_login(configure_email_settings)),
    url(r'^reset_to_factory_defaults/', require_login(reset_to_factory_defaults)),
    url(r'^configure_ntp_settings/', require_login(configure_ntp_settings)),
    url(r'^iscsi_display_targets/', require_login(iscsi_display_targets)),
    url(r'^iscsi_view_target/', require_login(iscsi_view_target)),
    url(r'^iscsi_create_target/', require_login(iscsi_create_target)),
    url(r'^iscsi_edit_target/', require_login(iscsi_edit_target)),
    url(r'^iscsi_delete_target/', require_login(iscsi_delete_target)),
    url(r'^iscsi_display_initiators/', require_login(iscsi_display_initiators)),
    url(r'^iscsi_view_initiator/', require_login(iscsi_view_initiator)),
    url(r'^iscsi_create_initiator/', require_login(iscsi_create_initiator)),
    url(r'^iscsi_delete_initiator/', require_login(iscsi_delete_initiator)),
    url(r'^iscsi_edit_initiator/', require_login(iscsi_edit_initiator)),
    url(r'^iscsi_display_auth_access_group_list/', require_login(iscsi_display_auth_access_group_list)),
    url(r'^iscsi_create_auth_access_group/', require_login(iscsi_create_auth_access_group)),
    url(r'^iscsi_create_auth_access_user/', require_login(iscsi_create_auth_access_user)),
    url(r'^iscsi_view_auth_access_group/', require_login(iscsi_view_auth_access_group)),
    url(r'^iscsi_delete_auth_access_group/', require_login(iscsi_delete_auth_access_group)),
    url(r'^iscsi_delete_auth_access_user/', require_login(iscsi_delete_auth_access_user)),
    url(r'^iscsi_edit_auth_access_user/', require_login(iscsi_edit_auth_access_user)),
    url(r'^iscsi_edit_target_global_config/', require_login(iscsi_edit_target_global_config)),
    url(r'^iscsi_view_target_global_config/', require_login(iscsi_view_target_global_config)),
    url(r'^display_shares/', require_login(display_shares)),
    url(r'^view_local_users/', require_login(view_local_users)),
    url(r'^create_local_user/', require_login(create_local_user)),
    url(r'^delete_local_user/', require_login(delete_local_user)),
    url(r'^change_local_user_password/', require_login(change_local_user_password)),
    url(r'^create_share/', require_login(create_share)),
    url(r'^view_share/', require_login(view_share)),
    url(r'^edit_share/', require_login(edit_share)),
    url(r'^edit_auth_method/', require_login(edit_auth_method)),
    url(r'^delete_share/', require_login(delete_share)),
    url(r'^auth_server_settings/', require_login(samba_server_settings)),
    url(r'^save_samba_server_settings/', require_login(save_samba_server_settings)),
    url(r'^replace_node/', require_login(replace_node)),
    url(r'^replace_disk/', require_login(replace_disk)),
    url(r'^edit_integral_view_log_level/', require_login(edit_integral_view_log_level)),
    url(r'^set_volume_options/', require_login(set_volume_options)),
    url(r'^set_volume_quota/', require_login(set_volume_quota)),
    url(r'^remove_node/', require_login(remove_node)),
    url(r'^show/([A-Za-z0-9_]+)/([a-zA-Z0-9_\-\.]*)', require_login(show)),
    url(r'^refresh_alerts/([0-9_]*)', require_login(refresh_alerts)),
    url(r'^logout/', logout),
    url(r'^perform_op/([A-Za-z_]+)/([A-Za-z0-9_\-]*)/([A-Za-z0-9_\.\-\:\/]*)', require_login(perform_op.perform_op)),
    #url(r'^server_op/([A-Za-z_]+)', require_login(server_op)),
    url(r'^add_nodes/', require_login(add_nodes)),
    url(r'^volume_creation_wizard/([A-Za-z_]+)', require_login(volume_creation_wizard)),
    url(r'^create_volume/', require_login(create_volume)),
    url(r'^delete_volume/', require_login(delete_volume)),
    url(r'^create_volume_conf/', require_login(create_volume_conf)),
    url(r'^volume_specific_op/([A-Za-z_]+)/([A-Za-z0-9_\-]*)', require_login(volume_specific_op)),
    url(r'^expand_volume/', require_login(expand_volume)),
    url(r'^download_vol_log/', require_login(download_vol_log)),
    url(r'^download_sys_log/', require_login(download_sys_log)),
    url(r'^rotate_log/([A-Za-z_]+)', require_login(rotate_log)),
    url(r'^view_rotated_log_list/([A-Za-z_]+)', require_login(view_rotated_log_list)),
    url(r'^view_rotated_log_file/([A-Za-z_]+)', require_login(view_rotated_log_file)),
    #url(r'^sys_log/([A-Za-z]+)', sys_log),
    #url(r'^pull_node_status/([A-Za-z_\-0-9]+)', require_login(pull_node_status)),
    #url(r'^node_status/', node_status),
    ## url(r'^view_log/([A-Za-z_]*)/([0-9]*)/([0-9]*)', require_login(view_log)),
    ## url(r'^view_log/([A-Za-z_]*)', require_login(view_log)),
    #url(r'^download_vol_log/([A-Za-z0-9_\-\:\/]*)', require_login(download_vol_log)),
    #url(r'^display_users/', require_login(display_users)),
    #url(r'^create_user/', require_login(create_user)),
    #url(r'^create_unix_user/', require_login(create_unix_user)),
    #url(r'^perform_op/([A-Za-z_]+)/([A-Za-z0-9_\-]*)', require_login(perform_op.perform_op)),
    #url(r'^edit_samba_user/', require_login(edit_samba_user)),
    #url(r'^launch_swat/', require_login(launch_swat)),
    #url(r'^create_volume_get_num_bricks/([A-Za-z_]+)', require_login(get_num_bricks)),
    #url(r'^samba_server_settings_basic/', require_login(samba_server_settings_basic)),
    #url(r'^save_samba_server_settings_security/', require_login(save_samba_server_settings_security)),
    #url(r'^samba_server_settings_security/', require_login(samba_server_settings_security)),
    #url(r'^save_samba_server_settings_basic/', require_login(save_samba_server_settings_basic)),
    #url(r'^edit_samba_share/', require_login(edit_samba_share)),
    #url(r'^view_samba_share/', require_login(view_samba_share)),
)

