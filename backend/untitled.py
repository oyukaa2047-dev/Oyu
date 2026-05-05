import pandas as pd
import streamlit as st
import io

# 1. Тохиргоо болон файлын зам
file_path = "data/turshilt ai.xlsx"
output_path = "data/tech_kart_no_cost.xlsx"

st.title("Тех карт шинэчлэгч")

# 2. Өгөгдлийг унших
df_tech = pd.read_excel(file_path, sheet_name='Тех карт')
df_urtug = pd.read_excel(file_path, sheet_name='Sheet4')

# 3. Баганын нэрсийг цэвэрлэх (Хоосон зайг устгах)
df_tech.columns = df_tech.columns.str.strip()
df_urtug.columns = df_urtug.columns.str.strip()

# 4. Огноог datetime төрөлд шилжүүлэх
df_tech['effective_date'] = pd.to_datetime(df_tech['effective_date'])
df_urtug['effective_date'] = pd.to_datetime(df_urtug['effective_date'])

# 5. Сар бүрээр тулгахын тулд Year-Month туслах багана үүсгэх
df_tech['year_month'] = df_tech['effective_date'].dt.to_period('M')
df_urtug['year_month'] = df_urtug['effective_date'].dt.to_period('M')

# 6. AVERAGEIFS логик: ID болон Хугацаагаар груплэж, өртгийн дунджийг авна
urtug_average = df_urtug.groupby(['Buteegdehuunii_id', 'year_month'])['urtug_une'].mean().reset_index()
urtug_average.rename(columns={'urtug_une': 'average_urtug'}, inplace=True)

# 7. 'Тех карт' болон дундаж өртгийг нэгтгэх
df_final = pd.merge(
    df_tech, 
    urtug_average, 
    on=['Buteegdehuunii_id', 'year_month'], 
    how='left'
)

# 8. Туслах багана болон "шинэ_өртөг" (байвал) устгах
df_final = df_final.drop(columns=['year_month'])
if 'шинэ_өртөг' in df_final.columns:
    df_final = df_final.drop(columns=['шинэ_өртөг'])

# 9. Excel файлыг дотооддоо хадгалах (tech_kart_no_cost.xlsx)
df_final.to_excel(output_path, index=False)

# --- STREAMLIT ДЭЭР ХАРУУЛАХ ХЭСЭГ ---

st.success(f"Тооцоолол амжилттай! Файлыг '{output_path}' замд хадгаллаа.")

# Хүснэгтийг харуулах
st.subheader("Шинэчлэгдсэн хүснэгт")
st.dataframe(df_final)

# Excel файлыг Streamlit-ээр дамжуулан татаж авах боломж олгох
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    df_final.to_excel(writer, index=False, sheet_name='Sheet1')
    
st.download_button(
    label="📥 Excel файлыг татах",
    data=buffer.getvalue(),
    file_name="tech_kart_no_cost.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)