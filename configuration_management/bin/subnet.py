
import re

def main():
  ip_str = "192.168.1.2"
  subnet_str = "255.255.255.0"
  lst = get_ip_list(ip_str, subnet_str)
  print lst

def get_ip_list(ip_str, subnet_str):

  match = re.search('([0-9]+)\.([0-9]+)\.([0-9]+)\.([0-9]+)', ip_str)
  ip_tup = match.groups()
  match = re.search('([0-9]+)\.([0-9]+)\.([0-9]+)\.([0-9]+)', subnet_str)
  subnet_tup = match.groups()

  host = []
  for i in range(4):
    if int(subnet_tup[i]) != 255:
      if int(ip_tup[i]) < int(subnet_tup[i]):
        print "IP Address not in given network!!"
        return 1
    host.append(int(ip_tup[i]) & int(subnet_tup[i]))
  #print "host"
  #print host

  for i in range(4):
    #print "i=%d"%i
    #print subnet_tup[i]
    if int(subnet_tup[i]) == 255:
      continue
    else:
      break
  #print "final i=%d"%i
  ip_list = []
  #return
  if i == 0:
    d1 = host[0]
    while d1 < 256:
      for d2 in range(1,256):
        for d3 in range(1,256):
          for d4 in range(1,255):
            ip_list.append("%d.%d.%d.%d"%(d1,d2,d3,d4))
  elif i == 1:
    d1 = host[0]
    d2 = host[1]
    while d2 < 256:
      for d3 in range(1,256):
        for d4 in range(1,255):
          ip_list.append("%d.%d.%d.%d"%(d1,d2,d3,d4))
      d2 = d2+1
  elif i == 2:
    d1 = host[0]
    d2 = host[1]
    d3 = host[2]
    while d3 < 256:
      for d4 in range(1,255):
        ip_list.append("%d.%d.%d.%d"%(d1,d2,d3,d4))
      d3 = d3+1
  else:
    d1 = host[0]
    d2 = host[1]
    d3 = host[2]
    d4 = host[3]
    while d4 < 256:
      if d4 in [0,255]:
        d4 = d4+1
        continue
      ip_list.append("%d.%d.%d.%d"%(d1,d2,d3,d4))
      d4 = d4+1

  #print "Number of IPs = %d" %len(ip_list)
  #print ip_list
  return ip_list

#  for ns in subnet_tup:
#    print ns
#    if 

if __name__ == "__main__":
  main()
