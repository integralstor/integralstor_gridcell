import urllib, urllib2

url = 'http://127.0.0.1:8000/internal_audit/'
data = urllib.urlencode({'who' : 'batch',
                          'audit_action':'remove_storage',
                         'audit_str'  : 'Removed sled 99'})
content = urllib2.urlopen(url=url, data=data).read()
print content
