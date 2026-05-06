import streamlit as st
import time
import pandas as pd
import io
import functions as fn 
from openai import OpenAI

# --- 1. ХУУДАСНЫ ТОХИРГОО ---
st.set_page_config(
    page_title="CF - Data Chatbot", 
    page_icon="🤖",
    layout="wide"
)

# OpenAI Client тохиргоо (Түлхүүрийг .streamlit/secrets.toml-оос уншина)
# Хэрэв локал дээр туршиж байгаа бол st.secrets-ийн оронд api_key="таны_түлхүүр" гээд бичиж болно
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except:
    client = None

st.title("CF - Тех Карт & Аналитик Chatbot")

# --- 2. ӨГӨГДӨЛ АЧААЛАХ ---
@st.cache_data
def get_all_data():
    file_path = "data/turshilt ai.xlsx"
    try:
        raw_data = fn.load_and_preprocess(file_path)
        if raw_data is not None:
            report = fn.calculate_master_report(raw_data)
            return raw_data, report
    except Exception as e:
        st.error(f"Дата ачаалахад алдаа гарлаа: {e}")
    return None, None

raw_data, report_df = get_all_data()

# --- 3. CHAT SESSION CONTROL ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Сайн байна уу! Би Тех карт болон зардлын дата дээр суурилсан AI байна."}
    ]

# Өмнөх мессежүүдийг дэлгэцэнд зурах
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. CHAT USER PROMPT ---
prompt = st.chat_input("Танд юугаар туслах вэ?")

if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Мэдээллийг шүүж байна..."):
            user_input = prompt.lower()
            response = ""

            # --- A. ROUTING LOGIC (ХАТУУ НӨХЦӨЛҮҮД) ---
            
            # 1. Түүхий эдийн өртөг хайх
            ingredients_list = ["мах", "будаа", "гурил", "ногоо", "тос", "сонгино", "төмс", "лууван"]
            if any(x in user_input for x in ["өртөг", "үнэ"]) and any(i in user_input for i in ingredients_list):
                ing_name = next((i for i in ingredients_list if i in user_input), "")
                impact_results = fn.get_ingredient_impact(raw_data, ing_name)
                if impact_results is not None and not impact_results.empty:
                    response = f"📊 **'{ing_name.capitalize()}' орсон хоолнуудын зардал:**\n\n"
                    for _, row in impact_results.head(10).iterrows():
                        response += f"* **{row['hoolnii_ner']}**: {row['ingredient_cost']:.0f}₮\n"

            # 2. Ашигтай хоол хайх
            elif any(x in user_input for x in ["ашигтай", "top", "шилдэг"]):
                results = fn.get_top_profitable_foods(report_df)
                response = "📊 **Хамгийн өндөр ашигтай хоолнууд:**\n\n"
                for _, row in results.iterrows():
                    response += f"* **{row['hoolnii_ner']}**: {row['profit']:.0f}₮\n"

            # 3. Зөрүүтэй хоол хайх
            elif any(x in user_input for x in ["зөрүү", "варианс", "алдаа"]):
                results = fn.get_high_waste_foods(report_df)
                if not results.empty:
                    response = "⚠️ **Анхаарал хандуулах зөрүүтэй хоолнууд:**\n\n"
                    for _, row in results.iterrows():
                        response += f"* **{row['hoolnii_ner']}**: {row['variance']:.0f} порц\n"
                else:
                    response = "✅ Одоогоор их хэмжээний зөрүүтэй хоол алга байна."

            # --- B. OPENAI FALLBACK (ХЭРЭВ НӨХЦӨЛ ТААРАХГҮЙ БОЛ) ---
            else:
                if client:
                    try:
                        # Датанаас контекст бэлдэх (AI-д мэдээлэл өгөх)
                        context_data = report_df[['hoolnii_ner', 'unit_cost', 'profit']].head(10).to_string()
                        
                        ai_res = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {"role": "system", "content": f"Чи рестораны аналитик туслах. Дата: {context_data}"},
                                {"role": "user", "content": prompt}
                            ]
                        )
                        response = ai_res.choices[0].message.content
                    except Exception as e:
                        response = f"AI холболтонд алдаа гарлаа: {e}"
                else:
                    # Хэрэв OpenAI тохируулаагүй бол хуучин хайлтаа ажиллуулна
                    clean_name = user_input
                    for word in ["өртөг", "үнэ", "хоолны", "надад"]:
                        clean_name = clean_name.replace(word, "").strip()
                    
                    results = fn.get_food_details(report_df, clean_name)
                    if not results.empty:
                        res = results.iloc[0]
                        response = f"### 🍲 {res['hoolnii_ner']}\n* **Өртөг:** {res['unit_cost']:.0f}₮\n* **Ашиг:** {res['profit']:.0f}₮"
                    else:
                        response = "Уучлаарай, би таны асуултыг ойлгосонгүй. Та арай тодорхой асууна уу?"

            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

# --- 5. SIDEBAR ---
with st.sidebar:
    st.header("Тохиргоо")
    st.divider()
    
    if report_df is not None:
        # Excel файлыг санах ойд бэлдэх
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            report_df.to_excel(writer, index=False, sheet_name='Sheet1')
        
        st.download_button(
            label="📥 Тайлан татах (Excel)",
            data=output.getvalue(),
            file_name="food_analytics_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    if st.button("Чатыг цэвэрлэх"):
        st.session_state.messages = []
        st.rerun()