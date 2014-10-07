import smtplib
import email.utils
from email.mime.text import MIMEText

msg = MIMEText("Test email from home")
msg.set_unixfrom('home')
msg['To'] = email.utils.formataddr(('Recipient', 'bkrram@gmail.com'))
msg['From'] = email.utils.formataddr(('Raghuram', 'ram@fractal-io.com'))
msg['Subject'] = 'Test email header'
print "Opening connection"
server = smtplib.SMTP('smtp.gmail.com', 587)
print "Opened connection"

try:
  server.set_debuglevel(True)
  server.ehlo()
  if server.has_extn('STARTTLS'):
    server.starttls()
    server.ehlo()

  server.login('bkrram@gmail.com', 'WeLiveNearMagadi')
  server.sendmail('ram@fractal-io.com', ['bkrram@gmail.com'], msg.as_string())
finally:
  server.quit()

