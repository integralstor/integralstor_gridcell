import os

def is_production():

  if os.path.isfile('/opt/fractalio/devel_env'):
    return False
  else:
    return True

def get_defaults_dir():
  return "/opt/fractalio/defaults"

def get_bin_dir():
  return "/opt/fractalio/bin"

def get_tmp_path():
  return "/opt/fractalio/tmp"

def get_admin_vol_name():
  return "fractalio_admin_vol"

def get_admin_vol_mountpoint():
  return "/opt/fractalio/mnt/admin_vol"

def get_salt_master_config():
  return '/etc/salt/master'

def get_krb5_conf_path():
  return '/etc'

def get_smb_conf_path():
  return '/etc/samba'

def get_system_status_path():
  return "%s/status"%get_admin_vol_mountpoint()

def get_ntp_conf_path():
  return "/etc"

def get_db_path():
  return "%s/db"%get_admin_vol_mountpoint()

def get_batch_files_path():
  return "%s/batch_processes"%get_admin_vol_mountpoint()

def get_devel_files_path():
  return "/opt/fractalio/devel/files"

def get_audit_dir():
  return "%s/logs/audit"%get_admin_vol_mountpoint()

def get_audit_url_component():
  return "internal_audit"

def get_audit_url_host():
  return "integral_view.fractalio.lan"

def get_alerts_dir():
  return "%s/logs/alerts"%get_admin_vol_mountpoint()

def get_alerts_url_component():
  return "raise_alert"

def get_alerts_url_host():
  return "integral_view.fractalio.lan"

def main():
  print is_production()

if __name__ == "__main__":
  main()
