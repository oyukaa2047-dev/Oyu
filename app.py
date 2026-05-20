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
@st.cache_data(ttl=60)
def load_and_clean_data():
    file_path = "data/best_hurgelt.xlsx"
    all_sheets = pd.read_excel(file_path, sheet_name=None)
    zah_huu_df = all_sheets["зах хуу"]
    
    zah_huu_df = zah_huu_df.loc[:, :'мэдээ']
    
    # А. Огноо цэвэрлэгээ
    if 'он сар' in zah_huu_df.columns:
        zah_huu_df['он сар'] = zah_huu_df['он сар'].astype(str).str.strip()
    elif 'он са r' in zah_huu_df.columns:
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
        '99335584': 'Хүрлээ', 'амаглан': 'Амгалан', 'араас мэндээ': 'Мэндсайхан', 'ээгий араас': 'Enkhbold',
        'араас ээгий': 'Enkhbold', 'туул2': 'Ариунтуул', 'Араас мэндээ': 'Мэндсайхан', 'Араас батболд': 'Батболд',
        'Зоорий': 'Ариунзориг', 'Араас ээгий': 'Ээгий', 'Туул2': 'Ариунтуул', 'Ээгий араас': 'Ээгий',
        'Амаглан': 'Амгалан', 'Мэндээ': 'Мэндсайхан', 'Туул': 'Ариунтуул', 'Зоригоо': 'Аriunzoриг',
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
st.write("Жолооч, бараа, огноо эсвэл хугацааны интервалаар асуугаарай.")

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
    all_drivers = [name for name in zah_huu_df['Жолооч'].unique() if name != 'Тодорхойгүй' and not pd.isna(name)]
    for driver in all_drivers:
        if driver.lower() in query_lower:
            driver_found = driver
            break

    # Б. ХУГАЦААНЫ ТҮЛХҮҮР ҮГ ШАЛГАХ
    has_date_keyword = any(kw in query_lower for kw in ["өнөөдөр", "өчигдөр", "долоо хоног", "сар"]) or extract_date_from_text(user_query) is not None

    # В. БАРАА ШҮҮХ ЛОГИК
    product_filter = None
    product_text = ""
    if "tengsu" in query_lower or "тэнхсү" in query_lower:
        product_filter = "Tengsu"
        product_text = " (Бараа: Tengsu)"
    elif "маск" in query_lower:
        product_filter = "маск"
        product_text = " (Бараа: Mask)"

    # Г. ҮР ДҮН ТООЦООЛОХ БОЛОН ХАРИУЛТ БЭЛДЭХ ЛОГИК
    bot_response = ""

    # Нөхцөл 1: Зөвхөн Жолоочийн нэр хэлсэн бөгөөд хугацаа заагаагүй бол (Өнөөдөр, 7 хоног, Сар гэсэн 3 интервалыг цуг харуулна)
    if driver_found and not has_date_keyword:
        bot_response = f"👤 Жолооч **{driver_found}**-ийн нэгдсэн статистик мэдээлэл{product_text}:\n\n"
        
        intervals = {
            "📌 Өнөөдөр": (today, today),
            "📅 Өнгөрсөн 7 хоног": (today - timedelta(days=today.weekday() + 7), today - timedelta(days=today.weekday() + 7) + timedelta(days=6)),
            "📊 Энэ сар": (today.replace(day=1), today)
        }
        
        for title, (start, end) in intervals.items():
            df_slice = zah_huu_df[(zah_huu_df['огноо_өдөр'] >= start) & (zah_huu_df['огноо_өдөр'] <= end) & (zah_huu_df['Жолооч'] == driver_found)]
            
            if product_filter:
                df_slice = df_slice[df_slice['барааны нэр'].str.contains(product_filter, case=False)]
                
            total_orders = len(df_slice)
            summary = df_slice['мэдээ'].value_counts()
            
            # Мэдээ баганын мөрүүдийг шууд тоолж байна
            delivered = summary.get('Хүргэсэн', 0)
            postponed = summary.get('Хойшлогдсон захиалга', 0)
            returned = summary.get('Буцаасан', 0)
            canceled = summary.get('Цуцалсан', 0)
                
            bot_response += f"### {title}\n"
            bot_response += f"• 📑 Нийт захиалга (мөр): **{total_orders}** ш\n"
            bot_response += f"• 🟩 Хүргэсэн: {delivered} ш | 🟨 Хойшилсон: {postponed} ш | 🟧 Буцаасан: {returned} ш | 🟥 Цуцалсан: {canceled} ш\n"
            bot_response += "---\n"

    # Нөхцөл 2: Тодорхой хугацаа (өдөр, 7 хоног, сар) зааж асуусан бол
    else:
        filtered_df = zah_huu_df.copy()
        date_text = "Бүх цаг үеийн"
        
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
            date_text = f"Энэ долоо хоног"
        elif "энэ сар" in query_lower:
            start_date = today.replace(day=1)
            filtered_df = filtered_df[filtered_df['огноо_өдөр'] >= start_date]
            date_text = f"Энэ сар ({start_date.strftime('%Y-%m')})"

        # Жолоочоор шүүх
        if driver_found:
            filtered_df = filtered_df[filtered_df['Жолооч'] == driver_found]
        # Бараагаар шүүх
        if product_filter:
            filtered_df = filtered_df[filtered_df['барааны нэр'].str.contains(product_filter, case=False)]

        total_orders = len(filtered_df)
        summary = filtered_df['мэдээ'].value_counts()
        
        # Мэдээ баганын мөрүүдийг шууд тоолж хувьсагчид авна
        delivered = summary.get('Хүргэсэн', 0)
        postponed = summary.get('Хойшлогдсон захиалга', 0)
        returned = summary.get('Буцаасан', 0)
        canceled = summary.get('Цуцалсан', 0)

        driver_info = f" Жолооч: **{driver_found}**" if driver_found else ""
        
        # Хариултын текстийг бэлдэх хэсэг
        bot_response = f"📅 **{date_text}**-ний{driver_info}{product_text} захиалгын мэдээлэл:\n\n"
        bot_response += f"• 📑 **Нийт бүртгэгдсэн захиалга:** {total_orders} ш\n"
        bot_response += f"• 📦 **Нийт хүргэсэн захиалга:** {delivered} ш\n"
        bot_response += f"--- \n"
        bot_response += f"• 🟩 **Хүргэсэн:** {delivered} ш\n"
        bot_response += f"• 🟨 **Хойшлогдсон захиалга:** {postponed} ш\n"
        bot_response += f"• 🟧 **Буцаасан:** {returned} ш\n"
        bot_response += f"• 🟥 **Цуцалсан:** {canceled} ш"

    # Үр дүнг чатад хэвлэх
    with st.chat_message("assistant"):
        st.write(bot_response)
    st.session_state.messages.append({"role": "assistant", "content": bot_response})