import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from django.db import connection
cursor = connection.cursor()
cursor.execute("select * from samba_config_global_conf")
row = cursor.fetchone()
print row

# vim: tabstop=8 softtabstop=0 expandtab ai shiftwidth=4 smarttab
