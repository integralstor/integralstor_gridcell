
import os

def rescan_drives():
  for dirname, dirs, files in os.walk('/sys/class/scsi_host/'):
    #print dirs
    for dir in dirs:
      #print '/sys/class/scsi_host/%s/scan'%dir
      with open('/sys/class/scsi_host/%s/scan'%dir, 'w') as f:
        #print '/sys/class/scsi_host/%s/scan'%dir
        f.write('- - -')
        f.close()

def main():
  rescan_drives()

if __name__ == '__main__':
  main()   

