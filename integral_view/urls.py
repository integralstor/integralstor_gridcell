from django.conf.urls import patterns, include, url

#from integral_view.views.iscsi import iscsi_display_global_config, iscsi_display_initiators, iscsi_display_targets, iscsi_view_initiator, iscsi_edit_initiator, iscsi_create_initiator, iscsi_delete_initiator, iscsi_display_auth_access_group_list, iscsi_create_auth_access_group, iscsi_view_auth_access_group, iscsi_delete_auth_access_group, iscsi_edit_auth_access_user, iscsi_edit_target_global_config, iscsi_view_target_global_config, iscsi_create_target,iscsi_view_target , iscsi_edit_target, iscsi_delete_target, iscsi_delete_auth_access_user, iscsi_create_auth_access_user

from integral_view.views.stgt_iscsi_management import view_iscsi_targets, view_iscsi_target, create_iscsi_target, delete_iscsi_target, add_iscsi_user_authentication, remove_iscsi_user_authentication, create_iscsi_lun, delete_iscsi_lun, add_iscsi_acl, remove_iscsi_acl

from integral_view.views.admin_auth  import login, logout, change_admin_password, configure_email_settings, view_email_settings

from integral_view.views.gridcell_management  import view_gridcells, view_gridcell, remove_a_gridcell_from_storage_pool, add_a_gridcell_to_storage_pool, remove_a_gridcell_from_grid, scan_for_new_gridcells, replace_gridcell, replace_disk, identify_gridcell, identify_disk

from integral_view.views.volume_creation import volume_creation_wizard, create_volume, create_volume_conf

from integral_view.views.batch_process_management import view_batch_processes, view_batch_process

from integral_view.views.volume_management import view_volumes, view_volume, change_volume_status, expand_volume, set_volume_options, delete_volume, deactivate_snapshot, activate_snapshot, create_snapshot, delete_snapshot, restore_snapshot, set_dir_quota, remove_dir_quota, change_quota_status, initiate_volume_rebalance, volume_browser, create_volume_dir, remove_volume_dir, retrieve_volume_subdirs, volume_selector

from integral_view.views.log_management import view_audit_trail, view_alerts, rotate_log, download_sys_log, view_rotated_log_list, view_rotated_log_file

from integral_view.views.common import dashboard, access_shell

from integral_view.views.services_management import view_services,change_service_status_on_gridcell, view_ntp_settings, edit_ntp_settings

from integral_view.views.scheduler_management import schedule_scrub,view_scheduled_jobs,view_scheduled_job,remove_scheduled_job

from integral_view.views.log_management import download_vol_log, download_sys_log, rotate_log, view_rotated_log_list, view_rotated_log_file, refresh_alerts, raise_alert, internal_audit, download_system_configuration

from integral_view.views.cifs_share_management import view_cifs_shares, create_cifs_share, view_cifs_share, edit_cifs_share, delete_cifs_share, edit_cifs_authentication_method , view_cifs_authentication_settings, edit_cifs_authentication_settings

from integral_view.views.local_user_management import view_local_users, create_local_user, change_local_user_password, delete_local_user

from django.contrib.auth.decorators import login_required

