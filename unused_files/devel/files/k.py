from ConfigParser import SafeConfigParser

parser = SafeConfigParser()
parser.read("krb5.conf")

print parser.get("appdefaults", "pam")

# vim: tabstop=8 softtabstop=0 expandtab ai shiftwidth=4 smarttab
