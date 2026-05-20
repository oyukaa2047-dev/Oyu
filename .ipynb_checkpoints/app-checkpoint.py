import pandas as pd
import streamlit as st
import numpy as np
import re
import warnings
from datetime import datetime, timedelta

# 1. Тохиргоо болон Анхааруулга хаах
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# Стримлит хуудасны тохиргоо
st.set_page_config(page_title="CF - Тех Карт & Аналитик Chatbot", page_icon="💬", layout="centered")

# 2. ДАТА УНШИХ БОЛОН ЦЭВЭРЛЭХ ФУНКЦ (Гүйцэтгэлийг хурдан байлгах үүднээс cache ашиглав)
@st.cache_data
def load_and_clean_data():
    file_path = "data/best_hurgelt.xlsx"
    all_sheets = pd.read_excel(file_path, sheet_name=None)
    zah_huu_df = all_sheets["зах хуу"]
    
    # Шаардлагатай багануудыг шүүж авах
    zah_huu_df = zah_huu_df.loc[:, :'мэдээ']
    
    # А. Огноо (он сар) баганыг засаж, дүүргэх (Forward Fill)
    zah_huu_df['он сар'] = zah_huu_df['он сар'].astype(str).str.strip()
    zah_huu_df['он сар'] = zah_huu_df['он сар'].replace(['nan', 'None', ''], np.nan)
    zah_huu_df['он сар'] = zah_huu_df['он сар'].replace('1/3', '2026-01-03')
    
    # Дээд утгаар нөхөх
    zah_huu_df['он сар'] = zah_huu_df['он сар'].ffill()
    zah_huu_df['он сар'] = pd.to_datetime(zah_huu_df['он сар'], errors='coerce')
    zah_huu_df['огноо_өдөр'] = zah_huu_df['он сар'].dt.date
    
    # Б. Барааны нэр болон Жолооч баганыг цэвэрлэх
    zah_huu_df.dropna(subset=['барааны нэр'], inplace=True)
    zah_huu_df.rename(columns={'Unnamed: 4': 'Жолооч'}, inplace=True)
    
    zah_huu_df['Жолооч'] = zah_huu_df['Жолооч'].fillna('').astype(str).str.strip().str.capitalize()
    
    # Жолооч нэрс ижилсүүлэх
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
    
    # В. Тусгай нөхцөлөөр утасны дугаар зоож өгөх
    zah_huu_df['барааны нэр'] = zah_huu_df['барааны нэр'].fillna('').astype(str)
    tengsu_нөхцөл = zah_huu_df['барааны нэр'].str.contains('Эр бэлдмэл Tengsu-1,', case=False, na=False)
    zah_huu_df.loc[tengsu_нөхцөл, 'утас'] = 99335584
    
    # Жолоочгүй мөрүүдийн утсыг 0 болгох
    zah_huu_df.loc[zah_huu_df['Жолооч'].isna() | (zah_huu_df['Жолооч'] == ''), 'утас'] = 0
    
    # Г. "Мэдээ" баганыг 4 төлөвт ухаалгаар ангилах
    хүргэсэн_үгс = [
        'хүргэсэн', 'хүрэгсэн', 'хүргэгдсэн', 'хүргэсэн ', 'өглөөгүүр хүргэсэн', 'өнөөдөр хүргэлтээр авсан',
        'авсан', 'өч авсан', 'өчигдөр авсан', 'авчихсан', 'сольж өгсөн', 'сольсон', 'тавагаар сольно', 
        'солиулах', 'хүргэсэн буцаж очиж солино', 'ажлын өдөр', 'аж өдөр', '1дэх өдөр', 'бодио', 'баяраа', 
        'анар', 'туул', 'ээгиййд', 'дархан мэндээ', '1.12', 'зоригоо', 'багана'
    ]
    
    буцаасан_үгс = [
        'буцаасан', 'буцаав', 'буцаана', 'буцаалт авсан', 'буцаасан хулхи', 'буцаав согтуу',
        'үзээд аваагүй буцаав', 'үзээд буцаав', 'үзээд буцаасан 5к', 'бараа тавьсаын дараа буц', 'үзээд болисон', 
        'үзээд аваагүй', 'голсон', 'голов', 'жижиг байна гээд голов', 'жижиг байна', 'голсон жижиг', 'голсон аваагүй', 
        'голсон авахгүй', 'зураг шигээ биш  гээд голсон', 'зурагнаасаа өөр бна', 'өөр бна гээд буцаав', 'хайрцаггүй гэж голсон', 
        'таараагүй', 'өөр маск', 'үнэтэй байна буцаж авсан', '29к бол авна буцаав', 'хиртэй бна гсн', 'голсон буцаж очиж ав', 
        'голсон буцаж очиж авав', 'буцаж очиж авсан', 'буцаж очиж авна голсон', 'буцаана очиж авсан', 'хэрэглээд тасарсан буцаав', 
        'авчихсан гээд буцаав', 'мөнгөө хийхгүй буцаж очиж авсан', 'мөнгө хийхгүй бна буцаж очиж авна', 'мөнгө өгөхгүй гээд очиж авна', 
        'буцаасан мөнгө хийгээгүй', 'хүргээд буцаж очиж авсан'
    ]
    
    хойшлогдсон_үгс = [
        'хойшилсон', 'хойш', 'захиалгаа хойшлуулсан', 'маргааш', 'мар', 'худ мар', 'худ уа мсж', 'худ', 
        'худ голдэн будда', 'маргааш авна', 'маргааш авна цалин буугаад', 'маргааш авахаар болсон', 
        'маргааш авахаар болсо', 'мар яг авна', 'мар 4с өмнө', 'мар бүс', 'мар өөр хаяг др', 'мар ажлын цагаар', 
        'мар 3хл', 'мар төмөр зам', 'мар тэнгэр', 'өч өгсөн', 'тэц газар шим мар', 'гурвалжин гүүр мар', 
        'амжаагүй', 'татан авалт', 'татан авалт ', ' татан авалт', 'хугацаанаас хоцорсон ', 'хугацаа дууссан', 
        'дараа', 'дараа яриж бгаад авна', 'ярьж байгаад авна', 'яриж байгаад ирэх', 'өөрөө залгана', 'аваагүй', 
        'мэдэхгүй', 'очиж авна', 'орой авна', 'заавал орой авна', 'орой', '7с хойш', '8с хойш', '17 цаг хүртэл', 
        'өглөө эрт авна', 'амралтын өдөр авна', 'amaraltiin odor awna gesen genee', '1/9 нд авна', '1/10', 
        '01/14', '01/15', '01/20', '01/22', '01/31 авна гэж хэлсэн', '2.3 хоногийн өмнө захисан мар ямартай ч ярь'
    ]

    def утгаар_ангилах(утга):
        if pd.isna(утга) or утга == '':
            return 'Цуцалсан'
        if isinstance(утга, (pd.Timestamp, type(pd.NaT))) or 'datetime' in str(type(утга)):
            return 'Хүргэсэн'
        
        цэвэр_утга = str(утга).strip().lower()
        
        тусгай_цуцлах_үгс = ['аптекаас авсан', 'ooriig awtsan', 'жолоочид хувиарласан']
        if цэвэр_утга in тусгай_цуцлах_үгс or 'дэлгүүрт үлдээ' in цэвэр_утга:
            return 'Цуцалсан'
            
        if цэвэр_утга in хүргэсэн_үгс:
            return 'Хүргэсэн'
        elif цэвэр_утга in буцаасан_үгс:
            return 'Буцаасан'
        elif цэвэр_утга in хойшлогдсон_үгс:
            return 'Хойшлогдсон захиалга'
        return 'Цуцалсан'

    # Төлөвийн хувиргалтыг хийх
    zah_huu_df['мэдээ'] = zah_huu_df['мэдээ'].apply(утгаар_ангилах)
    return zah_huu_df

