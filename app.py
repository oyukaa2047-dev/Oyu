import pandas as pd
import streamlit as st
import numpy as np
import re
import warnings
from datetime import datetime, timedelta
import openpyxl

# 1. Тохиргоо болон Анхааруулга хаах
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

st.set_page_config(page_title="CF - Тех Карт & Аналитик Chatbot", page_icon="💬", layout="centered")

# 2. ДАТА УНШИХ БОЛОН ЦЭВЭРЛЭХ ФУНКЦ
@st.cache_data
def load_and_clean_data():
    file_path = "data/best_hurgelt.xlsx"
    all_sheets = pd.read_excel(file_path, sheet_name=None)
    zah_huu_df = all_sheets["зах хуу"]
    
    zah_huu_df = zah_huu_df.loc[:, :'мэдээ']
    
    # А. Огноо цэвэрлэгээ
    zah_huu_df['он сар'] = zah_huu_df['он сар'].astype(str).str.strip()
    zah_huu_df['он сар'] = zah_huu_df['он сар'].replace(['nan', 'None', ''], np.nan)
    
    zah_huu_df['он сар'] = zah_huu_df['он сар'].ffill()
    zah_huu_df['он сар'] = pd.to_datetime(zah_huu_df['он сар'], errors='coerce')
    zah_huu_df['огноо_өдөр'] = zah_huu_df['он сар'].dt.date
    
    # Б. Барааны нэр болон Жолооч баганыг цэвэрлэх
    zah_huu_df.dropna(subset=['барааны нэр'], inplace=True)
    zah_huu_df.rename(columns={'Unnamed: 4': 'Жолооч'}, inplace=True)
    
    zah_huu_df['Жолооч'] = zah_huu_df['Жолооч'].fillna('').astype(str).str.strip().str.capitalize()
    
    солих_нэрс = {
        'Яабраа': 'Ябраа', 'Үүүний': 'Үүний', 'Мз': 'МЗ', 'Э/болд': 'Enkhbold', 'Эболд': 'Enkhbold',
        'Насмрай': 'Намсрай', 'Батэрэдэнэ': 'Батэрдэнэ', 'Батэрдэнэ\n': 'Батэрдэнэ', 'Азаа2': 'Азбилэг',
        '99335584': 'Хүрлээ', 'амаглан': 'Амгалан', 'араас мэндээ': 'Мэндсайхан', 'ээгий араас': 'Энхболд',
        'араас ээгий': 'Энхболд', 'туул2': 'Ариунтуул', 'Араас мэндээ': 'Мэндсайхан', 'Араас батболд': 'Батболд',
        'Зоорий': 'Ариунзориг', 'Араас ээгий': 'Ээгий', 'Туул2': 'Ариунтуул', 'Ээгий араас': 'Ээгий',
        'Амаглан': 'Амгалан', 'Мэндээ': 'Мэндсайхан', 'Туул': 'Ариунтуул', 'Зоригоо': 'Ариунзориг',
        'Пүрэвээ': 'Пүрэв', 'Эндээ': 'Мэндсайхан', 'Багана': 'Баганаа'
    }
    zah_huu_df['Жолооч'] = zah_huu_df['Жолооч'].replace(солих_нэрс)
    zah_huu_df['Жолооч'] = zah_huu_df['Жолооч'].apply(lambda x: 'Тодорхойгүй' if x.isdigit() else x)
    
    zah_huu_df['барааны нэр'] = zah_huu_df['барааны нэр'].fillna('').astype(str)
    tengsu_нөхцөл = zah_huu_df['барааны нэр'].str.contains('Эр бэлдмэл Tengsu-1,', case=False, na=False)
    zah_huu_df.loc[tengsu_нөхцөл, 'утас'] = 99335584
    
    zah_huu_df.loc[zah_huu_df['Жолооч'].isna() | (zah_huu_df['Жолооч'] == ''), 'утас'] = 0
    
    # В. Ангилах логик
    хүргэсэн_үгс = ['хүргэсэн', 'хүрэгсэн', 'хүргэгдсэн', 'хүргэсэн ', 'авсан', 'өчигдөр авсан', 'авчихсан']
    буцаасан_үгс = ['буцаасан', 'буцаав', 'буцаана', 'үзээд аваагүй', 'голсон', 'голов'] 
    хойшлогдсон_үгс = ['хойшилсон', 'хойш', 'маргааш', 'мар', 'орой', 'амжаагүй']
    
    def утгаар_ангилах(утга):
        if pd.isna(утга) or утга == '': return 'Цуцалсан'
        if isinstance(утга, (pd.Timestamp, type(pd.NaT))): return 'Хүргэсэн'
        цэвэр_утга = str(утга).strip().lower()
        if 'дэлгүүрт үлдээ' in цэвэр_утга: return 'Цуцалсан'
        if any(w in цэвэр_утга for w in хүргэсэн_үгс): return 'Хүргэсэн'
        if any(w in цэвэр_утга for w in буцаасан_үгс): return 'Буцаасан'
        if any(w in цэвэр_утга for w in хойшлогдсон_үгс): return 'Хойшлогдсон захиалга'
        return 'Цуцалсан'

    zah_huu_df['мэдээ'] = zah_huu_df['мэдээ'].apply(утгаар_ангилах)
    return zah_huu_df

try:
    zah_huu_df = load_and_clean_data()
except Exception as e:
    st.error(f"Дата уншихад алдаа гарлаа: {e}")
    st.stop()

# 3. ТЕКСТЭЭС ОГНОО ШҮҮХ ФУНКЦ
def extract_date_from_text(text):
    date_pattern = r'(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})'
    match = re.search(date_pattern, text)
    if match:
        year, month, day = match.groups()
        return datetime(int(year), int(month), int(day)).date()
    return None

# --- ЧАТБОТ ИНТЕРФЭЙС ---
st.title("💬 online Chatbot")
st.write("Жолооч, бараа, огноо эсвэл хугацааны интервалаар асуугаарай. (ж.нь: `Батболд`, `Батболд өчигдөр`)")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Сайн байна уу! Би захиалгын ухаалаг аналитик туслах байна."}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if user_query := st.chat_input("Асуултаа энд бичнэ үү..."):
    with st.chat_message("user"):
        st.write(user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    query_lower = user_query.lower()
    today = datetime.today().date()
    
    # А. ЖОЛООЧ ШҮҮХ
    driver_found = None
    all_drivers = [name for name in zah_huu_df['Жолооч'].unique() if name !=