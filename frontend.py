import streamlit as st
import time
import pandas as pd
import numpy as np
import os
import datetime
import backend.functions as back

st.set_page_config(
    page_title="Way Academy - Data Chatbot", 
    page_icon="🤖"
)

st.title("Way Academy - Тех Карт Chatbot")
st.info(
    """Энэхүү AI chatbot нь Тех карт болон өртгийн мэдээллээс хайлт хийнэ. 
    Та Хоолны нэр, ID, эсвэл Түүхий эдийн мэдээллээ бичнэ үү."""
)

### Chat Session Control
if "messages" not in st.session_state:
    st.session_state.messages = []

# Өмнөх мессежүүдийг харуулах
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["output"])

if "waiting" not in st.session_state:
    st.session_state.waiting = False

### Chat user prompt & response generation
prompt = st.chat_input("Танд юугаар туслах вэ? (Жишээ нь: Цуйван, H001, 2024-05)", disabled=st.session_state.waiting)

if prompt:
    # Хэрэглэгчийн мессежийг харуулах
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "output": prompt})
    st.session_state.waiting = True
    st.rerun()

if st.session_state.waiting:
    last_prompt = st.session_state.messages[-1]["output"]
    
    with st.spinner("Мэдээллийг шүүж байна..."):
        # Backend-ээс хариу авах
        response = back.handle_user_query(last_prompt)
        time.sleep(0.5) # Бага зэрэг хүлээлт үүсгэх (илүү амьд болгох)

    # Туслахын хариуг харуулах
    with st.chat_message("assistant"):
        st.markdown(response)
        
    st.session_state.messages.append({"role": "assistant", "output": response})
    st.session_state.waiting = False
    st.rerun()