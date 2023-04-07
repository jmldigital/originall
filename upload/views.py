from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
import pandas as pd
#import numpy as np
import os.path
from mechanize import Browser
import cgi
from .forms import StopWordsForm, FilesForm,BrandsForm,FileFieldForm
from .models import StopWords,AddFiles,Brands
from django.views import generic
from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse
from sqlalchemy import create_engine




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

def words_delete(request, id=None):   
    words = StopWords.objects.get(pk=id)
    words.delete()
    return redirect("/")  

def brands_delete(request, id=None):   
    brand = Brands.objects.get(brand_id=id)
    brand.delete()
    return redirect("/")  


def brands_create(request):
    form = BrandsForm(request.POST, request.FILES)
    engine = create_engine('sqlite:///db.sqlite3')

    if request.method == "POST":
        if form.is_valid():
            form = BrandsForm(request.POST, request.FILES)
            brends = request.FILES['files']
            # form.save(commit=False)
            brendsdf = pd.read_excel(brends)
            brendsdf.columns=["brand"]
            brendsdf['files'] = None
            brendsdf.to_sql(Brands._meta.db_table, if_exists='replace', con=engine, index=True, index_label='brand_id')
            # print(brendsdf)
            return redirect("brands-create")
        else:
            print('все грязно')
    context = {
        "form": form
    }   
    return render(request, "index.html", context)

 

def image_upload(request):
    context ={}
    arr=[]
    tit={}
    frame=''
    html_str = ''
    r=[]


    form_files = FilesForm(request.POST,request.FILES)
    form_words = StopWordsForm(request.POST)
    form_brands = BrandsForm(request.POST or None)
    words = StopWords.objects.all()
    brands = Brands.objects.all()
    # print('sdfsdfdf',brands)


    if request.method == "POST" and 'btnform2' in request.POST:
        if form_files.is_valid():
            file = form_files.cleaned_data['files']
            # print(file)
            form_files = FilesForm(request.POST or None, request.FILES)
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
                    tit[key] = '------------'   

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

        else:
            # print('все плохо') 
            return redirect("/")  
                

    if request.method == "POST" and 'btnform1' in request.POST:
        # print('слова записываются')
        form_words = StopWordsForm(request.POST or None)
        StopWords.objects.create(words = request.POST['words'])
        form_words.save(commit=False)
        return redirect("/")   
        

    if request.method == "POST" and 'btnform3' in request.POST:
        form_brands = BrandsForm(request.POST or None)

        # brand_l = list(Brands.objects.values_list("brand_id", flat=True).order_by("brand_id"))
        brand_last = list(Brands.objects.values_list("brand_id", flat=True).order_by("brand_id"))[- 1] + 1

        Brands.objects.create(
            
            brand = request.POST['brand'],
            brand_id = brand_last
        )
        form_brands.save(commit=False)
        return redirect("/")  

#------------------------Добавляем фйлы-------------------------------------------
    # if request.method == "POST":
    #     form_files = FilesForm(request.POST or None, request.FILES)
    #     # words = StopWords.objects.get(id=1)
    #     if form_files.is_valid():
    #         print('все ок')
    #         form_files.save()
    #     else:
    #         print('все плохо')  

            # words.words = words
            # words.save()

            # file = form_files.cleaned_data['files']
            # files_str = form_files.cleaned_data['files'].name
            # extension = files_str.split(".")[1]
            # if extension == 'xls':
            #     anime = pd.read_excel(file)
            #     for title in anime.columns.tolist():
            #         for key in fields.keys():
            #             if any(ext in title.lower() for ext in fields[key]):
            #                 arr.append(title)
            #                 tit[key]=title

            # anime_cleare = anime[arr] 
            # for key in fields.keys():  
            #     if key in tit.keys():
            #         print('')
            #     else:
            #         tit[key] = 'ничего'   

            # # print(tit)
            # # print(tit["brend_field"])
            
            # AddFiles.objects.create(
            # files=file,
            # oem_field=tit['oem_field'],
            # brend_field=tit['brend_field'],
            # name_field=tit['name_field'],
            # weight_field=tit['weight_field'],
            # volume_field=tit['volume_field'],

            # )
           
            # frame = anime_cleare.to_html('upload/templates/filename.html')
            # frame = anime_cleare.to_html()
            # r.append(frame)

            # ff=render(request, frame)
            # print(HttpResponse(frame))
  
            # print(frame)
            # HttpResponse(frame, headers={'Content-Type': 'text/html'})
            # form_files.save()
            # return redirect("/")  


    # mytextfield = "".join(frame.split())
    # print('nen',frame)
    context = {
        'files':AddFiles.objects.all(),
        'form_words': form_words,
        'form_files': form_files,
        'form_brands': form_brands,
        'frame':frame,
        'words':words,
        'brands':brands 
      
    }

    # print(context['brands'])

    
        
    return render(request, "upload.html", context)






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


