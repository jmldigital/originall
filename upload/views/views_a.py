from django.shortcuts import render
import pandas as pd
import numpy as np
import pickle
import os.path, shutil
import cgi
from ..forms import StopWordsForm, FilesForm,BrandsForm,BrandsUploadForm
from ..models import StopWords,AddFiles,Brands,OriginallBD
import pyarrow as pa
import pyarrow.parquet as pq
import requests
from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse,Http404
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, text
from sqlalchemy.orm import sessionmaker
import time
from django.http import JsonResponse
from django.core import serializers
from pandas import read_sql_query
from django.db.models import Q
from django.conf import settings
from django.views import generic
from upload.views.converter import converter, fields,fields_price, concatenate,delimetr
from upload.views.filter import Dfilter
from dask.delayed import delayed
from dask import dataframe as df1

# from pyheat import PyHeat
# from line_profiler import LineProfiler
import mimetypes
# import sqlite3
# import pandasql
# import pysqldf
#python manage.py migrate --run-syncdb

pd.options.mode.chained_assignment = None

dtypes ={'brend_field':'category',
        'name_field':'category',
        'oem_field':'object'
        }


user = settings.DATABASES['default']['USER']
password = settings.DATABASES['default']['PASSWORD']
database_name = settings.DATABASES['default']['NAME']
host_name = settings.DATABASES['default']['HOST']
port = settings.DATABASES['default']['PORT']

database_url = 'postgresql://{user}:{password}@{host_name}:{port}/{database_name}'.format( user=user,password=password,database_name=database_name,host_name=host_name,port=port)
engine = create_engine(database_url, echo=False)

Mediafiles = settings.MEDIA_ROOT
filepath_price = str(Mediafiles)+"/prices"
filepath_csv = str(Mediafiles)+"/csv"
filepath_csv_bd = str(Mediafiles)+"/csv/FULL.csv"


def price_create(request, id=None):  
    price = AddFiles.objects.get(pk=id).files.name
    Curency = AddFiles.objects.get(pk=id).currency_field

    Valute = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()
    
    # print('dollar',Valute['Valute']['USD']['Value'],'euro',Valute['Valute']['EUR']['Value'])

    if Curency == 'доллар':
       cur = Valute['Valute']['USD']['Value']
    if Curency == 'евро':
       cur = Valute['Valute']['EUR']['Value']
    if Curency == 'рубль':
       cur = 1

 
    # вначале удаляем все файлы из прайсов папки
    folder = filepath_price
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

    pricefulldf = converter("mediafiles/"+price,fields_price)
    BDdf = pd.read_sql_query('select * from "upload_originallbd"',con=engine)
    BDdf.drop('id', axis= 1 , inplace= True )

# фильтруем по минимальному пакеджу в доставке прайсовый датафрейм
    if Curency != 'рубль':
        pricefulldf = pricefulldf[pricefulldf['quantity_field']==1]
    else:
        pricefulldf = pricefulldf[pricefulldf['quantity_field']!=0]

    pricefulldf['weight_field'] = pricefulldf['weight_field'].astype(float)

    if (pricefulldf['weight_field'].dtype == np.float64 or pricefulldf['weight_field'].dtype == np.int64):
        pass
    else:
        pricefulldf['price_field'] = pricefulldf['price_field'].str.replace(',', '.').astype('float64')

    if (pricefulldf['price_field'].dtype == object):
        pricefulldf['price_field'] = pricefulldf['price_field'].str.replace(',', '.').astype('float64')

# получаем готовый прайс из базы данных 
    if Curency != 'рубль':
        PriseDf = BDdf.loc[((BDdf["weight_field"] != 0) & (BDdf["volume_field"] != 0)) & (BDdf["brend_field"].isin(pricefulldf['brend_field'])) & (BDdf["oem_field"].isin(pricefulldf['oem_field']))]
    else:
        PriseDf = BDdf.loc[(BDdf["brend_field"].isin(pricefulldf['brend_field'])) & (BDdf["oem_field"].isin(pricefulldf['oem_field']))]


# добавляем к прайсу цену и мин кол-во
    fin = PriseDf.merge(pricefulldf, left_on=['brend_field', 'oem_field'], right_on=['brend_field', 'oem_field'])
    fin['price_field'] = fin['price_field']*cur
    fin['price_field'] = fin['price_field'].round(2)
