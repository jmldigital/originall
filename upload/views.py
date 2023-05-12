from django.shortcuts import render
import pandas as pd
import numpy as np
import os.path, shutil
import cgi
from .forms import StopWordsForm, FilesForm,BrandsForm,BrandsUploadForm
from .models import StopWords,AddFiles,Brands,OriginallBD

from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse,Http404
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, text
from sqlalchemy.orm import sessionmaker
import re
from django.http import JsonResponse
from django.core import serializers
from pandas import read_sql_query
from django.db.models import Q
from django.conf import settings
from django.views import generic
from dask import dataframe as df1
import time
from dask.diagnostics import ProgressBar,ResourceProfiler
from pandas.api.types import union_categoricals
# from pyheat import PyHeat
# from line_profiler import LineProfiler
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

    else:
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
    return delim


# заголовки для файлов экселя
def heders_xls(file,fields):
    arr={}
# получаем заголовки из прайсов
    header_list = pd.read_excel(file).columns
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

# заголовки для csv и txt файлов
def heders(file,fields,delim):
    arr={}
# получаем заголовки из прайсов
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

    words = StopWords.objects.values_list('words', flat=True).distinct()
    words_up=list(map(str.upper, words))
    brands = Brands.objects.values_list('brand', flat=True).distinct()
    brands_low = list(map(str.lower, brands))

    
    try:
        extension = file.split(".")[1]
    except:
        extension = cleaner(os.path.splitext(file.name)[1])
    
    if (extension == 'xls') or (extension == 'xlsx'):

        dic=heders_xls(file,dfcolumns)
        dtypes ={get_key('brend_field',dic):'category',
            get_key('name_field',dic):'category',
            get_key('oem_field',dic):'object'
                }
        
        dtypes_mono ={
            get_key('name_field',dic):'category',
            get_key('oem_field',dic):'object'
            }  

        if extension == 'xls':
            engine_xls=None
        if extension == 'xlsx':
            engine_xls='openpyxl'


        if OneFile.is_mono:
                raw_data = pd.read_excel(file, usecols=dic.keys(), engine = engine_xls, dtype=dtypes_mono)
                raw_data['brend_field'] = OneFile.brend_field
                raw_data['brend_field'] = raw_data['brend_field'].astype('category')
        else:
            raw_data = pd.read_excel(file, usecols=dic.keys(), engine = engine_xls, dtype=dtypes)

        

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

        ta = ts.loc[ts["brend_field"].str.lower().isin(brands_low)]

        new = ta.loc[~ta["name_field"].str.upper().isin(words_up)]

        new['oem_field'] = new['oem_field'].astype(str)      
        new['brend_field'] = new['brend_field'].str.lower()


    if (extension == 'txt') or (extension == 'csv'): 
        dic=heders(file,dfcolumns,delimetr(file))

        dtypes ={get_key('brend_field',dic):'category',
            get_key('name_field',dic):'category',
            get_key('oem_field',dic):'object'
                }
        
        dtypes_mono ={
            get_key('name_field',dic):'category',
            get_key('oem_field',dic):'object'
            }  

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

            ta = ts.loc[ts["brend_field"].str.lower().isin(brands_low)].compute()

            new = ta[~ta["name_field"].str.upper().isin(words_up)]

            new['brend_field'] = new['brend_field'].str.lower()
            e_time_dask = time.time()

            # print(new)

            print("Read with dask: utf-8 ", (e_time_dask-s_time_dask), "seconds")

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

    user = settings.DATABASES['default']['USER']
    password = settings.DATABASES['default']['PASSWORD']
    database_name = settings.DATABASES['default']['NAME']
    host_name = settings.DATABASES['default']['HOST']
    port = settings.DATABASES['default']['PORT']

    database_url = 'postgresql://{user}:{password}@{host_name}:{port}/{database_name}'.format( user=user,password=password,database_name=database_name,host_name=host_name,port=port)
    engine = create_engine(database_url, echo=False)

    if Curency == 'доллар':
       cur = 78.6
    if Curency == 'евро':
       cur = 87
    if Curency == 'рубль':
       cur = 1

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filepath_url = BASE_DIR + '/mediafiles/prices/'

    # вначале удаляем все файлы из прайсов папки
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
    

    BDdf = pd.read_sql_query('select * from "upload_originallbd"',con=engine)

    # conn = sqlite3.connect('db.sqlite3')        
    # sql_query = pd.read_sql_query ('''
    #                             SELECT
    #                             *
    #                             FROM upload_originallbd
    #                             ''', conn)
    

    # BDdf = pd.DataFrame(sql_query)

