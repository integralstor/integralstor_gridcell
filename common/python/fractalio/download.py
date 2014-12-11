import urllib2


def url_download(urlname):
  """ Used to download the output of a given url and return a dict with the content, type(attachment/normal) and content-disposition.
  The dict value of error is set if the download could not happen"""

  dict = {}
  dict["error"] = None
  try :
    ur = urllib2.urlopen(urlname)
  except urllib2.URLError as e:
    dict["error"] = "Could not contact the requested host"
    return dict
  if ur:
    if 'content-disposition' in ur.info():
      dict["type"] = "attachment"
      inf = ur.info().getheader('content-disposition')
      dict["content-disposition"] = inf
    else:
      dict["type"] = "normal"
    dict["content"] = ur.read()

  return dict

def main():

  dict = url_download("http://www.google.com")
  print dict

if __name__ == "__main__":
  main()
