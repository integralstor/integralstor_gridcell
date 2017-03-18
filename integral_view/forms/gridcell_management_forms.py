from django import forms


class AddGridcellsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if kwargs:
            pml = kwargs.pop('pending_minions_list')
        super(AddGridcellsForm, self).__init__(*args, **kwargs)
        ch = []
        for minion in pml:
            tup = (minion, minion)
            ch.append(tup)
        self.fields["gridcells"] = forms.MultipleChoiceField(
            widget=forms.CheckboxSelectMultiple, choices=ch)


# vim: tabstop=8 softtabstop=0 expandtab ai shiftwidth=4 smarttab
