import time

i=0
with open("/home/bkrram/fractal/gluster_admin/gluster_admin/devel/files/status/hs_Jun_13_2014_15_16_15_1402652775", "a") as f:
  while i < 10:
    f.write("aaa\n")
    f.flush()
    time.sleep(1)
    i += 1
  f.write("==done==")
  f.flush()
f.close()

