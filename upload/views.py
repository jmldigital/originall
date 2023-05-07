from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
import pandas as pd
import numpy as np
import os.path, shutil

from mechanize import Browser
import cgi
from .forms import StopWordsForm, FilesForm,BrandsForm,FileFieldForm
from .models import StopWords,AddFiles,Brands,OriginallBD
from django.views import generic
from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse,Http404
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, text
import re
from django.http import JsonResponse
from django.core import serializers
from django.views.generic.edit import FormView
from .forms import FileFieldForm
from pandas import read_sql_query
from django.db.models import Q
from django.conf import settings
from django.views.generic import TemplateView, ListView
from dask import dataframe as df1
import time
from dask.diagnostics import ProgressBar,ResourceProfiler
from memory_profiler import profile
from pandas.api.types import union_categoricals
# from pyheat import PyHeat
from line_profiler import LineProfiler
import mimetypes
import sqlite3

# import pandasql
# import pysqldf

#python manage.py migrate --run-syncdb

pd.options.mode.chained_assignment = None

def get_key(val,dic):

    for key, value in dic.items():
        if val == value:
            return key
 
    return "key doesn't exist"

fields = {
'oem_field':['Номер детали','артикль','artikel','nummer','id','sachnummer','zahl','number','article','nr','num','номер','артикул','DetailNum','ArtikelNr'],
'brend_field':['Производитель','makename','brand','preis','marke','hersteller','производитель','brend_field'],
'name_field':['Название','detailname','titel','title','название','bezde'],
'weight_field':['Вес', 'weight','вес','кг','WeightKG'],
'volume_field':['Объем','volume','band','gewicht','umfang','lautstärke','volumen','VolumeKG','объем'] }

fields_price = {
'oem_field':['Номер детали','артикль','artikel','nummer','id','sachnummer','zahl','number','article','nr','num','номер','артикул','DetailNum','ArtikelNr'],
'price_field':['price','cost','preis','цена','стоимость','DetailPrice'],
'brend_field':['Производитель','makename','brand','preis','marke','hersteller','производитель','brend_field'],
'name_field':['Название','detailname','titel','title','название','bezde'],
'quantity_field':['volume','menge','quantity','кол-во','количество','min','PackQuantity'],
'weight_field':['Вес', 'weight','вес','кг','WeightKG'],
'volume_field':['Объем','volume','band','gewicht','umfang','lautstärke','volumen','VolumeKG','объем'] }



try:
    words = StopWords.objects.values_list('words', flat=True).distinct()
    words_up=list(map(str.upper, words))
    brands = Brands.objects.values_list('brand', flat=True).distinct()
    brands_low = list(map(str.lower, brands))
    brands_up = list(map(str.upper, brands))
except:
    pass


sumdf = pd.DataFrame(index = fields.keys())


def concatenate(dfs):
    """Concatenate while preserving categorical columns.
    NB: We change the categories in-place for the input dataframes"""
    # Iterate on categorical columns common to all dfs
    for col in set.intersection(
        *[
            set(df.select_dtypes(include='category').columns)
            for df in dfs
        ]
    ):
        # Generate the union category across dfs for this column
        uc = union_categoricals([df[col] for df in dfs])
        # Change to union category for all dataframes
        for df in dfs:
            df[col] = pd.Categorical(df[col].values, categories=uc.categories)
    return pd.concat(dfs)


def lowercomapre(list1,list2):
    dif=''
    d = [x.lower() for x in list1] # make dict of list with less elements  
    for m in list2:  # search against bigger list  
        if m.lower() in d: 
            dif = m
    return dif

def cleaner(string):
    reg = re.compile('[^a-zA-Z ]')
    return reg.sub('', string)

def delimetr(file):
    
    if type(file) == str:
        # print('загружаем из бд',file)
        file_path = file
        file= open(file_path, 'r', errors='ignore')
        first_line = file.readline()
        # first = file.readline()
        # first_line = first.decode('utf-8')
        # file.seek(0)

    else:
        # print("загружаем из формы",file)
        first = file.readline()
        first_line = first.decode('utf-8')
        file.seek(0)

    match = re.search(r'(\W+)', first_line)
    if match.group(0) =='\t':
        delim = '\t'
        # print("разделитель таб",delim)
    else:
        delim =match.group(0)
        # print("разделитель:",delim) 
        # file.seek(0)
    return delim

