
import json,sqlite3

from django.conf import settings

def read_single_row(db_path, query):
  d = {}
  conn = None
  try :
    #conn = sqlite3.connect("%s/integral_view_config.db"%settings.DB_LOCATION)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query)
    r = cur.fetchone()
    if not r:
      return None
    d = {}
    for key in r.keys():
      d[key] = r[key]
  finally:
    if conn:
      conn.close()
  return d

def read_multiple_rows(db_path, query):
  l = []
  conn = None
  try :
    #conn = sqlite3.connect("%s/integral_view_config.db"%settings.DB_LOCATION)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    if not rows:
      return None
    for row in rows:
      d = {}
      for key in row.keys():
        d[key] = row[key]
      l.append(d)
  finally:
    if conn:
      conn.close()
  return l

def execute_iud(db_path, command_list, get_rowid = False):
  #command_list is a list of commands to execute in a transaction. Each command can have just the command or command with parameters
  conn = None
  rowid = -1
  try :
    #conn = sqlite3.connect("%s/integral_view_config.db"%settings.DB_LOCATION)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    for command in command_list:
      if len(command) > 1:
        cur.execute(command[0], command[1])
      else:
        cur.execute(command[0])
    if get_rowid:
      rowid = cur.lastrowid
    cur.close()
    conn.commit()
  finally:
    if conn:
      conn.close()
  return rowid
