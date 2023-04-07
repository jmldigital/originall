from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
import pandas as pd
#import numpy as np
import os.path
from mechanize import Browser
import cgi
from .forms import StopWordsForm, FilesForm
from .models import StopWords,AddFiles
from django.views import generic
from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse




from django.views.generic.edit import FormView

from .forms import FileFieldForm

#python manage.py migrate --run-syncdb

fields = {
'oem_field':['artikel','nummer','id','sachnummer','zahl','number','article','nr','num','номер','артикль','артикул'],
# 'price':['price','cost','preis','цена','стоимость'],
'brend_field':['makename','brand','preis','marke','hersteller','производитель'],
'name_field':['detailname','titel','title','название','bezde'],
# 'quantity':['volume','menge','quantity','кол-во','количество','min'],
'weight_field':['weight','gewicht','вес','кг'],
'volume_field':['volume','band','umfang','lautstärke','volumen','объем'] }



def file_delete(request, id=None):   
    file = AddFiles.objects.get(id=id)
    file.delete()
    return redirect("/")  

    # return render(request, "upload.html")




def stop_create(request):
    form2 = StopWordsForm()
    if request.method == "POST":
        form2 = StopWordsForm(request.POST, request.FILES)
        if form2.is_valid():
            form2.save()
            return redirect("create")
    context = {
        "form": form2
    }   

    return render(request, "index.html", context)
    



def Words_update(request, pk):
    words = StopWords.objects.get(id=pk)
    form3 = StopWordsForm(instance=words )
    if request.method == "POST":
        form3 = StopWordsForm(request.POST,request.FILES,instance=words)
        if form3.is_valid():
            form3.save()
            return redirect("/edit/4/")

    context = {
        "words": words,
        "form": form3
    }

    return render(request, "upload.html", context)
  




def image_upload(request):
    context ={}
    arr=[]
    tit={}
    frame=''
    html_str = ''
    r=[]

 


    form_files = FilesForm(prefix='name2')
    obj=StopWords.objects.get(id=1)
  
    # print('before',type(obj.words))
    words = obj.words
    form_words = StopWordsForm(instance=obj)


    if request.method == "POST":
        form_words = StopWordsForm(request.POST or None, instance=obj)
   
        if form_words.is_valid():
            form_words.save()
            return redirect("/")  
        

#------------------------Добавляем фйлы-------------------------------------------
    if request.method == "POST":
        form_files = FilesForm(request.POST or None, request.FILES,prefix='name2')
        words = StopWords.objects.get(id=1)
        if form_files.is_valid():

            words.words = words
            # words.save()
            form_files.save(commit=False)
            file = form_files.cleaned_data['files']
            files_str = form_files.cleaned_data['files'].name
            extension = files_str.split(".")[1]
            if extension == 'xls':
                anime = pd.read_excel(file)
                for title in anime.columns.tolist():
                    for key in fields.keys():
                        if any(ext in title.lower() for ext in fields[key]):
                            arr.append(title)
                            tit[key]=title

            anime_cleare = anime[arr] 
            for key in fields.keys():  
                if key in tit.keys():
                    print('')
                else:
                    tit[key] = 'ничего'   

            # print(tit)
            # print(tit["brend_field"])
            
            AddFiles.objects.create(
            files=file,
            oem_field=tit['oem_field'],
            brend_field=tit['brend_field'],
            name_field=tit['name_field'],
            weight_field=tit['weight_field'],
            volume_field=tit['volume_field'],

            )
           
            # frame = anime_cleare.to_html('upload/templates/filename.html')
            frame = anime_cleare.to_html()
            # r.append(frame)

            # ff=render(request, frame)
            # print(HttpResponse(frame))
  
            # print(frame)

            


            # HttpResponse(frame, headers={'Content-Type': 'text/html'})
            # form_files.save()
            return redirect("/")  


    # mytextfield = "".join(frame.split())
    print('nen',frame)
    context = {
        'files':AddFiles.objects.all(),
        'form_words': form_words,
        'form_files': form_files,
        'frame':frame 
      
    }

    
        
    return render(request, "upload.html", context)


