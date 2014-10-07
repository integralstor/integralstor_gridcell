import re

def is_ip(addr):
  test = re.compile('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
  result = test.match(addr)
  if result:
    return True
  else:
    return False

def is_valid_ip(addr):
  if not is_ip(addr):
    return False
  match = re.search('([0-9]+)\.([0-9]+)\.([0-9]+)\.([0-9]+)', addr)
  ip_tup = match.groups()
  for i in range(4):
    n = int(ip_tup[i])
    if n < 1 or n > 255:
      return False
  return True

def is_valid_hostname(hostname):
    if len(hostname) > 255:
        return False
    if hostname.endswith("."): # A single trailing dot is legal
        hostname = hostname[:-1] # strip exactly one dot from the right, if present
    disallowed = re.compile("[^A-Z\d-]", re.IGNORECASE)
    return all( # Split by labels and verify individually
        (label and len(label) <= 63 # length is within proper range
         and not label.startswith("-") and not label.endswith("-") # no bordering hyphens
         and not disallowed.search(label)) # contains only legal characters
        for label in hostname.split("."))

def is_valid_ip_or_hostname(addr):
  ret = False

  if is_ip(addr):
    if is_valid_ip(addr) :
      ret = True
  else:
    if is_valid_hostname(addr):
      ret = True

  return ret

def main():

  print is_ip("a.b.c")
  print is_ip("1.2.c")
  print is_ip("11.12.14.13")

  print is_valid_ip("1.2.3.4")
  print is_valid_ip("1.2.3.400")

  print is_valid_hostname("jkj&.hh.com")
  print is_valid_hostname("a.hh.com")

  print is_valid_ip_or_hostname("1.2.3.4")
  print is_valid_ip_or_hostname("a.b.c")
  print is_valid_ip_or_hostname("1111.2.1.2")
  print is_valid_hostname("1111.2.1.2")

if __name__ == "__main__":
  main()
