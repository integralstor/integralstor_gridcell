from django import forms


class LocalUserForm(forms.Form):

    userid = forms.CharField()
    name = forms.CharField(required=False)
    password = forms.CharField(widget=forms.PasswordInput())
    password_conf = forms.CharField(widget=forms.PasswordInput())

    def clean(self):
        cd = super(LocalUserForm, self).clean()
        if "password" in cd and "password_conf" in cd:
            if cd["password"] != cd["password_conf"]:
                self._errors["password"] = self.error_class(
                    ["The password and password confirmation do not match."])
                del cd["password"]
                del cd["password_conf"]
        if "'" in cd["name"] or '"' in cd["name"]:
            self._errors["name"] = self.error_class(
                ["The name cannot contain special characters."])
            del cd["name"]
        if cd['userid'][0].isdigit():
            self._errors["userid"] = self.error_class(
                ["The username cannot contain begin with numbers."])
            del cd["userid"]
        if "name" in cd:
            n = cd["name"]
            cd["name"] = "_".join(n.split())
        return cd


class PasswordChangeForm(forms.Form):

    userid = forms.CharField(widget=forms.HiddenInput)
    password = forms.CharField(widget=forms.PasswordInput())
    password_conf = forms.CharField(widget=forms.PasswordInput())

    def clean(self):
        cd = super(PasswordChangeForm, self).clean()
        if "password" in cd and "password_conf" in cd:
            if cd["password"] != cd["password_conf"]:
                self._errors["password"] = self.error_class(
                    ["The password and password confirmation do not match."])
                del cd["password"]
                del cd["password_conf"]
        return cd

# vim: tabstop=8 softtabstop=0 expandtab ai shiftwidth=4 smarttab
