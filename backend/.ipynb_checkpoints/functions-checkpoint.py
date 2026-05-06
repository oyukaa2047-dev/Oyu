import pandas as pd
import os
import re

def cyrillic_to_latin(text):
    """Кириллээр бичсэн текстийг Латин руу хөрвүүлэх (Хайлтад зориулсан)"""
    char_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'j', 'з': 'z', 'и': 'i', 'й': 'i', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'ө': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
        'у': 'u', 'ү': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh',
        'щ': 'sh', 'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
    }
    text = text.lower()
    return "".join(char_map.get(c, c) for c in text)

def load_and_process_data():
    file_path = "data/turshilt ai.xlsx"
    if not os.path.exists(file_path):
        return None

    df_tech = pd.read_excel(file_path, sheet_name='Тех карт')
    df_urtug = pd.read_excel(file_path, sheet_name='Sheet4')

    df_tech.columns = df_tech.columns.str.strip()
    df_urtug.columns = df_urtug.columns.str.strip()

    # Огноонуудыг хөрвүүлэх
    date_cols = ['effective_date', 'expiry_date']
    for col in date_cols:
        if col in df_tech.columns:
            df_tech[col] = pd.to_datetime(df_tech[col])
    
    df_urtug['effective_date'] = pd.to_datetime(df_urtug['effective_date'])

    # Сар бүрээр нэгтгэх
    df_tech['year_month'] = df_tech['effective_date'].dt.to_period('M')
    df_urtug['year_month'] = df_urtug['effective_date'].dt.to_period('M')

    urtug_average = df_urtug.groupby(['Buteegdehuunii_id', 'year_month'])['urtug_une'].mean().reset_index()
    urtug_average.rename(columns={'urtug_une': 'average_urtug'}, inplace=True)

    df_final = pd.merge(df_tech, urtug_average, on=['Buteegdehuunii_id', 'year_month'], how='left')
    df_final = df_final.drop(columns=['year_month'])
    
    return df_final

def handle_user_query(query):
    df = load_and_process_data()
    if df is None: return "Мэдээллийн файл олдсонгүй."

    raw_query = query.lower().strip()
    latin_query = cyrillic_to_latin(raw_query) # Кирилл бол латин руу хөрвүүлж шалгах

    # --- 1. АНАЛИТИК ХАЙЛТ (Нийт өртөг) ---
    if "нийт өртөг" in raw_query or "niit urtug" in latin_query:
        # Хэрэв тодорхой огноо дурдсан бол (Жишээ нь: 2026-01-31)
        date_match = re.search(r'\d{4}.\d{2}.\d{2}', raw_query)
        temp_df = df.copy()
        if date_match:
            target_date = pd.to_datetime(date_match.group())
            temp_df = temp_df[temp_df['effective_date'] <= target_date].sort_values('effective_date').groupby(['Hoolnii_id', 'Buteegdehuunii_id']).last().reset_index()
        
        temp_df['row_cost'] = temp_df['Hemjee'] * temp_df['average_urtug']
        hool_summary = temp_df.groupby('Hoolnii_ner')['row_cost'].sum().reset_index()
        
        res = "💰 **Хоол тус бүрийн нийт өртөг:**\n"
        for _, r in hool_summary.iterrows():
            res += f"- {r['Hoolnii_ner']}: {r['row_cost']:,.2f}₮\n"
        return res

    # --- 2. ӨСӨЛТ БУУРАЛТ ШАЛГАХ ---
    if "өссөн" in raw_query or "буурсан" in raw_query or "ussen" in latin_query:
        # Энэ хэсэгт сүүлийн 2 сарын өртгийг харьцуулах логик орно
        return "📈 Өртгийн өөрчлөлтийг тооцоолж байна... (Сүүлийн саруудын мэдээллийг харьцуулж харна уу)"

    # --- 3. ЕРДИЙН ХАЙЛТ (Латин/Кирилл үсэг хамаарахгүй) ---
    # Хэрэглэгчийн хайлтыг багана бүрээр шалгах
    def search_logic(row):
        for val in row.values:
            str_val = str(val).lower()
            if raw_query in str_val or latin_query in cyrillic_to_latin(str_val):
                return True
        return False

    mask = df.apply(search_logic, axis=1)
    result = df[mask]

    if result.empty:
        return f"'{query}' утгатай холбоотой мэдээлэл олдсонгүй."

    # Үр дүнг форматлах
    response = f"🔍 '{query}' хайлтад {len(result)} илэрц олдлоо:\n\n"
    for _, row in result.head(10).iterrows():
        response += f"🍴 **{row['Hoolnii_ner']}** ({row['Damjlaga']})\n"
        response += f"   - Бүрэлдэхүүн: {row['Buteegdehuunii_ner']} ({row['Hemjee']} {row['Hemjih_negj']})\n"
        response += f"   - Нэгж өртөг: {row['average_urtug']:,.2f}₮\n"
        response += f"   - Огноо: {row['effective_date'].strftime('%Y-%m-%d')}\n---\n"
    
    return response
# --- ЛОГИК 4: ХАМГИЙН ӨНДӨР ӨРТӨГТЭЙ ХООЛ ---
    if "үнэтэй" in q_low or "unetei" in q_lat:
        current_df['total'] = current_df['Hemjee'] * current_df['average_urtug']
        top_hool = current_df.groupby('Hoolnii_ner')['total'].sum().sort_values(ascending=False).head(3)
        msg = "🥇 **Хамгийн өндөр өртөгтэй ТОП 3 хоол:**\n"
        for i, (name, val) in enumerate(top_hool.items(), 1):
            msg += f"{i}. {name}: **{val:,.2f}₮**\n"
        return msg