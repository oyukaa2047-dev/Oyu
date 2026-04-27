import pandas as pd
import streamlit as st

# --- 1. ӨГӨГДӨЛ УНШИХ БА ЦЭВЭРЛЭХ ХЭСЭГ ---
# Файлын замыг өөрийнхөөрөө зөв зааж өгөх (жишээ нь: "data/admin_units.xlsx")
df = pd.read_exce("backend/data/admin_units.xlsx")

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