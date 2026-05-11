import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns

def process_restaurant_data(file_path):
    if not os.path.exists(file_path):
        return None, "❌ Файл олдсонгүй."

    try:
        # 1. Өгөгдлийг унших
        xls = pd.ExcelFile(file_path)
        df_tech = pd.read_excel(xls, 'Тех карт')
        df_urtug = pd.read_excel(xls, 'Sheet4')
        df_sales = pd.read_excel(xls, 'Борлуулалт')
        df_prod = pd.read_excel(xls, 'Үйлдвэрлэл')

        # Огноог хөрвүүлэх (Сар бүрээр)
        for df in [df_tech, df_urtug, df_sales, df_prod]:
            if 'effective_date' in df.columns:
                df['effective_date'] = pd.to_datetime(df['effective_date'])
                df['year_month'] = df['effective_date'].dt.to_period('M').astype(str)

        # 2. Түүхий эдийн сарын дундаж өртөг (Buteegdehuunii_id - аар)
        urtug_avg = df_urtug.groupby(['Buteegdehuunii_id', 'year_month'])['urtug_une'].mean().reset_index()
        urtug_avg.rename(columns={'urtug_une': 'average_urtug'}, inplace=True)

        # 3. Нэгж өртөг тооцох (Тех картны логик)
        # Хэрэв Грамм багана байхгүй бол 1 гэж үзэж алдаанаас сэргийлнэ
        df_unit_calc = pd.merge(df_tech, urtug_avg, on=['Buteegdehuunii_id', 'year_month'], how='left')
        gram_col = 'Грамм' if 'Грамм' in df_unit_calc.columns else 'gram'
        
        df_unit_calc['row_total'] = (df_unit_calc['Hemjee'] * df_unit_calc['average_urtug']) / df_unit_calc[gram_col].fillna(1)
        
        # Хоолны 1 порцны нийт өртөг
        hool_cost = df_unit_calc.groupby(['Hoolnii_ner', 'year_month'])['row_total'].sum().reset_index()
        hool_cost.rename(columns={'row_total': 'unit_cost'}, inplace=True)

        # 4. Борлуулалт ба Үйлдвэрлэлтэй нэгтгэх
        final_df = pd.merge(df_sales, hool_cost, on=['Hoolnii_ner', 'year_month'], how='left')
        
        # Sales_Price хоосон бол unit_cost-оор нөхөх
        if 'Sales_Price' in final_df.columns:
            final_df['Sales_Price'] = final_df['Sales_Price'].fillna(final_df['unit_cost'])
        
        # Үйлдвэрлэлийн тоог нэмэх
        final_df = pd.merge(final_df, df_prod[['Hoolnii_ner', 'year_month', 'Production_Count']], 
                            on=['Hoolnii_ner', 'year_month'], how='outer')

        # Санхүүгийн үзүүлэлтүүд
        final_df['Revenue'] = final_df['Sales_Count'] * final_df['Sales_Price']
        final_df['Total_Cost'] = final_df['Production_Count'] * final_df['unit_cost']
        final_df['Net_Profit'] = final_df['Revenue'] - final_df['Total_Cost']
        final_df['Margin_%'] = ((final_df['Sales_Price'] - final_df['unit_cost']) / final_df['Sales_Price']) * 100

        return final_df, df_unit_calc  # Тайлан ба дэлгэрэнгүй тооцоолол (түүхий эдтэй) буцаана

    except Exception as e:
        return None, f"⚠️ Алдаа гарлаа: {str(e)}"

def generate_profit_chart(df):
    plt.figure(figsize=(10, 6))
    # Сүүлийн 1 сарын датаг шүүх эсвэл бүгдийг зурах
    sns.barplot(data=df.sort_values('Net_Profit', ascending=False).head(10), 
                x='Hoolnii_ner', y='Net_Profit', hue='year_month')
    plt.title('Хамгийн их ашигтай 10 хоол (Сараар)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    chart_path = "profit_chart.png"
    plt.savefig(chart_path)
    return chart_path