# Датаг ачаалах
try:
    zah_huu_df = load_and_clean_data()
except Exception as e:
    st.error(f"Дата уншихад алдаа гарлаа: {e}. Файлын зам зөв эсэхийг шалгана уу.")
    st.stop()

# 3. ТЕКСТЭЭС ОГНОО ШҮҮЖ АВАХ ФУНКЦ
def extract_date_from_text(text):
    date_pattern = r'(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})'
    match = re.search(date_pattern, text)
    if match:
        year, month, day = match.groups()
        return datetime(int(year), int(month), int(day)).date()
    return None

# 4. ЧАТБОТ ИНТЕРФЭЙС
st.title("💬 Online Chatbot")
st.write("Захиалгын мэдээллийг тодорхой огноогоор эсвэл ерөнхий өдрөөр асуугаарай. (ж.нь: `2026-01-03-ний өдөр нийт захиалга хэд байна?`)")

# Сессийн түүх үүсгэх
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Сайн байна уу! Би захиалгын аналитик туслах байна. Та асуултаа үлдээнэ үү."}
    ]

# Өмнөх чатыг хэвлэх
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Шинэ асуулт авах хэсэг
if user_query := st.chat_input("Асуултаа энд бичнэ үү..."):
    with st.chat_message("user"):
        st.write(user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    query_lower = user_query.lower()
    
    # Огноог regex-ээр хайх
    target_date = extract_date_from_text(user_query)
    
    if target_date:
        date_text = str(target_date)
    else:
        # Хэрэв шууд огноо бичээгүй бол түлхүүр үгсээр хайх
        if "өчигдөр" in query_lower:
            target_date = datetime.today().date() - timedelta(days=1)
            date_text = "Өчигдөр"
        elif "уржигдар" in query_lower:
            target_date = datetime.today().date() - timedelta(days=2)
            date_text = "Уржигдар"
        else:
            target_date = datetime.today().date()
            date_text = "Өнөөдөр"

    # Датаг огноогоор шүүж тоолох
    daily_df = zah_huu_df[zah_huu_df['огноо_өдөр'] == target_date]
    total_orders = len(daily_df)
    summary = daily_df['мэдээ'].value_counts()
    
    # Хариултыг таны хүссэн яг таг форматаар бэлдэх
    bot_response = f"📅 **{date_text}**-ний өдрийн захиалгын нэгдсэн мэдээлэл:\n\n"
    bot_response += f"• **Нийт захиалга:** {total_orders}ш\n"
    bot_response += f"--- \n"
    bot_response += f"• 🟩 **Хүргэсэн:** {summary.get('Хүргэсэн', 0)}ш\n"
    bot_response += f"• 🟨 **Хойшлогдсон захиалга:** {summary.get('Хойшлогдсон захиалга', 0)}ш\n"
    bot_response += f"• 🟧 **Буцаасан:** {summary.get('Буцаасан', 0)}ш\n"
    bot_response += f"• 🟥 **Цуцалсан:** {summary.get('Цуцалсан', 0)}ш"

    # Ботын хариултыг дэлгэцэнд гаргах, хадгалах
    with st.chat_message("assistant"):
        st.write(bot_response)
    st.session_state.messages.append({"role": "assistant", "content": bot_response})