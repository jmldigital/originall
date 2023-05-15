import gzip
import re

from ..models import StopWords,AddFiles,Brands,OriginallBD
from dask.diagnostics import ProgressBar,ResourceProfiler
import time
from dask.delayed import delayed
from dask import dataframe as df1
import pandas as pd
import numpy as np
from pandas.api.types import union_categoricals
import os.path, shutil

def get_key(val,dic):
    for key, value in dic.items():
        if val == value:
            return key
    return "key doesn't exist"

fields = {
'oem_field':['код','Номер детали','артикль','artikel','nummer','id','sachnummer','zahl','number','article','nr','num','номер','артикул','DetailNum','ArtikelNr'],
'brend_field':['Производитель','makename','brand','preis','marke','hersteller','производитель','brend_field','бренд'],
'name_field':['Название','detailname','titel','title','название','bezde','Наименование'],
'weight_field':['Вес', 'weight','вес','кг','WeightKG'],
'volume_field':['Объем','volume','band','gewicht','umfang','lautstärke','volumen','VolumeKG','объем'] }

fields_add = {
'price_field':['price','cost','preis','цена','стоимость','DetailPrice'],
'quantity_field':['volume','menge','quantity','кол-во','количество','min','PackQuantity','мин'],
 }

fields_price = fields | fields_add


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
        # print('загружаем из бд',file,type(file))
        file_path = file
        try:
            file.split(".")[2]
            # print('extantions',file.split(".")[2])
            file = gzip.open(file, 'rb')
            first_line = next(file).decode('utf-8')

        except: 
            # print('extantions',file.split(".")[1])
            file= open(file_path, 'r', errors='ignore')
            first_line = file.readline()

    else:
        # print('загружаем из аплоадера',file,type(file))
        first = file.readline()
        first_line = first.decode('utf-8')
        file.seek(0)
    
    # print('first_line',first_line)
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
    # print('title',NewTitle)
    return NewTitle

# заголовки для csv и txt файлов
def heders(file,fields,delim):
    arr={}
# получаем заголовки из прайсов
    try:
        with open(file, 'r') as f:
            first_line = next(f).strip()
            header_list = first_line.split(delim)
    except:
        with gzip.open(file, 'rb') as f:
            first_line = next(f).strip()
            header_list = first_line.decode("utf-8").split(delim)


    for key in fields.keys():
        result=lowercomapre(fields[key],header_list)
        arr[key] = result
    
    
    for key in arr.copy():
        if not arr[key]:
            arr.pop(key)
    
    #Переименовываем заголовки фрейма на наши
    NewTitle = {v:k for k, v in arr.items()}
    # print('title',NewTitle)
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
            raw_data = pd.read_excel(file, usecols=dic.keys(), engine = engine_xls)
        
   
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
                # print('usecols',dic.keys())
                dfs = delayed(pd.read_csv(file, on_bad_lines='skip', encoding_errors='ignore', header=0, usecols=dic.keys(), dtype=dtypes_mono, sep=delimetr(file)))
                raw_data = df1.from_delayed(dfs)
                # print('this is raw_data',raw_data)
                raw_data['brend_field'] = OneFile.brend_field
                raw_data['brend_field'] = raw_data['brend_field'].astype('category')
            else:
                dfs = delayed(pd.read_csv(file, on_bad_lines='skip', encoding_errors='ignore', header=0, usecols=dic.keys(), dtype=dtypes, sep=delimetr(file)))
                raw_data = df1.from_delayed(dfs)            


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

