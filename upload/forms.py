from django import forms
from .models import StopWords,AddFiles
from django.forms import ModelForm



class StopWordsForm(ModelForm):
    class Meta:
        model = StopWords
        fields = '__all__'   
           

class FilesForm(ModelForm):
    class Meta:
        model = AddFiles
        fields = '__all__'   

    def __init__(self, *args, **kwargs):  
        super(FilesForm, self).__init__(*args, **kwargs)
        self.fields['words'].empty_label = None
        





class GeeksForm(forms.Form):
    words = forms.CharField()

class FileFieldForm(forms.Form):
    file_field = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))

 
        