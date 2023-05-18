import pandas as pd
import numpy as np
import pickle
import pyarrow as pa
import pyarrow.parquet as pq

def Dfilter(dataframe):
        # Убираем полные дубликаты из общего фрейма
        dataframe.drop_duplicates(inplace=True)
        
        # Получаем все неполные дубликаты по оем
        dub_oem = dataframe[(dataframe[['oem_field']].duplicated(keep=False))]
        dub_oem.to_csv('mediafiles/csv/df_duble.csv', index = False)

        # Вынимаем из фрйма оставшиеся совпадения по оем
        dataframe.drop_duplicates(subset = 'oem_field', inplace=True, keep=False)
        # result.to_csv('result.csv', index = False)

        # Получаем все дубликаты с полностью заполненными полями
        dub_oem_name_weight_vol = dub_oem[(dub_oem[['oem_field']].duplicated(keep=False)) & (dub_oem['weight_field'] > 0) & (dub_oem['volume_field'] > 0)]
        dub_oem_name_weight_vol.drop_duplicates(['oem_field','brend_field'], inplace=True)
        # dub_oem_name_weight_vol.to_csv('mediafiles/csv/dub_oem_name_weight_vol.csv', index = False)

        # Получаем все дубликаты с одним из заполненных полей
        dub_oem_null = dub_oem[(dub_oem[['oem_field']].duplicated(keep=False)) & ((dub_oem['weight_field'] == 0) | (dub_oem['volume_field'] == 0)) ]
        # dub_oem_null.to_csv('dub_oem_null.csv', index = False)

        # print(dub_oem_null)

        # Мерджим между собой дубликаты с одним из заполненных полей
        group_null_merdge = dub_oem_null.groupby(by=['oem_field','brend_field'],as_index=False).agg({'name_field': 'first','weight_field': 'max','volume_field': 'max','brend_field': 'first'})
        # group_null_merdge.to_csv('mediafiles/csv/group_null_merdge.csv', index = False)
        
        # Соединяем смерженные с полными полями и оставляем максимальные
        finalDF = pd.concat([group_null_merdge, dub_oem_name_weight_vol],ignore_index=True)

        #функция для поиска минимального ненулевого значения
        get_min = lambda x: np.min(x) if np.min(x) > 0 else np.max(x)


        finalDF_ALL = finalDF.groupby(by=['oem_field','brend_field'],as_index=False).agg({'name_field': 'first','weight_field': get_min,'volume_field': 'max','brend_field': 'first'})
        # finalDF_ALL.to_csv('mediafiles/csv/finalDF_ALL.csv', index = False)

        FULL = pd.concat([finalDF_ALL, dataframe],ignore_index=True)

        # проверяем если объем меньше массы
        FULL.loc[FULL['volume_field'] < FULL['weight_field'], 'volume_field'] = 0


        table = pa.Table.from_pandas(FULL, preserve_index=False)
        pq.write_table(table, 'mediafiles/parquet/data.parquet')

        # with open('mediafiles/csv/data.pickle', 'wb') as f:
        #     pickle.dump(FULL, f)

        # FULL.to_csv('mediafiles/csv/FULL.csv', index = False)

        return FULL