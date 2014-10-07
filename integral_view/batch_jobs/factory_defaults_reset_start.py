import sys, json, time, subprocess, os
import settings

path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '%s/../..'%path)
os.environ['DJANGO_SETTINGS_MODULE']='integral_view.settings'

def main():

  fname = sys.argv[1]
  r = subprocess.Popen([sys.executable, '%s/batch_jobs/factory_defaults_reset_start.py'%integral_view.settings.BASE_APP_PATH, integral_view.settings.BASE_APP_ROOT, fname], stdout = subprocess.PIPE, stderr=subprocess.STDOUT)
  print r.returncode
  return 0

if __name__ == "__main__":
  main()