# убираем лишние колонки и дубликаты по номеру и бренду
    fin.drop(['name_field_y','volume_field_y','weight_field_y'], axis= 1 , inplace= True )
    fin.drop_duplicates(['oem_field','brend_field'], inplace=True)

    # fin.rename(columns = {
    #     'oem_field':'номер', 
    #     'name_field_x':'название',
    #     'weight_field_x':'вес', 
    #     'volume_field_x':'объем', 
    #     'price_field':'цена', 
    #     'quantity_field':'кол-во',
    #     'brend_field':'бренд',
    #     }, inplace = True )

    fin.rename(columns = {
        'oem_field':'Nomber', 
        'name_field_x':'Name',
        'weight_field_x':'Weight', 
        'volume_field_x':'Volume', 
        'price_field':'Price', 
        'quantity_field':'Min',
        'brend_field':'Brand',
        }, inplace = True )

  
    pricedf_name = price.split('.')[0]+'_create.csv'
    price_url = filepath_price+'/'+pricedf_name
    
    # try:
    #     fin.to_csv(price_url, index = False,encoding='cp1251')
    # except:
    try:
        fin.to_csv(price_url, index = False, encoding='cp1251')
    except:
        fin.to_csv(price_url, index = False)

    len = fin.shape[0]
    context = {
    'price':pricedf_name,
    'price_url':price_url,
    'len':len
    }
    
    return  render(request, "prices.html",context)
 

def download(request):

    filename =os.listdir(filepath_price)[0]
    filepath = filepath_price +'/'+ filename
    path = open(filepath, 'r', encoding="utf8")
    mime_type, _ = mimetypes.guess_type(filepath)
    response = HttpResponse(path, content_type=mime_type)
    s = "attachment; filename=%s" % filename
    cr = s.encode(encoding = 'cp1251')
    response['Content-Disposition'] = cr
    return response
    

def file_delete(request, id=None):   
    file = AddFiles.objects.get(pk=id)
    file_name = AddFiles.objects.get(pk=id).files.name
    file.delete()
    filepath_url = settings.MEDIA_ROOT
    os.remove(str(filepath_url)+"/"+file_name)
    return JsonResponse({'success': True, 'message': 'Delete','id':id}) 


def BD_delete(request, id=None):   
    detail = OriginallBD.objects.get(id=id)
    detail.delete()
    return JsonResponse({'success': True, 'message': 'Delete','id':id}) 


class BD_update(generic.UpdateView):
    model = OriginallBD
    template_name = "bd_update.html"
    fields = '__all__'

    def get_success_url(self):
        return reverse("upload")
    
    # def get_queryset(self):
    #     context = super(BD_update, self).get_context_data()
    #     queryset = OriginallBD.objects.filter(name_field='kia')
    #     print('ddsfsdfdf',context)
    #     return queryset

    


def words_delete(request, id=None):   
    words = StopWords.objects.get(pk=id)
    words.delete()
    return JsonResponse({'success': True, 'message': 'Delete','id':id})  



def brands_delete(request, id=None):   
    brand = Brands.objects.get(id=id)
    brand.delete()
    return JsonResponse({'success': True, 'message': 'Delete','id':id})   



# @lp
def bd_create(request):   
    s_time_dask = time.time()
    start_time = time.time()

    prices=AddFiles.objects.values_list('files', flat=True).distinct()
    DataFrames = []
    
    for price in prices:
        pricedf = converter("mediafiles/"+price,fields) 
        DataFrames.append(pricedf)

    result = concatenate(DataFrames)
    # result.to_csv('result.csv', index = False)
    # Получаем датафрейм для текущей бд
    # with open('mediafiles/csv/data.pickle', 'rb') as f:
    #     Bdcsv = pickle.load(f)
    # dfs = delayed(pd.read_csv(filepath_csv_bd, on_bad_lines='skip', encoding_errors='ignore', header=0, dtype=dtypes, sep=delimetr(filepath_csv_bd)))
    # raw_data = df1.from_delayed(dfs)
    # Bdcsv = raw_data.compute()


    # Соединяем нашу бд с новыми загруженными прайсами
    try:
        Bd = pq.read_table('mediafiles/parquet/data.parquet')
        Bddf = Bd.to_pandas()
        Oldbd_newprice_arr = [result,Bddf]
    except:
        Oldbd_newprice_arr = [result]
    


    # Обновляем бд!
    BdupdateDF = concatenate(Oldbd_newprice_arr)
    FULL = Dfilter(BdupdateDF)

    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        FULL.to_sql(OriginallBD._meta.db_table, if_exists='replace', con=engine,  index=True, index_label='id')
        session.commit()
    except:
        session.rollback()
    finally:
        session.close()

    e_time_dask = time.time()

    print("calculate df ", (e_time_dask-s_time_dask), "seconds")


    render(request, "search_results.html")
    return redirect(request.META['HTTP_REFERER'])



