data = f'{None};{location};{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")};{link};{mail_address};{time_posted}'
for phone_number in phone_numbers:
    data = f'{phone_number};{location};{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")};{link};{mail_address};{time_posted}'
    print(f'{datetime.datetime.now().strftime("%H:%M:%S")} - {data} | (Поток -> {thread_id})')
    write_data(data=data, filename=filename)

# Разбиваем строку на переменные
_, location, timestamp, link, mail_address, time_posted = data.split(';')
date_part, time_part = timestamp.split(' ')

# Параметры для вставки в таблицу
site_id = 6  # id_site для 'https://gratka.pl/'

# Подключение к базе данных и запись данных
try:
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor(buffered=True)  # Используем buffered=True для извлечения всех результатов

    insert_announcement = (
        "INSERT INTO ogloszenia (id_site, poczta, adres, data, czas, link_do_ogloszenia, time_posted) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)"
    )

    announcement_data = (site_id, mail_address, location, date_part, time_part, link, time_posted)

    cursor.execute(insert_announcement, announcement_data)

    cnx.commit()  # Убедитесь, что изменения зафиксированы, прежде чем получить id

    # Получение id_ogloszenia с помощью SELECT-запроса
    select_query = (
        "SELECT id_ogloszenia FROM ogloszenia "
        "WHERE id_site = %s AND poczta = %s AND adres = %s AND data = %s AND czas = %s AND link_do_ogloszenia = %s AND time_posted = %s"
    )
    cursor.execute(select_query, (site_id, mail_address, location, date_part, time_part, link, time_posted))
    
    # Извлечение результата и проверка наличия данных
    result = cursor.fetchone()
    if result:
        id_ogloszenia = result[0]
    else:
        print("Не удалось получить id_ogloszenia")
        # Пропустить обработку, если id не найден
        raise ValueError("Не удалось получить id_ogloszenia")

    # Заполнение таблицы numbers, если номера телефонов присутствуют
    if phone_numbers and id_ogloszenia:
        phone_numbers_extracted, invalid_numbers = extract_phone_numbers(phone_numbers)
        valid_numbers = [num for num in phone_numbers_extracted if re.match(polish_phone_patterns["final"], num)]
        if valid_numbers:
            clean_numbers = ', '.join(valid_numbers)
        else:
            clean_numbers = 'invalid'

        insert_numbers = (
            "INSERT INTO numbers (id_ogloszenia, raw, correct) "
            "VALUES (%s, %s, %s)"
        )
        raw_numbers = ', '.join(phone_numbers)
        numbers_data = (id_ogloszenia, raw_numbers, clean_numbers)
        cursor.execute(insert_numbers, numbers_data)

        cnx.commit()
        print("Данные успешно добавлены в таблицы numbers и ogloszenia.")
    else:
        print("Нет номеров телефонов для добавления в таблицу numbers.")

except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Ошибка доступа: Неверное имя пользователя или пароль")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Ошибка базы данных: База данных не существует")
    else:
        print(err)
finally:
    cursor.close()
    cnx.close()
    print("Соединение с базой данных закрыто.")

    links_count = 1

    if os.path.exists(links_counter_file):
        with open(links_counter_file, 'r', encoding='utf-8') as f:
            total_links_count = int(f.read().strip())
            links_count += total_links_count

    with open(links_counter_file, 'w', encoding='utf-8') as f:
        f.write(str(links_count))

    with open(links_file, 'a', encoding='utf-8') as file:
        file.write(link + '\n')