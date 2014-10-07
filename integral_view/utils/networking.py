import socket

def can_connect(hostname, port, timeout=0.05):

  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.settimeout(timeout)

  connected = True if s.connect_ex((hostname,port)) == 0 else False

  return connected