from integral_view.decorators import login_and_admin_vol_mountpoint_required

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    #From admin_auth
    url(r'^login/', login),
    url(r'^logout/', logout),
    url(r'^$', login),
    url(r'^change_admin_password/', login_and_admin_vol_mountpoint_required(change_admin_password),name="change_admin_password"),
    url(r'^view_email_settings/', login_and_admin_vol_mountpoint_required(view_email_settings)),
    url(r'^configure_email_settings/', login_and_admin_vol_mountpoint_required(configure_email_settings)),


    #From batch_process_management
    url(r'^view_batch_processes/', login_and_admin_vol_mountpoint_required(view_batch_processes)),
    url(r'^view_batch_process/', login_and_admin_vol_mountpoint_required(view_batch_process)),

    #From cifs_share_management
    url(r'^view_cifs_shares/', login_and_admin_vol_mountpoint_required(view_cifs_shares)),
    url(r'^view_cifs_share/', login_and_admin_vol_mountpoint_required(view_cifs_share)),
    url(r'^edit_cifs_share/', login_and_admin_vol_mountpoint_required(edit_cifs_share)),
    url(r'^create_cifs_share/', login_and_admin_vol_mountpoint_required(create_cifs_share)),
    url(r'^delete_cifs_share/', login_and_admin_vol_mountpoint_required(delete_cifs_share)),
    url(r'^edit_cifs_authentication_method/', login_and_admin_vol_mountpoint_required(edit_cifs_authentication_method)),
    url(r'^view_cifs_authentication_settings/', login_and_admin_vol_mountpoint_required(view_cifs_authentication_settings)),
    url(r'^edit_cifs_authentication_settings/', login_and_admin_vol_mountpoint_required(edit_cifs_authentication_settings)),

    #From common
    url(r'^dashboard/', dashboard),
    url(r'^access_shell/', login_and_admin_vol_mountpoint_required(access_shell)),

    #From gridcell_management
    url(r'^view_gridcells/', login_and_admin_vol_mountpoint_required(view_gridcells)),
    url(r'^view_gridcell/', login_and_admin_vol_mountpoint_required(view_gridcell)),
    url(r'^scan_for_new_gridcells/', login_and_admin_vol_mountpoint_required(scan_for_new_gridcells)),
    url(r'^remove_a_gridcell_from_grid/', login_and_admin_vol_mountpoint_required(remove_a_gridcell_from_grid)),
    url(r'^add_a_gridcell_to_storage_pool/', login_and_admin_vol_mountpoint_required(add_a_gridcell_to_storage_pool)),
    url(r'^remove_a_gridcell_from_storage_pool/', login_and_admin_vol_mountpoint_required(remove_a_gridcell_from_storage_pool)),
    url(r'^replace_gridcell/', login_and_admin_vol_mountpoint_required(replace_gridcell)),
    url(r'^replace_disk/', login_and_admin_vol_mountpoint_required(replace_disk)),
    url(r'^identify_gridcell/', login_and_admin_vol_mountpoint_required(identify_gridcell)),
    url(r'^identify_disk/', login_and_admin_vol_mountpoint_required(identify_disk)),

    #From local_user_management
    url(r'^view_local_users/', login_and_admin_vol_mountpoint_required(view_local_users)),
    url(r'^create_local_user/', login_and_admin_vol_mountpoint_required(create_local_user)),
    url(r'^delete_local_user/', login_and_admin_vol_mountpoint_required(delete_local_user)),
    url(r'^change_local_user_password/', login_and_admin_vol_mountpoint_required(change_local_user_password)),

    #From log_management
    url(r'^view_alerts/', login_and_admin_vol_mountpoint_required(view_alerts)),
    url(r'^view_audit_trail/', login_and_admin_vol_mountpoint_required(view_audit_trail)),
    url(r'^rotate_log/([A-Za-z_]+)', login_and_admin_vol_mountpoint_required(rotate_log)),
    url(r'^download_vol_log/', login_and_admin_vol_mountpoint_required(download_vol_log)),
    url(r'^download_sys_log/', login_and_admin_vol_mountpoint_required(download_sys_log)),
    url(r'^view_rotated_log_list/([A-Za-z_]+)', login_and_admin_vol_mountpoint_required(view_rotated_log_list)),
    url(r'^view_rotated_log_file/([A-Za-z_]+)', login_and_admin_vol_mountpoint_required(view_rotated_log_file)),
    #url(r'^refresh_alerts/([0-9_]*)', login_and_admin_vol_mountpoint_required(refresh_alerts)),
    url(r'^refresh_alerts/', login_and_admin_vol_mountpoint_required(refresh_alerts)),
    url(r'^raise_alert/', login_and_admin_vol_mountpoint_required(raise_alert)),
    url(r'^internal_audit/', login_and_admin_vol_mountpoint_required(internal_audit)),
    url(r'^download_system_configuration/', login_and_admin_vol_mountpoint_required(download_system_configuration)),

    #From scheduler_management
    url(r'^schedule_scrub/', login_and_admin_vol_mountpoint_required(schedule_scrub)),
    url(r'^view_scheduled_jobs/',login_and_admin_vol_mountpoint_required(view_scheduled_jobs)),
    url(r'^view_scheduled_job/([0-9]*)',login_and_admin_vol_mountpoint_required(view_scheduled_job)),

    #From services_management
    url(r'^view_services/', login_and_admin_vol_mountpoint_required(view_services)),
    url(r'^change_service_status_on_gridcell/', login_and_admin_vol_mountpoint_required(change_service_status_on_gridcell)),
    url(r'^view_ntp_settings/', login_and_admin_vol_mountpoint_required(view_ntp_settings)),
    url(r'^edit_ntp_settings/', login_and_admin_vol_mountpoint_required(edit_ntp_settings)),

    #From stgt_iscsi_management
    url(r'^view_iscsi_targets/', login_and_admin_vol_mountpoint_required(view_iscsi_targets)),
    url(r'^view_iscsi_target/', login_and_admin_vol_mountpoint_required(view_iscsi_target)),
    url(r'^create_iscsi_target/', login_and_admin_vol_mountpoint_required(create_iscsi_target)),
    url(r'^delete_iscsi_target/', login_and_admin_vol_mountpoint_required(delete_iscsi_target)),
    url(r'^create_iscsi_lun/', login_and_admin_vol_mountpoint_required(create_iscsi_lun)),
    url(r'^delete_iscsi_lun/', login_and_admin_vol_mountpoint_required(delete_iscsi_lun)),
    url(r'^add_iscsi_user_authentication/', login_and_admin_vol_mountpoint_required(add_iscsi_user_authentication)),
    url(r'^remove_iscsi_user_authentication/', login_and_admin_vol_mountpoint_required(remove_iscsi_user_authentication)),
    url(r'^add_iscsi_acl/', login_and_admin_vol_mountpoint_required(add_iscsi_acl)),
    url(r'^remove_iscsi_acl/', login_and_admin_vol_mountpoint_required(remove_iscsi_acl)),

    #From volume_creation
    url(r'^volume_creation_wizard/([A-Za-z_]+)', login_and_admin_vol_mountpoint_required(volume_creation_wizard)),
    url(r'^create_volume_conf/', login_and_admin_vol_mountpoint_required(create_volume_conf)),
    url(r'^create_volume/', login_and_admin_vol_mountpoint_required(create_volume)),

    #From volume_management
    url(r'^view_volumes/', login_and_admin_vol_mountpoint_required(view_volumes)),
    url(r'^volume_selector/', login_and_admin_vol_mountpoint_required(volume_selector)),
    url(r'^view_volume/', login_and_admin_vol_mountpoint_required(view_volume)),
    url(r'^volume_browser/', login_and_admin_vol_mountpoint_required(volume_browser)),
    url(r'^create_volume_dir/', login_and_admin_vol_mountpoint_required(create_volume_dir)),
    url(r'^remove_volume_dir/', login_and_admin_vol_mountpoint_required(remove_volume_dir)),
    url(r'^retrieve_volume_subdirs/', login_and_admin_vol_mountpoint_required(retrieve_volume_subdirs)),
    url(r'^change_volume_status/', login_and_admin_vol_mountpoint_required(change_volume_status)),
    url(r'^delete_volume/', login_and_admin_vol_mountpoint_required(delete_volume)),
    url(r'^expand_volume/', login_and_admin_vol_mountpoint_required(expand_volume)),
    url(r'^initiate_volume_rebalance/', login_and_admin_vol_mountpoint_required(initiate_volume_rebalance)),
    url(r'^set_volume_options/', login_and_admin_vol_mountpoint_required(set_volume_options)),
    url(r'^set_dir_quota/', login_and_admin_vol_mountpoint_required(set_dir_quota)),
    url(r'^remove_dir_quota/', login_and_admin_vol_mountpoint_required(remove_dir_quota)),
    url(r'^change_quota_status/', login_and_admin_vol_mountpoint_required(change_quota_status)),
    url(r'^create_snapshot/', login_and_admin_vol_mountpoint_required(create_snapshot)),
    url(r'^delete_snapshot/', login_and_admin_vol_mountpoint_required(delete_snapshot)),
    url(r'^restore_snapshot/', login_and_admin_vol_mountpoint_required(restore_snapshot)),
    url(r'^deactivate_snapshot/', login_and_admin_vol_mountpoint_required(deactivate_snapshot)),
    url(r'^activate_snapshot/', login_and_admin_vol_mountpoint_required(activate_snapshot)),

    #url(r'^edit_integral_view_log_level/', login_and_admin_vol_mountpoint_required(edit_integral_view_log_level)),
    #url(r'^auth_server_settings/', login_and_admin_vol_mountpoint_required(samba_server_settings)),
    #url(r'^save_samba_server_settings/', login_and_admin_vol_mountpoint_required(save_samba_server_settings)),
    #url(r'^show/([A-Za-z0-9_]+)/([a-zA-Z0-9_\-\.]*)', login_and_admin_vol_mountpoint_required(show),name="show_page"),
    #url(r'^perform_op/([A-Za-z_]+)/([A-Za-z0-9_\-]*)/([A-Za-z0-9_\.\-\:\/]*)', login_and_admin_vol_mountpoint_required(perform_op.perform_op)),
    #url(r'^volume_specific_op/([A-Za-z_]+)/([A-Za-z0-9_\-]*)', login_and_admin_vol_mountpoint_required(volume_specific_op)),
    #url(r'^volume_specific_op/create_volume_dir/', login_and_admin_vol_mountpoint_required(volume_specific_op),name="create_vol_dir"),
    #url(r'^first_login/', login_and_admin_vol_mountpoint_required(hardware_scan)),


    url(r'^remove_scheduled_job/',login_and_admin_vol_mountpoint_required(remove_scheduled_job)),
    #url(r'^view_task_details/([0-9]*)', login_and_admin_vol_mountpoint_required(view_task_details)),
    
)

