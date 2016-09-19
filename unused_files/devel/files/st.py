
import time
with open("test_status", "a") as f:
  i=0
  while i < 20:
    f.write("aai\n")
    f.flush()
    time.sleep(2)
    i += 1
f.close()