# удаляем id столбец из датафрейма бд
    BDdf.drop('id', axis= 1 , inplace= True )

# фильтруем по минимальному пакеджу в доставке прайсовый датафрейм
    pricefulldf = pricefulldf[pricefulldf['quantity_field']==1]
    pricefulldf['weight_field'] = pricefulldf['weight_field'].astype(float)

    if (pricefulldf['weight_field'].dtype == np.float64 or pricefulldf['weight_field'].dtype == np.int64):
        pass
    else:
        pricefulldf['price_field'] = pricefulldf['price_field'].str.replace(',', '.').astype('float64')

    if (pricefulldf['price_field'].dtype == object):
        pricefulldf['price_field'] = pricefulldf['price_field'].str.replace(',', '.').astype('float64')

# получаем готовый прайс из базы данных 
    PriseDf = BDdf.loc[((BDdf["weight_field"] != 0) & (BDdf["volume_field"] != 0)) & (BDdf["brend_field"].isin(pricefulldf['brend_field'])) & (BDdf["oem_field"].isin(pricefulldf['oem_field']))]

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

    pricedf_path = 'mediafiles/prices/'
    pricedf_name = price.split('.')[0]+'_create.csv'
    price_url = pricedf_path+pricedf_name
    
    # try:
    #     fin.to_csv(price_url, index = False,encoding='cp1251')
    # except:
    fin.to_csv(price_url, index = False)
    len = fin.shape[0]
    context = {
    'price':pricedf_name,
    'price_url':price_url,
    'len':len
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

# def words_asJson(request):
#     object_list = StopWords.objects.all() #or any kind of queryset
#     json = serializers.serialize('json', object_list)
#     return HttpResponse(json, content_type='application/json')


def brands_delete(request, id=None):   
    brand = Brands.objects.get(id=id)
    brand.delete()
    return JsonResponse({'success': True, 'message': 'Delete','id':id})   

# import atexit
# lp = LineProfiler()
# atexit.register(lp.print_stats)


# @lp
def bd_create(request):   
    s_time_dask = time.time()
    start_time = time.time()
    user = settings.DATABASES['default']['USER']
    password = settings.DATABASES['default']['PASSWORD']
    database_name = settings.DATABASES['default']['NAME']
    host_name = settings.DATABASES['default']['HOST']
    port = settings.DATABASES['default']['PORT']

    database_url = 'postgresql://{user}:{password}@{host_name}:{port}/{database_name}'.format( user=user,password=password,database_name=database_name,host_name=host_name,port=port)
    engine = create_engine(database_url, echo=False)

    # engine = create_engine('sqlite:///db.sqlite3')
    prices=AddFiles.objects.values_list('files', flat=True).distinct()
    DataFrames = []
    
    for price in prices:
        pricedf = converter("mediafiles/"+price,fields) 
        DataFrames.append(pricedf)

    result = concatenate(DataFrames)
    # result.to_csv('result.csv', index = False)

    # Убираем полные дубликаты из общего фрейма
    result.drop_duplicates(inplace=True)
    
    # Получаем все неполные дубликаты по оем
    dub_oem = result[(result[['oem_field']].duplicated(keep=False))]
    dub_oem.to_csv('mediafiles/csv/df_duble.csv', index = False)

    # Вынимаем из фрйма оставшиеся совпадения по оем
    result.drop_duplicates(subset = 'oem_field', inplace=True, keep=False)
    # result.to_csv('result.csv', index = False)

    # Получаем все дубликаты с полностью заполненными полями
    dub_oem_name_weight_vol = dub_oem[(dub_oem[['oem_field']].duplicated(keep=False)) & (dub_oem['weight_field'] > 0) & (dub_oem['volume_field'] > 0)]
    dub_oem_name_weight_vol.drop_duplicates(['oem_field','brend_field'], inplace=True)
    # dub_oem_name_weight_vol.to_csv('mediafiles/csv/dub_oem_name_weight_vol.csv', index = False)

    # Получаем все дубликаты с одним из заполненных полей
    dub_oem_null = dub_oem[(dub_oem[['oem_field']].duplicated(keep=False)) & ((dub_oem['weight_field'] == 0) | (dub_oem['volume_field'] == 0)) ]
    # dub_oem_null.to_csv('dub_oem_null.csv', index = False)

    # Мерджим между собой дубликаты с одним из заполненных полей
    group_null_merdge = dub_oem_null.groupby(by=['oem_field','brend_field'],as_index=False).agg({'name_field': 'first','weight_field': 'max','volume_field': 'max','brend_field': 'first'})
    # group_null_merdge.to_csv('mediafiles/csv/group_null_merdge.csv', index = False)
    
    # Соединяем смерженные с полными полями и оставляем максимальные
    finalDF = pd.concat([group_null_merdge, dub_oem_name_weight_vol],ignore_index=True)

    #функция для поиска минимального ненулевого значения
    get_min = lambda x: np.min(x) if np.min(x) > 0 else np.max(x)


    finalDF_ALL = finalDF.groupby(by=['oem_field','brend_field'],as_index=False).agg({'name_field': 'first','weight_field': get_min,'volume_field': 'max','brend_field': 'first'})
    # finalDF_ALL.to_csv('mediafiles/csv/finalDF_ALL.csv', index = False)

    FULL = pd.concat([finalDF_ALL, result],ignore_index=True)

    # проверяем если объем меньше массы
    FULL.loc[FULL['volume_field'] < FULL['weight_field'], 'volume_field'] = 0
    FULL.to_csv('mediafiles/csv/FULL.csv', index = False)

    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        FULL.to_sql(OriginallBD._meta.db_table, if_exists='replace', con=engine,   index=True, index_label='id')
        session.commit()
    except:
        session.rollback()
    finally:
        session.close()

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
    form = BrandsUploadForm(request.POST, request.FILES)
    brands = list(Brands.objects.values_list('brand', flat=True).distinct())

    user = settings.DATABASES['default']['USER']
    password = settings.DATABASES['default']['PASSWORD']
    database_name = settings.DATABASES['default']['NAME']
    host_name = settings.DATABASES['default']['HOST']
    port = settings.DATABASES['default']['PORT']

    database_url = 'postgresql://{user}:{password}@{host_name}:{port}/{database_name}'.format( user=user,password=password,database_name=database_name,host_name=host_name,port=port)
    engine = create_engine(database_url, echo=False)

    # engine = create_engine('sqlite:///db.sqlite3')

    if request.method == "POST":
        if form.is_valid():
            form = BrandsUploadForm(request.POST, request.FILES)
            brends = request.FILES['files']
            # form.save(commit=False)
            brendsdf = pd.read_excel(brends)
            brendsdf.columns=["brand"]

            brendsdf['files'] = None
            # print(brendsdf)
            # brendsdf.to_sql('brendss', if_exists='replace', index=True, index_label='id', con=engine2)
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
        len = OriginallBD.objects.all().count()
    except:
        len = 0

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
        'notation':notation
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
    


# def Words_update(request, pk):
#     words = StopWords.objects.get(id=pk)
#     form3 = StopWordsForm(instance=words )
#     if request.method == "POST":
#         form3 = StopWordsForm(request.POST,request.FILES,instance=words)
#         if form3.is_valid():
#             form3.save()
#             return redirect("/edit/4/")

#     context = {
#         "words": words,
#         "form": form3
#     }

#     return render(request, "upload.html", context)