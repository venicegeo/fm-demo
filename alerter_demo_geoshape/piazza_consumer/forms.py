from django import forms

class ListenerForm(forms.Form):
    listener_topic = forms.CharField(label='Listener Topic', max_length=100)
    listener_key = forms.CharField(label='Listener Key', max_length=100)

class UploadFulcrumData(forms.Form):
    file = forms.FileField()
