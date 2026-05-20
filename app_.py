import pandas as pd
import streamlit as st
import numpy as np
import re
import warnings
from datetime import datetime, timedelta

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
    zah_huu_df['он сар'] = zah_huu_df['он сар'].replace('1/3', '2026-01-03')
    
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
    хүргэсэн_үгс = ['хүргэсэн', 'хүрэгсэн', 'хүргэгдсэн', 'хүргэсэн ', 'авсан', 'өчигдөр авсан', 'авчихсан'] # (товчлов)
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
st.write("Жолооч, бараа, огноо эсвэл хугацааны интервалаар асуугаарай. (ж.нь: `Батболд өнгөрсөн долоо хоногт хэдэн захиалга хүргэсэн бэ?`)")

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
    
    # А. ХУГАЦАА ТОГТООХ ЛОГИК (Интервал болон Тодорхой өдөр)
    filtered_df = zah_huu_df.copy()
    date_text = "Бүх цаг үеийн"
    today = datetime.today().date()
    
    specific_date = extract_date_from_text(user_query)
    
    if specific_date:
        filtered_df = filtered_df[filtered_df['огноо_өдөр'] == specific_date]
        date_text = str(specific_date)
    elif "өнөөдөр" in query_lower:
        filtered_df = filtered_df[filtered_df['огноо_өдөр'] == today]
        date_text = "Өнөөдөр"
    elif "өчигдөр" in query_lower:
        yesterday = today - timedelta(days=1)
        filtered_df = filtered_df[filtered_df['огноо_өдөр'] == yesterday]
        date_text = "Өчигдөр"
    elif "өнгөрсөн долоо хоног" in query_lower:
        start_date = today - timedelta(days=today.weekday() + 7)
        end_date = start_date + timedelta(days=6)
        filtered_df = filtered_df[(filtered_df['огноо_өдөр'] >= start_date) & (filtered_df['огноо_өдөр'] <= end_date)]
        date_text = f"Өнгөрсөн долоо хоног ({start_date} ~ {end_date})"
    elif "энэ долоо хоног" in query_lower:
        start_date = today - timedelta(days=today.weekday())
        filtered_df = filtered_df[filtered_df['огноо_өдөр'] >= start_date]
        date_text = f"Энэ долоо хоног (Мягмараас өнөөдрийг хүртэл)"
    elif "энэ сар" in query_lower:
        start_date = today.replace(day=1)
        filtered_df = filtered_df[filtered_df['огноо_өдөр'] >= start_date]
        date_text = f"Энэ сар ({start_date.strftime('%Y-%m')})"
        
    # Б. ЖОЛООЧ ШҮҮХ ЛОГИК
    driver_found = None
    all_drivers = [name for name in filtered_df['Жолооч'].unique() if name != 'Тодорхойгүй' and not pd.isna(name)]
    for driver in all_drivers:
        if driver.lower() in query_lower:
            driver_found = driver
            filtered_df = filtered_df[filtered_df['Жолооч'] == driver]
            break

    # В. БАРАА ШҮҮХ ЛОГИК
    product_text = ""
    if "tengsu" in query_lower or "тэнхсү" in query_lower:
        filtered_df = filtered_df[filtered_df['барааны нэр'].str.contains('Tengsu', case=False)]
        product_text = " (Бараа: Tengsu)"
    elif "маск" in query_lower:
        filtered_df = filtered_df[filtered_df['барааны нэр'].str.contains('маск', case=False)]
        product_text = " (Бараа: Маск)"

    # Г. ҮР ДҮНГ ТОГТООЖ ХАРИУЛТ БЭЛДЭХ
    total_orders = len(filtered_df)
    summary = filtered_df['мэдээ'].value_counts()
    
    # Гарчиг бэлдэх
    driver_info = f" Жолооч: **{driver_found}**" if driver_found else ""
    bot_response = f"📅 **{date_text}**-ний{driver_info}{product_text} захиалгын мэдээлэл:\n\n"
    bot_response += f"• **Нийт захиалга:** {total_orders}ш\n"
    bot_response += f"--- \n"
    bot_response += f"• 🟩 **Хүргэсэн:** {summary.get('Хүргэсэн', 0)}ш\n"
    bot_response += f"• 🟨 **Хойшлогдсон захиалга:** {summary.get('Хойшлогдсон захиалга', 0)}ш\n"
    bot_response += f"• 🟧 **Буцаасан:** {summary.get('Буцаасан', 0)}ш\n"
    bot_response += f"• 🟥 **Цуцалсан:** {summary.get('Цуцалсан', 0)}ш"

    with st.chat_message("assistant"):
        st.write(bot_response)
    st.session_state.messages.append({"role": "assistant", "content": bot_response})