def brands_create(request):
    form = BrandsUploadForm(request.POST, request.FILES)
    brands = list(Brands.objects.values_list('brand', flat=True).distinct())

    if request.method == "POST":
        if form.is_valid():
            form = BrandsUploadForm(request.POST, request.FILES)
            brends = request.FILES['files']
            # form.save(commit=False)
            brendsdf = pd.read_excel(brends)
            brendsdf.columns=["brand"]
            brendsdf['files'] = None
   
            brendsdf.to_sql(Brands._meta.db_table, if_exists='replace', index=True, index_label='id', con=engine)

            # with engine.connect() as con:
            #     con.execute('ALTER TABLE `Brands` ADD PRIMARY KEY (`ID`);')
            # # print(brendsdf)

            return redirect("brands-create")
        else:
            print('все грязно')
    context = {
        "form": form
    }   
    return render(request, "index.html", context)

 

def price_upload(request):
    context ={}
    frame=''

    form_files = FilesForm(request.POST,request.FILES)
    form_words = StopWordsForm(request.POST)
    form_brands = BrandsForm(request.POST or None)
    words = StopWords.objects.all()
    brands = Brands.objects.all()


    is_mono=False
    
    if request.method == "POST" and request.is_ajax and 'brend_field' in list(request.POST.keys()):
        form_files = FilesForm(request.POST or None, request.FILES)
        if form_files.is_valid():
            file = form_files.cleaned_data['files']
            files_str = form_files.cleaned_data['files'].name
            brend_field = form_files.cleaned_data['brend_field']
            currency_field = form_files.cleaned_data['currency_field']
            instance = form_files.save(commit=False)

            if brend_field != None:
                is_mono=True

            newfiles = AddFiles.objects.create(
            files=file,
            brend_field=brend_field,
            currency_field = currency_field,
            is_mono = is_mono
            )

            data = {'pk':newfiles.pk, 'brend_field': brend_field, 'currency_field': currency_field}
            ser_instance = serializers.serialize('json', [ instance, ])
            # print('это сериализация прайсов',data)
            return JsonResponse({"instance": ser_instance,'data':data}, status=200)
        else:
            # print('форма не валидная',form_files.errors)
            # some form errors occured.
            return JsonResponse({"error": form_files.errors}, status=404)

        return JsonResponse({"error": ""}, status=400)  

    if request.method == "POST" and request.is_ajax and 'words' in list(request.POST.keys()):
        form_words = StopWordsForm(request.POST or None)
        if form_words.is_valid():
            instance = form_words.save()
            ser_instance = serializers.serialize('json', [ instance, ])
            return JsonResponse({"instance": ser_instance}, status=200)
        else:
            # some form errors occured.
            return JsonResponse({"error": form_words.errors}, status=400)
        print('не аякс')
        return JsonResponse({"error": ""}, status=400)   
         

    if request.method == "POST" and request.is_ajax and 'brand' in list(request.POST.keys()): 
        # brand_last = list(Brands.objects.values_list("id", flat=True).order_by("id"))[- 1] + 1
        # print(list(request.POST.keys()), 'аякс бренды')
        form_brands = BrandsForm(request.POST or None)
        if form_brands.is_valid():
            instance = form_brands.save()
            ser_instance2 = serializers.serialize('json', [ instance, ])
            return JsonResponse({"instance": ser_instance2}, status=200)
        else:
            # some form errors occured.
            return JsonResponse({"error": form_brands.errors}, status=400)
        return JsonResponse({"error": ""}, status=400)  
    
    if request.method == "GET": 
        query = request.GET.get('q', None)
        if query:
            object_list = OriginallBD.objects.filter(
                Q(oem_field__icontains=query) | Q(name_field__icontains=query)
            )
        else:
            object_list = OriginallBD.objects.filter(pk=1)    


    try:
        lenPrice = AddFiles.objects.all().count()
    except:
        lenPrice = None    

    try:
        len = OriginallBD.objects.all().count()
    except:
        len = 0

    print('длинна бд',len)

    if len == None:
        notation = "не сформированна"
    else:
        notation = "сформированна"

    context = {
        'files':AddFiles.objects.all(),
        'form_words': form_words,
        'form_files': form_files,
        'form_brands': form_brands,
        'frame':frame,
        'words':words,
        'brands':brands,
        'BD':object_list,
        'len':len,
        'notation':notation,
        'lenPrice':lenPrice
    }
          
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
    