def heders(file,fields,delim):
    arr={}

    with open(file, 'r') as f:
        first_line = next(f).strip()
    header_list = first_line.split(delim)

    for key in fields.keys():
        result=lowercomapre(fields[key],header_list)
        arr[key] = result
    
    for key in arr.copy():
        if not arr[key]:
            arr.pop(key)

    #Переименовываем заголовки фрейма на наши
    NewTitle = {v:k for k, v in arr.items()}
    # print(NewTitle)
    return NewTitle


def converter(file,dfcolumns):

    key = file.split('/')[1]
    OneFile = AddFiles.objects.get(files=key)

    dic=heders(file,dfcolumns,delimetr(file))

    # print(dic)

    # dtypes_price ={get_key('brend_field',dic):'category',
    #         get_key('name_field',dic):'category',
    #         get_key('oem_field',dic):'object',
    #         get_key('quantity_field',dic):'int64',
    #         }

    dtypes ={get_key('brend_field',dic):'category',
            get_key('name_field',dic):'category',
            get_key('oem_field',dic):'object'
            }
    
    dtypes_mono ={
        get_key('name_field',dic):'category',
        get_key('oem_field',dic):'object'
  
        }
    
    try:
        extension = file.split(".")[1]
    except:
        extension = cleaner(os.path.splitext(file.name)[1])

    df = ''
 
    if extension == 'xls':
        df = pd.read_excel(file,dtype = str)
        for title in df.columns.tolist():
            df.rename(columns = {title:cleaner(title)}, inplace = True, )
    if extension == 'xlsx':
        df =pd.read_excel(file, engine='openpyxl',dtype = str)
        for title in df.columns.tolist():
            df.rename(columns = {title:cleaner(title)}, inplace = True, )
    if (extension == 'txt') or (extension == 'csv'):  

        with ProgressBar(), ResourceProfiler(dt=0.25) as rprof:
            s_time_dask = time.time()

            if OneFile.is_mono:
                raw_data = df1.read_csv(file, on_bad_lines='skip', encoding_errors='ignore', header=0, usecols=dic.keys(), dtype=dtypes_mono, sep=delimetr(file))
                raw_data['brend_field'] = OneFile.brend_field
                raw_data['brend_field'] = raw_data['brend_field'].astype('category')
            else:
                raw_data = df1.read_csv(file, on_bad_lines='skip', encoding_errors='ignore', header=0, usecols=dic.keys(), dtype=dtypes, sep=delimetr(file))

            tt=raw_data.rename(columns = dic)
            ts= tt.dropna(subset=['name_field', "brend_field"])

            if 'volume_field' in ts.columns.tolist():
                pass
            else:
                ts['volume_field'] = 0

            if 'weight_field' in ts.columns.tolist():
                pass
            else:
                ts['weight_field'] = 0

            if (ts['weight_field'].dtype == np.float64 or ts['weight_field'].dtype == np.int64):
                pass
            else:
                ts['weight_field'] = ts['weight_field'].str.replace(',', '.').astype('float64')

            if (ts['volume_field'].dtype == np.float64 or ts['volume_field'].dtype == np.int64):
                pass
            else:
                ts['volume_field'] = ts['volume_field'].str.replace(',', '.').astype('float64')

            # new = ts.loc[((ts["weight_field"] != 0) | (ts["volume_field"] != 0)) & (ts["brend_field"].str.lower().isin(brands_low))].compute()
            new = ts.loc[ts["brend_field"].str.lower().isin(brands_low)].compute()

            new['brend_field'] = new['brend_field'].str.lower()
            # print(new.info())

            # ddf = raw_data.to_parquet("mediafiles/park", engine="pyarrow", schema=None)
            # new=df1.read_parquet('mediafiles/park' ).compute()

            # WordsFilter = BrandsFilter[~BrandsFilter['name_field'].isin(words_up)] 
            e_time_dask = time.time()

            print("Read with dask: utf-8 ", (e_time_dask-s_time_dask), "seconds")
        # rprof.visualize()
    # print(headders)
    return new   


