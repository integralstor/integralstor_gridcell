from django import forms

class SystemLogsForm(forms.Form):
  """ Form to get the info about which system log to download"""

  ch = [('boot', 'Boot log'), ('dmesg', 'Dmesg log'), ('message', 'Message Log')]
  sys_log_type = forms.ChoiceField(choices=ch)

  def __init__(self, *args, **kwargs):

    if kwargs:
      si = kwargs.pop('system_config_list')

    super(SystemLogsForm, self).__init__(*args, **kwargs)
    ch = []

    if si:
      for hostname in si.keys():
        if si[hostname]["node_status"] < 0:
          continue
        tup = (hostname,hostname)
        ch.append(tup)
    self.fields['hostname'] = forms.ChoiceField(choices = ch)



