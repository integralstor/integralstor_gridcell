
import time
with open("test_status", "a") as f:
    i = 0
    while i < 20:
        f.write("aai\n")
        f.flush()
        time.sleep(2)
        i += 1
f.close()


# vim: tabstop=8 softtabstop=0 expandtab ai shiftwidth=4 smarttab
