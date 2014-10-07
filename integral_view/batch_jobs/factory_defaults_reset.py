import sys, json, time

def main():

  with open("/tmp/err", "w") as errf:
    if len(sys.argv) < 2:
      errf.write("no settings!")
      errf.flush()
      return -1

    sys.path.insert(0, sys.argv[1])

    fname = sys.argv[2]
    errf.write("fname %s"%fname)
    errf.flush()
    print "fname=%s"%fname
    l = []
    i = 0
    try :
      print i
      errf.write("%d"%i)
      errf.flush()
      while i < 10:
        d = {"process_name":"Process %d"%i, "status": i}
        l.append(d)
        errf.write(str(l))
        f = open(fname, "w")
        json.dump(l, f, indent=2)
        f.close()
        time.sleep(5)
        i = i+1
    except Exception, e:
      errf.write("Exception : %s"%str(e))
    finally:
      f.close()


  '''
  vil = volume_info.get_volume_info_all()
  scl = system_info.load_system_config()
  for v in vil:
    if v["status"] == "1":
      // Stop this volume
      command = 'gluster volume stop %s force'%name1
      //l.append(v["name"])
  for v in vil:
    command = 'gluster volume delete %s force'%name1
  // Remove all the volume directories..
  for n in scl:
    command = 'gluster peer detach %s --xml'%n["hostname"]
  // Reset the ntp config file
  shutil.copyfile("%s/defaults"%settings.BASE_CONF_PATH, '%s/ntp.conf'%settings.NTP_CONF_PATH)
  // Remove email settings
  mail.delete_email_settings()
  '''
    
if __name__ == "__main__":
  main()