# def price_load(request, id=None):   
#     file = AddFiles.objects.get(pk=id)
#     OTVET = JsonResponse({'success': True, 'message': 'POST','id':id})
#     print('fgdgfdgdg',OTVET)
#     # OTVET = JsonResponse({'success': True, 'message': 'POST','id':id})
#     # print('dfdfdfdfdf')     
#     # redirect(request.META['HTTP_REFERER']) 
#     return  JsonResponse({'success': True, 'message': 'POST','id':id})


def price_create(request, id=None):  

    price = AddFiles.objects.get(pk=id).files.name

    Curency = AddFiles.objects.get(pk=id).currency_field

    if Curency == 'доллар':
       cur = 78.6
    if Curency == 'евро':
       cur = 87
    if Curency == 'рубль':
       cur = 1



    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filepath_url = BASE_DIR + '/mediafiles/prices/'

    folder = filepath_url
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


    conn = sqlite3.connect('db.sqlite3')        
    sql_query = pd.read_sql_query ('''
                                SELECT
                                *
                                FROM upload_originallbd
                                ''', conn)
    BDdf = pd.DataFrame(sql_query)

    BDdf.drop('id', axis= 1 , inplace= True )

    pricefulldf = pricefulldf[pricefulldf['quantity_field']==1]

    pricefulldf['weight_field'] = pricefulldf['weight_field'].astype(float)

    if (pricefulldf['weight_field'].dtype == np.float64 or pricefulldf['weight_field'].dtype == np.int64):
        pass
    else:
        pricefulldf['price_field'] = pricefulldf['price_field'].str.replace(',', '.').astype('float64')

    if (pricefulldf['price_field'].dtype == object):
        pricefulldf['price_field'] = pricefulldf['price_field'].str.replace(',', '.').astype('float64')


    # print(pricefulldf['price_field'].dtype)

    PriseDf = BDdf.loc[((BDdf["weight_field"] != 0) & (BDdf["volume_field"] != 0)) & (BDdf["brend_field"].isin(pricefulldf['brend_field'])) & (BDdf["oem_field"].isin(pricefulldf['oem_field']))]


    # fin = PriseDf.merge(pricefulldf.rename(columns={'brend_field': 'brend','oem_field': 'oem'}), how='left', on=['oem_field','brend_field'])

    fin = PriseDf.merge(pricefulldf, left_on=['brend_field', 'oem_field'], right_on=['brend_field', 'oem_field'])
    fin['price_field'] = fin['price_field']*cur

    fin['price_field'] = fin['price_field'].round(2)

 

    fin.drop(['name_field_y','volume_field_y','weight_field_y'], axis= 1 , inplace= True )

    fin.drop_duplicates(['oem_field','brend_field'], inplace=True)

    fin.rename(columns = {
        'oem_field':'номер', 
        'name_field_x':'название',
        'weight_field_x':'вес', 
        'volume_field_x':'объем', 
        'price_field':'цена', 
        'quantity_field':'кол-во',
        'brend_field':'бренд',
        }, inplace = True )



    print(fin)

    pricedf_path = 'mediafiles/prices/'
    pricedf_name = price.split('.')[0]+'_create.csv'
    price_url = pricedf_path+pricedf_name
    fin.to_csv(price_url, index = False)

    context = {
    'price':pricedf_name,
    'price_url':price_url
    }
    
    return  render(request, "prices.html",context)

    

def download(request):

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filepath_url = BASE_DIR + '/mediafiles/prices/'
    filename =os.listdir(filepath_url)[0]
    filepath = BASE_DIR + '/mediafiles/prices/' + filename
    path = open(filepath, 'r')
    mime_type, _ = mimetypes.guess_type(filepath)
    response = HttpResponse(path, content_type=mime_type)
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    return response
    



def file_delete(request, id=None):   
    file = AddFiles.objects.get(pk=id)
    file_name = AddFiles.objects.get(pk=id).files.name
    file.delete()
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filepath_url = BASE_DIR + '/mediafiles/'
    os.remove(filepath_url+file_name)

    return JsonResponse({'success': True, 'message': 'Delete','id':id}) 

def words_delete(request, id=None):   
    words = StopWords.objects.get(pk=id)
    words.delete()
    return JsonResponse({'success': True, 'message': 'Delete','id':id})  

