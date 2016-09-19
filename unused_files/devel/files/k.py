from ConfigParser import SafeConfigParser

parser = SafeConfigParser()
parser.read("krb5.conf")

print parser.get("appdefaults", "pam")
