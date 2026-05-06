import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import re
from openai import OpenAI

# 1. Текст хөрвүүлэх функц
def cyrillic_to_latin(text):
    """Кирилл текстийг хайлтад зориулж латин руу хөрвүүлэх"""
    if not isinstance(text, str):
        return text
    char_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'j', 'з': 'z', 'и': 'i', 'й': 'i', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'ө': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
        'у': 'u', 'ү': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh',
        'щ': 'sh', 'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
    }
    text = text.lower().strip()
    result = "".join(char_map.get(c, c) for c in text)
    return re.sub(r'\s+', '_', result)

# 2. Өгөгдөл ачаалах ба цэвэрлэх
def load_and_preprocess(file_path):
    if not os.path.exists(file_path):
        return None
    
    xls = pd.ExcelFile(file_path)
    # Хуудас бүрийн нэрийг тохируулах (Таны Excel-ийн хуудасны нэрстэй таарах ёстой)
    raw_data = {
        'tech': pd.read_excel(xls, 'Тех карт'),
        'urtug': pd.read_excel(xls, 'Sheet4'),
        'sales': pd.read_excel(xls, 'Борлуулалт'),
        'prod': pd.read_excel(xls, 'Үйлдвэрлэл')
    }
    
    processed_data = {}
    for key, df in raw_data.items():
        # БАГАНЫН НЭРСИЙГ ЛАТИН БОЛГОХ
        df.columns = [cyrillic_to_latin(str(col)) for col in df.columns]
        
        if 'effective_date' in df.columns:
            df['effective_date'] = pd.to_datetime(df['effective_date'])
            df['year_month'] = df['effective_date'].dt.to_period('M')
        processed_data[key] = df
            
    return processed_data

# 3. Үндсэн тайлан бодох
def calculate_master_report(data):
    # Түүхий эдийн дундаж үнэ
    urtug_avg = data['urtug'].groupby(['buteegdehuunii_id', 'year_month'])['urtug_une'].mean().reset_index()
    urtug_avg.rename(columns={'urtug_une': 'avg_material_price'}, inplace=True)
    
    # Нэгж өртөг (1 порц)
    df_unit = pd.merge(data['tech'], urtug_avg, on=['buteegdehuunii_id', 'year_month'], how='left')
    df_unit['row_cost'] = (df_unit['hemjee'] * df_unit['avg_material_price']) / df_unit['gramm']
    unit_costs = df_unit.groupby(['hoolnii_ner', 'year_month'])['row_cost'].sum().reset_index(name='unit_cost')
    
    # Борлуулалт ба Үйлдвэрлэл нэгтгэх
    final = pd.merge(data['sales'], data['prod'], on=['hoolnii_ner', 'year_month'], how='outer')
    final = pd.merge(final, unit_costs, on=['hoolnii_ner', 'year_month'], how='left')
    
    # Санхүүгийн тооцоолол (Баганын нэрс латин болсныг анхаарна уу)
    final['sales_price'] = final['sales_price'].fillna(final['unit_cost'])
    final['revenue'] = final['sales_count'] * final['sales_price']
    final['total_cost'] = final['production_count'] * final['unit_cost']
    final['profit'] = final['revenue'] - final['total_cost']
    
    final['variance'] = final['production_count'] - final['sales_count']
    final['status'] = np.where(final['variance'] > (final['production_count'] * 0.1), "⚠️ Өндөр зөрүү", "✅ Хэвийн")
    
    return final

# 4. Туслах хайлтын функцүүд
def get_food_details(df, query):
    search_term = cyrillic_to_latin(query)
    mask = df.apply(lambda x: search_term in cyrillic_to_latin(str(x['hoolnii_ner'])), axis=1)
    return df[mask]

def get_top_profitable_foods(df, n=5):
    return df.sort_values(by='profit', ascending=False).head(n)

def get_high_waste_foods(df):
    return df[df['status'] == "⚠️ Өндөр зөрүү"]

def get_ingredient_impact(data, ingredient_name):
    search_term = cyrillic_to_latin(ingredient_name)
    urtug_df = data['urtug'].copy()
    
    mask = urtug_df.apply(lambda x: search_term in cyrillic_to_latin(str(x['buteegdehuunii_ner'])), axis=1)
    filtered_urtug = urtug_df[mask]
    
    if filtered_urtug.empty:
        return None

    impact_df = pd.merge(data['tech'], filtered_urtug, on=['buteegdehuunii_id'], how='inner')
    # Формула: (Хэмжээ * Үнэ) / Грамм
    impact_df['ingredient_cost'] = (impact_df['hemjee'] * impact_df['urtug_une']) / impact_df['gramm']
    
    return impact_df[['hoolnii_ner', 'buteegdehuunii_ner', 'ingredient_cost']]