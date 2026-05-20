# Г. ҮР ДҮН ТООЦООЛОХ БОЛОН ХАРИУЛТ БЭЛДЭХ ЛОГИК
    bot_response = ""

    # Нөхцөл 1: Зөвхөн Жолоочийн нэр хэлсэн бөгөөд хугацаа заагаагүй бол (Өнөөдөр, 7 хоног, Сарын нэгдсэн статистик харуулна)
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
        
        # Чатботын хариултыг бэлдэх хэсэг
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