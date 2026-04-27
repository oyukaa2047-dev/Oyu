import streamlit as st
import pandas as pd
import requests
import backend.functions as back

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

        answer['response'] = back.handle_user_query(last_prompt)

    st.chat_message("assistant").markdown(answer['response'])

    st.session_state.messages.append({"role": "assistant", "output": answer['response']})

    # Re-enable input

    st.session_state.waiting = False

    st.rerun()

# 1. Хуудасны гарчиг
st.title("🗺️ Монгол улсын бүсийн мэдээлэл")

# 2. Датаг унших болон цэвэрлэх
# "таны_файл.xlsx" гэсэн хэсэгт өөрийн файлын нэрийг заавал зөв бичээрэй
df = pd.read_excel("backend/data/admin_units.xlsx"") 

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