# def words_asJson(request):
#     object_list = StopWords.objects.all() #or any kind of queryset
#     json = serializers.serialize('json', object_list)
#     return HttpResponse(json, content_type='application/json')



def brands_delete(request, id=None):   
    brand = Brands.objects.get(id=id)
    brand.delete()
    return JsonResponse({'success': True, 'message': 'Delete','id':id})   

import atexit
lp = LineProfiler()
atexit.register(lp.print_stats)



# ph = PyHeat('D:/django-on-docker/app/upload/views.py')
fp = open("report.log", "w+")
# @profile(stream = fp)
# @lp
def bd_create(request):   
    # ph.create_heatmap()
    s_time_dask = time.time()
    # BD = OriginallBD.objects.all()
    start_time = time.time()

    files = AddFiles.objects.all()

    user = settings.DATABASES['default']['USER']
    password = settings.DATABASES['default']['PASSWORD']
    database_name = settings.DATABASES['default']['NAME']

    # database_url = 'postgresql://{user}:{password}@localhost:5432/{database_name}'.format( user=user,password=password,database_name=database_name,)
    # engine = create_engine(database_url, echo=False)

    engine = create_engine('sqlite:///db.sqlite3')

    prices=AddFiles.objects.values_list('files', flat=True).distinct()

    DataFrames = []
    
    for price in prices:
        #Получаем датафрейм      
        pricedf = converter("mediafiles/"+price,fields) 
        # print('before',pricedf.info())
        DataFrames.append(pricedf)

    result = concatenate(DataFrames)

    # Убираем полные дубликаты из общего фрейма
    result.drop_duplicates(inplace=True)
    
    # Получаем все неполные дубликаты по оем
    dub_oem = result[(result[['oem_field']].duplicated(keep=False))]
    dub_oem.to_csv('df_duble.csv', index = False)

    # Вынимаем из фрйма оставшиеся совпадения по оем
    result.drop_duplicates(subset = 'oem_field', inplace=True, keep=False)
    # result.to_csv('result.csv', index = False)

    # Получаем все дубликаты с полностью заполненными полями
    dub_oem_name_weight_vol = dub_oem[(dub_oem[['oem_field']].duplicated(keep=False)) & (dub_oem['weight_field'] > 0) & (dub_oem['volume_field'] > 0)]
    dub_oem_name_weight_vol.drop_duplicates(['oem_field','brend_field'], inplace=True)
    # dub_oem_name_weight_vol.to_csv('dub_oem_name_weight_vol.csv', index = False)

    # Получаем все дубликаты с одним из заполненных полей
    dub_oem_null = dub_oem[(dub_oem[['oem_field']].duplicated(keep=False)) & ((dub_oem['weight_field'] == 0) | (dub_oem['volume_field'] == 0)) ]
    # dub_oem_null.to_csv('dub_oem_null.csv', index = False)

    # Мерджим между собой
    group_null_merdge = dub_oem_null.groupby(by=['oem_field','brend_field'],as_index=False).agg({'name_field': 'first','weight_field': 'max','volume_field': 'max','brend_field': 'first'})
    # group_null_merdge.to_csv('group_null_merdge.csv', index = False)
    
    # Соединяем смерженные с полными полями и оставляем максимальные
    finalDF = pd.concat([group_null_merdge, dub_oem_name_weight_vol],ignore_index=True)
    finalDF_ALL = finalDF.groupby(by=['oem_field','brend_field'],as_index=False).agg({'name_field': 'first','weight_field': 'max','volume_field': 'max','brend_field': 'first'})

    FULL = pd.concat([finalDF_ALL, result],ignore_index=True)

    # проверяем если объем меньше массы
    FULL.loc[FULL['volume_field'] < FULL['weight_field'], 'volume_field'] = 0
    FULL.to_csv('FULL.csv', index = False)

    FULL.to_sql(OriginallBD._meta.db_table, if_exists='replace', con=engine,   index=True, index_label='id')

 
    e_time_dask = time.time()

    print("calculate df ", (e_time_dask-s_time_dask), "seconds")
    render(request, "search_results.html")
    return redirect(request.META['HTTP_REFERER'])


# class SearchResultsView(ListView):
#     model = OriginallBD
#     template_name = 'search_results.html'
 
