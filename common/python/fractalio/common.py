import os

def is_production():

  if os.path.isfile('/opt/fractalio/devel_env'):
    return False
  else:
    return True

def get_salt_master_config():
  return '/etc/salt/master'

def get_krb5_conf_path():
  return '/etc'

def get_smb_conf_path():
  return '/etc'

def get_fractalio_admin_volume_name():
  return "fractalio_admin_vol"

def get_system_status_path():
  return "/opt/fractalio/status"

def get_ntp_conf_path():
  return "/etc"

def get_db_path():
  return "/opt/fractalio/db"

def get_batch_files_path():
  return "/opt/fractalio/batch_processes"

def get_devel_files_path():
  return "/opt/fractalio/devel/files"

def get_audit_dir():
  return "/opt/fractalio/logs/audit"

def get_audit_url_component():
  return "internal_audit"

def get_audit_url_host():
  return "integral_view.fractalio.lan"

def get_alerts_dir():
  return "/opt/fractalio/logs/alerts"

def get_alerts_url_component():
  return "raise_alert"

def get_alerts_url_host():
  return "integral_view.fractalio.lan"

def main():
  print is_production()

if __name__ == "__main__":
  main()
