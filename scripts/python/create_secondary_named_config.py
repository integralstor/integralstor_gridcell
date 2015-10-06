import sys
from integralstor_common import networking, command

def main():

  rc = 0
  try:
    forwarder_ip = None

    if len(sys.argv) < 4:
      print "Usage : %s primary_ip secondary_ip secondary_netmask <forwarder_ip>"%sys.argv[0]
      sys.exit(-1)

    primary_ip = sys.argv[1]
    secondary_ip = sys.argv[2]
    secondary_netmask = sys.argv[3]

    if len(sys.argv) > 4:
      forwarder_ip = sys.argv[4]

    if forwarder_ip:
      rc, err = networking.generate_default_secondary_named_conf(primary_ip, secondary_netmask, secondary_ip, True, forwarder_ip)
    else:
      rc, err = networking.generate_default_secondary_named_conf(primary_ip, secondary_netmask, secondary_ip)

    if err:
      raise Exception(err)
    if rc :
      (r, rc), err = command.execute_with_rc('service named reload')
      if err:
        raise Exception(err)
      if rc != 0:
        raise Exception("Error restarting the DNS server")
    else:
      raise Exception('')
  except Exception, e:
    print "Error creating the secondary named configuration : %s"%e
    return -1
  else:
    return rc

if __name__ == '__main__':
  main()
