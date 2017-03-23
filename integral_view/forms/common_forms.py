
from django import forms

import re

from integralstor_utils import networking


class MultipleServerField(forms.CharField):

    def _is_valid_server(self, server):
        server = server.strip()
        valid, err = networking.validate_ip_or_hostname(server)
        if valid:
            return True
        else:
            return False

    def clean(self, value):
        if not value:
            raise forms.ValidationError(
                "Enter atleast one IP address or hostname")
        if ',' in value:
            servers = value.lower().split(',')
        else:
            servers = value.lower().split(' ')
        for server in servers:
            if not self._is_valid_server(server):
                raise forms.ValidationError(
                    "%s is not a valid address" % server)

        return value.lower()


class ConfigureNTPForm(forms.Form):

    server_list = MultipleServerField()


# vim: tabstop=8 softtabstop=0 expandtab ai shiftwidth=4 smarttab
