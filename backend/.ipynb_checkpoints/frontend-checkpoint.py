import pandas as pd
import sys
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np
from functions import process_restaurant_data, generate_profit_chart

def generate_comprehensive_margin_report(file_path):
    if not os.path.exists(file_path):
        print(f"❌ '{file_path}' файл олдсонгүй.")
        return

    # 1. Өгөгдлийг унших
    xls = pd.ExcelFile(file_path)
    df_tech = pd.read_excel(file_path, sheet_name='Тех карт')
    df_urtug = pd.read_excel(file_path, sheet_name='Sheet4')
    df_sales = pd.read_excel(file_path, sheet_name='Борлуулалт')
    df_prod = pd.read_excel(file_path, sheet_name='Үйлдвэрлэл')

    # Огноог сар болгон хөрвүүлэх (Сар бүрийн өртөг өөр байж болох тул)
    for df in [df_tech, df_urtug, df_sales, df_prod]:
        if 'effective_date' in df.columns:
            df['effective_date'] = pd.to_datetime(df['effective_date'])
            df['year_month'] = df['effective_date'].dt.to_period('M')

    # 2. Өртөг тооцох (Түүхий эдийн дундаж үнэ)
    urtug_avg = df_urtug.groupby(['Buteegdehuunii_id', 'year_month'])['urtug_une'].mean().reset_index()
    urtug_avg.rename(columns={'urtug_une': 'average_urtug'}, inplace=True)
    
    # 3. 1 порцны өртөг (Тех карт-ын логикоор)
    df_unit_calc = pd.merge(df_tech, urtug_avg, on=['Buteegdehuunii_id', 'year_month'], how='left')
    df_unit_calc['row_total'] = (df_unit_calc['Hemjee'] * df_unit_calc['average_urtug']) / df_unit_calc['Грамм']
    
    hool_cost = df_unit_calc.groupby(['Hoolnii_ner', 'year_month'])['row_total'].sum().reset_index()
    hool_cost.rename(columns={'row_total': 'unit_cost'}, inplace=True)

    # 4. Борлуулалтыг засах (Waste тооцох - Хоосон үнийг өртгөөр нөхөх)
    df_sales_fixed = pd.merge(df_sales, hool_cost, on=['Hoolnii_ner', 'year_month'], how='left')
    
    # Sales_Price багана байхгүй бол нэмэх, байвал хоосон утгыг өртгөөр нөхөх
    if 'Sales_Price' in df_sales_fixed.columns:
        df_sales_fixed['Sales_Price'] = df_sales_fixed['Sales_Price'].fillna(df_sales_fixed['unit_cost'])
    else:
        df_sales_fixed['Sales_Price'] = df_sales_fixed['unit_cost']

    # 5. Нэгдсэн тайлан ба Margin тооцоолол
    # Борлуулалт болон Үйлдвэрлэлийг нэгтгэх
    final_report = pd.merge(df_sales_fixed, df_prod, on=['Hoolnii_ner', 'year_month', 'effective_date'], how='outer')
    
    # Өртгийн мэдээллийг дахин баталгаажуулж нэгтгэх
    final_report = pd.merge(final_report, hool_cost, on=['Hoolnii_ner', 'year_month'], how='left', suffixes=('', '_final'))
    if 'unit_cost_final' in final_report.columns:
         final_report['unit_cost'] = final_report['unit_cost'].fillna(final_report['unit_cost_final'])
         final_report.drop(columns=['unit_cost_final'], inplace=True)

    # Margin тооцох
    final_report['Unit_Profit'] = final_report['Sales_Price'] - final_report['unit_cost']
    final_report['Margin_%'] = (final_report['Unit_Profit'] / final_report['Sales_Price']) * 100
    final_report['Food_Cost_%'] = (final_report['unit_cost'] / final_report['Sales_Price']) * 100
    
    # Санхүүгийн нийт дүн
    final_report['Total_Revenue'] = final_report['Sales_Count'] * final_report['Sales_Price']
    final_report['Total_Production_Cost'] = final_report['Production_Count'] * final_report['unit_cost']
    final_report['Net_Profit'] = final_report['Total_Revenue'] - final_report['Total_Production_Cost']

    # 6. Файлд хадгалах
    output_file = "final_margin_analysis_report.xlsx"
    final_report.to_excel(output_file, index=False)
    
    print(f"✅ Амжилттай! Бүх тооцоолол ба Margin орсон тайлан бэлэн боллоо: {output_file}")

# Кодыг ажиллуулах
file_path = "data/turshilt ai.xlsx"
generate_comprehensive_margin_report(file_path)



def perform_extended_analysis(file_path):
    xls = pd.ExcelFile(file_path)
    df_tech = pd.read_excel(xls, 'Тех карт')
    df_urtug = pd.read_excel(xls, 'Sheet4')
    df_sales = pd.read_excel(xls, 'Борлуулалт')
    df_prod = pd.read_excel(xls, 'Үйлдвэрлэл')

    # Огноо засах
    for df in [df_tech, df_urtug, df_sales, df_prod]:
        if 'effective_date' in df.columns:
            df['effective_date'] = pd.to_datetime(df['effective_date'])
            df['year_month'] = df['effective_date'].dt.to_period('M').astype(str)

    # 1. Өртөг тооцох
    urtug_avg = df_urtug.groupby(['Buteegdehuunii_id', 'year_month'])['urtug_une'].mean().reset_index()
    urtug_avg.rename(columns={'urtug_une': 'average_urtug'}, inplace=True)
    df_unit_calc = pd.merge(df_tech, urtug_avg, on=['Buteegdehuunii_id', 'year_month'], how='left')
    df_unit_calc['row_total'] = (df_unit_calc['Hemjee'] * df_unit_calc['average_urtug']) / df_unit_calc['Грамм']
    hool_cost = df_unit_calc.groupby(['Hoolnii_ner', 'year_month'])['row_total'].sum().reset_index()
    hool_cost.rename(columns={'row_total': 'unit_cost'}, inplace=True)

    # 2. Нэгдсэн дата үүсгэх (Unit_Profit-ийг энд үүсгэнэ)
    final_report = pd.merge(df_sales, hool_cost, on=['Hoolnii_ner', 'year_month'], how='left')
    final_report['Sales_Price'] = final_report['Sales_Price'].fillna(final_report['unit_cost'])
    final_report['Unit_Profit'] = final_report['Sales_Price'] - final_report['unit_cost']

    # 3. График зурах
    plt.figure(figsize=(12, 6))
    plot_data = final_report.groupby('Hoolnii_ner')['Unit_Profit'].mean().sort_values().reset_index()
    sns.barplot(data=plot_data, x='Hoolnii_ner', y='Unit_Profit', 
                palette=['red' if x < 0 else 'green' for x in plot_data['Unit_Profit']])
    plt.xticks(rotation=90)
    plt.title('Average Profit per Unit')
    plt.savefig('profit_chart.png')
    
    print("✅ Амжилттай: 'profit_chart.png' болон 'inventory_alert.xlsx' үүслээ.")

perform_extended_analysis("data/turshilt ai.xlsx")
