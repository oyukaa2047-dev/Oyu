import pandas as pd
import streamlit as st
def busiin_medeelel_avah(busiin_ner):
    # Хайлт хийх
    result = df[df['Бүс'].str.contains(busiin_ner, na=False, case=False)]
    
    if result.empty:
        # Хэрэв юу ч олдоогүй бол хоосон DataFrame буцаана
        print(f"⚠️ '{busiin_ner}' нэртэй бүс олдсонгүй.")
        return pd.DataFrame() 
    
    return result

# --- Ашиглах хэсэг ---
ner = input("Асуух бүсийн нэрээ оруулна уу: ")
search_result = busiin_medeelel_avah(ner)

# Хэрэв үр дүн хоосон биш бол хүснэгтээр харуулна
if not search_result.empty:
    print(f"\n✅ {ner} бүсийн мэдээлэл:")
    # Хэрэв та Jupyter дээр байгаа бол: display(search_result)
    print(search_result.to_string(index=False)) # Индексгүйгээр цэвэрхэн хэвлэх