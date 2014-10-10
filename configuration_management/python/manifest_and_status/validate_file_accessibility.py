#!/usr/bin/python


def file_validation(filename = None):
    """ This method validates whether file """
   
    if filename is None:
        print "No filename given"
        return -1
  
    try:
        with open(filename, "w") as fh:
            pass
    except Exception as e:
        print str(e)
        return -1

if __name__ == '__main__':
    ret_val = file_validation("/config/qq")
    print "Return value : ", ret_val
