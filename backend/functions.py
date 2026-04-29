import pandas as pd
import streamlit as st
import re
import os


# --- 1. ӨГӨГДӨЛ УНШИХ БА ЦЭВЭРЛЭХ ХЭСЭГ ---
# Файлын замыг өөрийнхөөрөө зөв зааж өгөх (жишээ нь: "data/admin_units.xlsx")
df = pd.read_excel("backend/data/admin_units.xlsx")

# Багануудыг шинэчлэн нэрлэх (Зураг дээрхтэй адил болгох)
df = df.rename(columns={
    'МОНГОЛ УЛСЫН ЗАСАГ ЗАХИРГАА, НУТАГ ДЭВСГЭРИЙН НЭГЖ, бүс, аймаг, нийслэл, жилээр': 'Аймаг_нийслэл',
    'Unnamed: 1': 'Бүс',
    'Unnamed: 2': 'Код',
    'Unnamed: 3': '2025 он'
})

# Дээд талын илүүдэл 1 мөрийг устгаж, индексийг шинэчлэх
df = df.iloc[1:].reset_index(drop=True)

# Бүс баганын сул зайг цэвэрлэх (Хайлт алдаагүй ажиллахад чухал)
df['Бүс'] = df['Бүс'].str.strip()


# --- 2. ФУНКЦ ТОДОРХОЙЛОХ ХЭСЭГ ---
def busiin_medeelel_avah(busiin_ner):
    """Хэрэглэгчийн оруулсан нэрээр бүсийг шүүж DataFrame буцаана"""
    result = df[df['Бүс'].str.contains(busiin_ner, na=False, case=False)]
    return result


# --- 3. STREAMLIT ХЭРЭГЛЭГЧИЙН ХАРАГДАЦ (UI) ---
st.title("🗺️ Бүсийн мэдээлэл хайх систем")

# Хэрэглэгчээс хайх утгыг авах
ner = st.text_input("Хайх бүс эсвэл аймгийн нэрээ оруулна уу:")

if ner:
    # Функцээ дуудаж үр дүнг авах
    search_result = busiin_medeelel_avah(ner)
    
    if not search_result.empty:
        st.success(f"✅ '{ner}' нэртэй илэрц олдлоо:")
        # Үр дүнг интерактив хүснэгтээр харуулах
        st.dataframe(search_result, use_container_width=True)
        
        # Нэмэлт: 2025 оны нийт дүнг тооцоолж харуулах
        total = pd.to_numeric(search_result['2025 он'], errors='coerce').sum()
        st.metric(label="2025 оны нийт дүн", value=f"{total:,.0f}")
    else:
        st.warning(f"⚠️ '{ner}' нэртэй мэдээлэл олдсонгүй. Өөр нэрээр хайж үзнэ үү.")
else:
    st.info("Дээрх талбарт хайх утгаа бичнэ үү.")
    # Эхний удаад бүх датаг харуулах (Сонголтоор)
    st.write("Нийт өгөгдлийн жагсаалт:", df)




# --- 1. ӨГӨГДӨЛ УНШИХ ---
@st.cache_data
def load_data():
    df = pd.read_csv("backend/data/salary - salary.csv")
    df.columns = [str(col).strip() for col in df.columns]
    return df

df = load_data()

# --- 2. ТЕКСТЭЭС МЭДЭЭЛЭЛ ШҮҮХ ФУНКЦ ---
def answer_question(user_input):
    # Бүс/Аймгийн жагсаалт
    regions = df['Аймаг'].unique().tolist()
    # Хүйсийн жагсаалт
    genders = df['Хүйс'].unique().tolist()
    # Онуудын жагсаалт
    years = [col for col in df.columns if col.isdigit()]

    # Хэрэглэгчийн бичсэн текст дотроос түлхүүр үгсийг хайх
    found_region = next((r for r in regions if r.lower() in user_input.lower()), None)
    found_gender = next((g for g in genders if g.lower() in user_input.lower()), "Бүгд")
    found_year = next((y for y in years if y in user_input), "2024") # Байхгүй бол 2023-ыг авна

    if found_region:
        # Датаг шүүх
        result = df[(df['Аймаг'] == found_region) & (df['Хүйс'] == found_gender)]
        
        if not result.empty:
            salary = result[found_year].values[0]
            return f"📍 **{found_region}**-ийн **{found_gender}** ажилчдын **{found_year}** оны дундаж цалин: **{salary:,.0f} ₮** байна."
        else:
            return "Уучлаарай, энэ үзүүлэлтээр мэдээлэл олдсонгүй."
    else:
        return "Та асуултандаа аймаг эсвэл бүсийн нэрээ оруулна уу. (Жишээ нь: 'Зүүн бүсийн цалин хэд вэ?')"

# --- 3. STREAMLIT CHAT UI ---
st.title("🤖 Цалингийн ухаалаг туслах")
st.info("Та асуултаа бичнэ үү. Жишээ нь: 'Баруун бүсийн эмэгтэйчүүдийн 2022 оны цалин?'")

# Чатны түүхийг хадгалах
if "messages" not in st.session_state:
    st.session_state.messages = []

# Өмнөх зурвасуудыг харуулах
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Хэрэглэгчийн асуулт авах хэсэг
if prompt := st.chat_input("Энд бичнэ үү..."):
    # Хэрэглэгчийн асуултыг харуулах
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Хариу боловсруулах
    with st.chat_message("assistant"):
        response = answer_question(prompt)
        st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})