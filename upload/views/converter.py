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
import chardet
from openpyxl import load_workbook

def get_key(val,dic):
    for key, value in dic.items():
        if val == value:
            return key
    return "key doesn't exist"


def decoder(file):
    enc = chardet.detect(open(file, 'rb').read())
    # print(enc['encoding'])
    return enc['encoding']


fields = {
'oem_field':[1,'1','код','Номер детали','артикль','artikel','nummer','id','sachnummer','zahl','number','article','nr','num','номер','артикул','DetailNum','ArtikelNr'],
'brend_field':[3,'3','Производитель','makename','brand','preis','marke','hersteller','производитель','brend_field','бренд','фирма'],
'name_field':[2,'2','Название','detailname','titel','title','название','bezde','Наименование','Наименование товара','Номенклатура'],
'weight_field':[6,'6','Вес', 'weight','вес','кг','WeightKG'],
'volume_field':['7,7','Объем','volume','band','gewicht','umfang','lautstärke','volumen','VolumeKG','объем'] }

fields_add = {
'price_field':[5,'5','price','cost','preis','цена','стоимость','DetailPrice','руб'],
'quantity_field':[4,'4','volume','menge','quantity','кол-во','количество','min','PackQuantity','мин','остаток'],
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
    d = [str(x).lower() for x in list1] # make dict of list with less elements  
    for m in list2:  # search against bigger list  
        if str(m).lower() in d: 
            dif = str(m)
    return dif

def cleaner(string):
    reg = re.compile('[^a-zA-Z ]')
    return reg.sub('', string)



class PriceDf:

    # Способ создания объекта (конструктор)
    def __init__(self, file):   
        

        self.ext = file.split(".")[-1]
        key = file.split('/')[1]
        OnePrice = AddFiles.objects.get(files=key)
        self.cur = OnePrice.currency_field
        self.mono = OnePrice.is_mono
        self.headers = self.get_headers_method(file)
        # self.encoding = self.get_encoding_method(file)
        self.fields = fields
        # self.usercol = self.get_usecols().keys()
        # self.dtypes = self.get_dtypes()
        # self.clean = self.get_clean(file,fields)
        # print("входные", self.fields)


    def get_headers_method(self,file):
        if self.ext == 'gz':
            headers_method = self.get_heders_gzip(file)
        if self.ext == 'csv':
            headers_method = self.get_heders(file)    
        if self.ext == 'txt':
            headers_method = self.get_heders(file)
        if self.ext == 'xls':
            headers_method = self.get_heders_xls(file)
        if self.ext == 'xlsx':
            headers_method = self.get_heders_xls(file)
        return headers_method
    

    def get_encoding_method(self,file):
        if self.cur == 'рубль':
            encoding_method = decoder(file)
        if self.cur == 'доллар':
            encoding_method = None
        if self.cur == 'евро':
            encoding_method = None           
        return encoding_method


    def get_delim_method(self,file):
        if self.ext == 'gz':
            delim_method = self.get_delim_gzip(file)
        else:
            delim_method = self.get_delim(file)
        return delim_method
    

    def get_delim_gzip(self,file):
        file = gzip.open(file, 'rb')
        first_line = next(file).decode('utf-8')
        match = re.search(r'(\W+)', first_line)
        if match.group(0) =='\t':
            delim = '\t'
            # print("разделитель таб",delim)
        else:
            delim =match.group(0)
            # print("разделитель у гзипа:",delim) 
        return delim 
    
    
    def get_delim(self,file):   
        file = open(file, 'r', errors='ignore', encoding=self.get_encoding_method(file))
        first_line = file.readline()
        match = re.search(r'(\W+)', first_line)
        if match.group(0) =='\t':
            delim = '\t'
            # print("разделитель таб",delim)
        else:
            delim =match.group(0)
            # print("разделитель у csv:",delim) 
        return delim 
    
    
    def get_heders(self,file): 
        with open(file, 'r',encoding=self.get_encoding_method(file)) as f:
            first_line = next(f).strip()
            delim = self.get_delim(file)
            header_list = first_line.split(delim)
            # print('header_list у csv',header_list)
            return header_list      


    def get_heders_gzip(self,file): 
        with gzip.open(file, 'rb') as f:
            first_line = next(f).strip()
            delim = self.get_delim_gzip(file)
            header_list = first_line.decode('utf-8').split(delim)
            # print('header_list у г зипа',header_list)
            return header_list
        

    def get_heders_xls(self,file): 
            header_list = pd.read_excel(file).columns
            return header_list
    

    def get_fields(self): 
        arr={}
        for key in self.fields.keys():
            result=lowercomapre(self.fields[key],self.headers)
            arr[key] = result       
        for key in arr.copy():
            if not arr[key]:
                arr.pop(key)
        #Переименовываем заголовки фрейма на наши
        NewTitle = {v:k for k, v in arr.items()}
        # print('title первонах',NewTitle)
        return NewTitle

    def get_usecols(self):
        usecols=self.get_fields()
        # print('usecols',usecols)
        return usecols

    def get_dtypes(self):
        dic = self.get_usecols()
        if self.mono:
            dtypes={
            get_key('name_field',dic):'category',
            get_key('oem_field',dic):'object'
            }
        else: 
            dtypes ={get_key('brend_field',dic):'category',
                     get_key('name_field',dic):'category',
                     get_key('oem_field',dic):'object'
                }
        return dtypes
    

    def get_exel_engine(self):
        if self.ext == 'xls':
            engine_xls = None
        if self.ext == 'xlsx':
            engine_xls = "openpyxl"
        return engine_xls


    def get_dask_df(self,file):
        dask = delayed(pd.read_csv(file, on_bad_lines='skip', encoding_errors='ignore', header=0, encoding=self.get_encoding_method(file), usecols=self.get_usecols().keys(), dtype=self.get_dtypes(), sep=self.get_delim_method(file)))
        data = df1.from_delayed(dask)
        return data
    


    def get_exel_df(self,file):
        app=[]
        usercols=self.get_usecols().keys()
        # print('self.get_usecols()',self.get_usecols())
        # print('self.get_fields()',self.get_fields())
        

        try:
            # print('usercols-str',usercols)
            data = pd.read_excel(file, usecols=usercols, engine = self.get_exel_engine())
        except:
            for key in list(usercols):
                # print('beffore',type(key))
                if type(key) == int:
                    app.append(int(key))
                else:
                    app.append(key)
                # print('after',type(key))
            # print('usercols-int',app)
            data = pd.read_excel(file, engine = self.get_exel_engine())
            data.columns = data.columns.astype("str")
            data = data[usercols]

            

        # print(data)
        return data
    
    
    def get_df_method(self,file):
        if (self.ext == 'xls') or (self.ext == 'xlsx'):
            df_method = self.get_exel_df(file)
        else:
            df_method = self.get_dask_df(file)
        return df_method
    

    def get_clean(self,file):
            
        words = StopWords.objects.values_list('words', flat=True).distinct()
        words_up=list(map(str.upper, words))
        brands = Brands.objects.values_list('brand', flat=True).distinct()
        brands_low = list(map(str.lower, brands))
        brands_up = list(map(str.upper, brands))
 
        # key = file.split('/')[-1]
        key = os.path.basename(file)
        # print('название фйла',key)
        OnePrice = AddFiles.objects.get(files=key)

        with ProgressBar(), ResourceProfiler(dt=0.25) as rprof:
            s_time_dask = time.time()
            
            data = self.get_df_method(file)
            tt=data.rename(columns = self.get_fields())

  


            if self.mono:
                tt['brend_field'] = OnePrice.brend_field
                tt['brend_field'] = tt['brend_field'].astype('category')
            else:
                pass

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

            if (self.ext == 'xls') or (self.ext == 'xlsx'):

                # print('new-before',ts)
                ts["brend_field"] = ts["brend_field"].astype(str)
                ta = ts.loc[ts["brend_field"].str.upper().isin(brands_up)]
                ta["oem_field"] = ta["oem_field"].astype(str)
            else:
                ta = ts.loc[ts["brend_field"].str.upper().isin(brands_up)].compute()

            new = ta[~ta["name_field"].str.upper().isin(words_up)]

            new = ta[~ta["name_field"].str.contains('|'.join(words_up))]
            
            # ddd = ta["name_field"][s.str.upper().contains('|'.join(words_up))]

            # print(ta)

            # new = ta[~ta["name_field"].str.upper().isin(words_up)]

            new['brend_field'] = new['brend_field'].str.upper()
            #изза этого крашится при заполнении новой дб, Exception Value:Length of values (998) does not match length of index (101706
            # new['brend_field'] = new['brend_field'].astype('category')
            # new['name_field'] = new['name_field'].astype('category')
            e_time_dask = time.time()

        
        # print(new)
        print("читаем файл ",key, (e_time_dask-s_time_dask), "seconds")
        return new

