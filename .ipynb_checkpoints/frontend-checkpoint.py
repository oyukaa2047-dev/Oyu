import streamlit as st
import pandas as pd
import requests
import backend.functions as back
import re
import os

st.set_page_config(

    page_title="Way Academy - Demo chatbot", 

    page_icon="🤖"

)

st.title("Way  Academy - Demo chatbot")

st.info(

    """AI chatbot course deliverable demonstration"""

)


### Chat Session Control

if "messages" not in st.session_state:

    st.session_state.messages = []

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        if "output" in message.keys():

            st.markdown(message["output"])


if "waiting" not in st.session_state:

    st.session_state.waiting = False


### Chat user prompt & response generation

prompt = st.chat_input("Танд юугаар туслах вэ?", disabled=st.session_state.waiting)

if prompt:

    # Disable input while waiting for response

    st.chat_message("user").markdown(prompt)

    st.session_state.messages.append({"role": "user", "output": prompt})

    st.session_state.waiting = True

    st.rerun()

if st.session_state.waiting:

    last_prompt = st.session_state.messages[-1]["output"] if st.session_state.messages else prompt

    with st.spinner("Хариу бичиж байна..."):

        answer = {}

        answer['response'] = back.busiin_medeelel_avah(last_prompt)

    st.chat_message("assistant").markdown(answer['response'])

    st.session_state.messages.append({"role": "assistant", "output": answer['response']})

    # Re-enable input

    st.session_state.waiting = False

    st.rerun()

# 1. Хуудасны гарчиг
st.title("🗺️ Монгол улсын бүсийн мэдээлэл")

# 2. Датаг унших болон цэвэрлэх
# "таны_файл.xlsx" гэсэн хэсэгт өөрийн файлын нэрийг заавал зөв бичээрэй
df = pd.read_excel("backend/data/admin_units.xlsx") 

# Багануудыг шинээр нэрлэх
df = df.rename(columns={
    'МОНГОЛ УЛСЫН ЗАСАГ ЗАХИРГАА, НУТАГ ДЭВСГЭРИЙН НЭГЖ, бүс, аймаг, нийслэл, жилээр': 'Аймаг, нийслэл',
    'Unnamed: 1': 'Бүс',
    'Unnamed: 2': 'Код',
    'Unnamed: 3': '2025 он'
})

# Илүүдэл мөрүүдийг устгах
df = df.iloc[1:].reset_index(drop=True)
df['Бүс'] = df['Бүс'].str.strip() # Хоосон зайг цэвэрлэх

# 3. Хайлтын хэсэг
ner = st.text_input("Асуух бүсийн нэрээ оруулна уу (Жишээ нь: Баруун):")

# 4. Үр дүнг DataFrame болгож харуулах
if ner:
    # Шүүлтүүр хийх
    search_result = df[df['Бүс'].str.contains(ner, na=False, case=False)]
    
    if not search_result.empty:
        st.success(f"✅ '{ner}' бүсийн мэдээлэл:")
        # Үр дүнг хүснэгт хэлбэрээр харуулах
        st.dataframe(search_result, use_container_width=True)
        
        # Тоон мэдээллийг Metric-ээр харуулах
        total_value = pd.to_numeric(search_result['2025 он'], errors='coerce').sum()
        st.metric(label=f"{ner} бүсийн 2025 оны нийт дүн", value=f"{total_value:,.0f}")
    else:
        st.warning(f"⚠️ '{ner}' нэртэй бүс олдсонгүй.")
else:
    st.info("Дээрх талбарт бүсийн нэрээ бичээд Enter дарна уу.")
    st.write("Нийт мэдээллийн жагсаалт:", df)


# --- 1. ӨГӨГДӨЛ УНШИХ ---
@st.cache_data
def load_data():
    df = pd.read_csv("backend/data/salary.csv")
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