#     def get_queryset(self): # новый
#         query = self.request.GET.get('q')
#         object_list = OriginallBD.objects.filter(
#             Q(brend_field__icontains=query) | Q(name_field__icontains=query)
#         )
#         return object_list


def brands_create(request):
    form = BrandsForm(request.POST, request.FILES)
    brands = list(Brands.objects.values_list('brand', flat=True).distinct())
    brands_old = pd.DataFrame(brands)

    user = settings.DATABASES['default']['USER']
    password = settings.DATABASES['default']['PASSWORD']
    database_name = settings.DATABASES['default']['NAME']

    # database_url = 'postgresql://{user}:{password}@localhost:5432/{database_name}'.format( user=user,password=password,database_name=database_name,)
    # engine = create_engine(database_url, echo=False)

    engine = create_engine('sqlite:///db.sqlite3')

    if request.method == "POST":
        if form.is_valid():
            form = BrandsForm(request.POST, request.FILES)
            brends = request.FILES['files']
            # form.save(commit=False)
            brendsdf = pd.read_excel(brends)
            brendsdf.columns=["brand"]

            brendsdf['files'] = None
            # print(brendsdf)
            # brendsdf.to_sql('brendss', if_exists='replace', index=True, index_label='id', con=engine2)
            brendsdf.to_sql(Brands._meta.db_table, if_exists='append', index=True, index_label='id', con=engine)

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
    # BD = OriginallBD.objects.all()
    is_mono=False
    # print('sdfsdfdf',brands)


    # print(list(request.POST.keys()), 'ПРОСТОЙ ЗАПРОС')
    
    if request.method == "POST" and request.is_ajax and 'brend_field' in list(request.POST.keys()):
        form_files = FilesForm(request.POST or None, request.FILES)
        # print(list(request.POST.keys()), 'аякс прайсы')
        if form_files.is_valid():
            file = form_files.cleaned_data['files']
            files_str = form_files.cleaned_data['files'].name
            brend_field = form_files.cleaned_data['brend_field']
            currency_field = form_files.cleaned_data['currency_field']
            instance = form_files.save(commit=False)
            # print('dct jr',instance)

            if brend_field != None:
                is_mono=True


            # print(';nj nbn',tit)

            newfiles = AddFiles.objects.create(
            files=file,
            brend_field=brend_field,
            currency_field = currency_field,
            is_mono = is_mono
            )
             # newfiles.is_mono = True

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
        # print(list(request.POST.keys()), 'аякс стоп слова')
        form_words = StopWordsForm(request.POST or None)
        if form_words.is_valid():
            instance = form_words.save()
            ser_instance = serializers.serialize('json', [ instance, ])
            # print("сериализованные слова",ser_instance)
            return JsonResponse({"instance": ser_instance}, status=200)
        else:
            # some form errors occured.
            return JsonResponse({"error": form_words.errors}, status=400)
        
        # StopWords.objects.create(words = request.POST['words'])
        # form_words.save(commit=False)
        print('не аякс')
        return JsonResponse({"error": ""}, status=400)   
         

    if request.method == "POST" and request.is_ajax and 'brand' in list(request.POST.keys()): 
        # brand_last = list(Brands.objects.values_list("id", flat=True).order_by("id"))[- 1] + 1
        # print(list(request.POST.keys()), 'аякс бренды')
        form_brands = BrandsForm(request.POST or None)
        if form_brands.is_valid():
            instance = form_brands.save()
            ser_instance2 = serializers.serialize('json', [ instance, ])
            # print(ser_instance2)
            return JsonResponse({"instance": ser_instance2}, status=200)
        else:
            # some form errors occured.
            return JsonResponse({"error": form_brands.errors}, status=400)
        
        return JsonResponse({"error": ""}, status=400)  
    
    if request.method == "GET": 
        query = request.GET.get('q', None)
        if query:
            # print('yes',query)
            object_list = OriginallBD.objects.filter(
                Q(brend_field__icontains=query) | Q(name_field__icontains=query)
            )
        else:
            # print('none',query)
            object_list = OriginallBD.objects.filter(pk=1)    

    context ={'BD':object_list}


    context = {
        'files':AddFiles.objects.all(),
        'form_words': form_words,
        'form_files': form_files,
        'form_brands': form_brands,
        'frame':frame,
        'words':words,
        'brands':brands,
        'BD':object_list,
      
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