"""
    #url(r'^server_op/([A-Za-z_]+)', login_and_admin_vol_mountpoint_required(server_op)),
    #url(r'^sys_log/([A-Za-z]+)', sys_log),
    #url(r'^pull_node_status/([A-Za-z_\-0-9]+)', login_required(pull_node_status)),
    #url(r'^node_status/', node_status),
    ## url(r'^view_log/([A-Za-z_]*)/([0-9]*)/([0-9]*)', login_required(view_log)),
    ## url(r'^view_log/([A-Za-z_]*)', login_required(view_log)),
    #url(r'^download_vol_log/([A-Za-z0-9_\-\:\/]*)', login_required(download_vol_log)),
    #url(r'^display_users/', login_required(display_users)),
    #url(r'^create_user/', login_required(create_user)),
    #url(r'^create_unix_user/', login_required(create_unix_user)),
    #url(r'^perform_op/([A-Za-z_]+)/([A-Za-z0-9_\-]*)', login_required(perform_op.perform_op)),
    #url(r'^edit_samba_user/', login_required(edit_samba_user)),
    #url(r'^launch_swat/', login_required(launch_swat)),
    #url(r'^create_volume_get_num_bricks/([A-Za-z_]+)', login_required(get_num_bricks)),
    #url(r'^samba_server_settings_basic/', login_required(samba_server_settings_basic)),
    #url(r'^save_samba_server_settings_security/', login_required(save_samba_server_settings_security)),
    #url(r'^samba_server_settings_security/', login_required(samba_server_settings_security)),
    #url(r'^save_samba_server_settings_basic/', login_required(save_samba_server_settings_basic)),
    #url(r'^edit_samba_share/', login_required(edit_samba_share)),
    #url(r'^view_samba_share/', login_required(view_samba_share)),
    # ISCSI Initiator
    url(r'^iscsi_create_initiator/', login_required(iscsi_create_initiator)),
    url(r'^iscsi_display_initiators/', login_required(iscsi_display_initiators)),
    url(r'^iscsi_view_initiator/', login_required(iscsi_view_initiator)),
    url(r'^iscsi_delete_initiator/', login_required(iscsi_delete_initiator)),
    url(r'^iscsi_edit_initiator/', login_required(iscsi_edit_initiator)),

    # ISCSI Targets
    url(r'^iscsi_create_target/', login_required(iscsi_create_target)),
    url(r'^iscsi_display_targets/', login_required(iscsi_display_targets)),
    url(r'^iscsi_view_target/', login_required(iscsi_view_target)),
    url(r'^iscsi_edit_target/', login_required(iscsi_edit_target)),
    url(r'^iscsi_delete_target/', login_required(iscsi_delete_target)),

    # ISCSI Utilities
    url(r'^iscsi_create_auth_access_user/', login_required(iscsi_create_auth_access_user)),
    url(r'^iscsi_display_auth_access_group_list/', login_required(iscsi_display_auth_access_group_list)),
    url(r'^iscsi_create_auth_access_group/', login_required(iscsi_create_auth_access_group)),
    url(r'^iscsi_view_auth_access_group/', login_required(iscsi_view_auth_access_group)),
    url(r'^iscsi_delete_auth_access_group/', login_required(iscsi_delete_auth_access_group)),
    url(r'^iscsi_delete_auth_access_user/', login_required(iscsi_delete_auth_access_user)),
    url(r'^iscsi_edit_auth_access_user/', login_required(iscsi_edit_auth_access_user)),
    url(r'^iscsi_edit_target_global_config/', login_required(iscsi_edit_target_global_config)),
    url(r'^iscsi_view_target_global_config/', login_required(iscsi_view_target_global_config)),

"""
