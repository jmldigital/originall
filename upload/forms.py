from django import forms
from .models import StopWords,AddFiles,Brands
from django.forms import ModelForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Fieldset, Div, HTML, ButtonHolder, Submit, Row, Column




class StopWordsForm(ModelForm):
    class Meta:
        model = StopWords
        fields = '__all__'   


class BrandsForm(ModelForm):
    class Meta:
        model = Brands
        fields = '__all__' 


class BrandsUploadForm(ModelForm):
    class Meta:
        model = Brands
        fields = ['files'] 
           

class FilesForm(ModelForm):
    class Meta:
        model = AddFiles
        fields = '__all__'   

    def __init__(self, *args, **kwargs):  
        super(FilesForm, self).__init__(*args, **kwargs)
        self.fields['currency_field'].empty_label = None

        self.helper = FormHelper()
        self.helper.form_tag = True
        # self.helper.form_class = 'form-inline'
        self.helper.field_class = 'mr-5' 
        # self.helper.submit_class = 'hidden'  
        # self.helper.label_class = ''
        
        self.helper.layout = Layout(
        Row(
                Column('brend_field', css_class='form-group mr-5 col-md-6 mb-0'),
                Column('currency_field', css_class='form-group mr-5 col-md-6 mb-0'),
                Column('files', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ), 

            Submit('btnform2', 'Добавить прайс', css_class='bg-blue-500 hover:bg-blue-600 px-3 py-3 mt-7 text-white rounded-md color-white')
        
        )

class GeeksForm(forms.Form):
    words = forms.CharField()

class FileFieldForm(forms.Form):
    file_field = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))

 
        