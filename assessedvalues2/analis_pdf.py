import pdfplumber


def anali_pdf():
    pdf_path = "Woolwich, ME.pdf"

    with pdfplumber.open(pdf_path) as pdf:
        first_page = pdf.pages[0]  # Работаем только со второй страницей, индексация с 0

        # vertical_lines = [330, 430]  # Пример координат X для вертикальных линий
        # horizontal_lines = [190, 199, 205, 213, 221, 233]  # Пример координат Y для горизонтальных линий

        # table_settings = {
        #     "vertical_strategy": "explicit",
        #     "explicit_vertical_lines": vertical_lines,
        #     "horizontal_strategy": "explicit",
        #     "explicit_horizontal_lines": horizontal_lines,
        # }
        # tables = first_page.extract_tables(table_settings)  # Передаем table_settings в метод

        # Если вы хотите визуализировать расположение таблиц на странице:
        image = first_page.to_image()
        image.debug_tablefinder()
        # image.debug_tablefinder(table_settings)
        image.save("analis.png")

        # # Вывод таблицы (или таблиц)
        # for table in tables:
        #     for row in table:
        #         print(row)
def anali_pdf_02():
    pdf_path = "Woolwich, ME.pdf"

    with pdfplumber.open(pdf_path) as pdf:
        first_page = pdf.pages[1]

        # Настройки для обнаружения таблиц
        table_settings = {
            # Стратегии могут быть: "lines", "text", "explicit"
            "vertical_strategy": "text", 
            "horizontal_strategy": "text",
            
            # Для стратегии "explicit" необходимо явно указать координаты линий:
            # "explicit_vertical_lines": [x1, x2, ...],
            # "explicit_horizontal_lines": [y1, y2, ...],
            
            # Можно настроить дополнительные параметры:
            "snap_tolerance": 3,  # Толерантность при поиске линий (в пикселях)
            "join_tolerance": 3,  # Толерантность при объединении линий
            "edge_min_length": 3,  # Минимальная длина линий
            "min_words_vertical": 3,  # Минимальное количество слов для вертикальной линии
            "min_words_horizontal": 3,  # Минимальное количество слов для горизонтальной линии
        }
        tables = first_page.extract_tables(table_settings)

        # Выводим данные всех найденных таблиц
        for table_no, table in enumerate(tables):
            print(f"Таблица №{table_no + 1}:")
            for row in table:
                print(row)
            print("\n")  # Добавляем пустую строку для разделения таблиц
        # Визуализация поиска таблиц с настройками
        image = first_page.to_image()
        image.debug_tablefinder(table_settings)
        image.save("analis.png")


if __name__ == "__main__":
    # anali_pdf()
    anali_pdf_02()
