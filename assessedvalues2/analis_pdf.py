import pdfplumber


def anali_pdf():
    pdf_path = "K000100N40157510.pdf"

    with pdfplumber.open(pdf_path) as pdf:
        first_page = pdf.pages[1]  # Работаем только со второй страницей, индексация с 0

        vertical_lines = [330, 430]  # Пример координат X для вертикальных линий
        horizontal_lines = [190, 199, 205, 213, 221, 233]  # Пример координат Y для горизонтальных линий

        table_settings = {
            "vertical_strategy": "explicit",
            "explicit_vertical_lines": vertical_lines,
            "horizontal_strategy": "explicit",
            "explicit_horizontal_lines": horizontal_lines,
        }
        tables = first_page.extract_tables(table_settings)  # Передаем table_settings в метод

        # Если вы хотите визуализировать расположение таблиц на странице:
        image = first_page.to_image()
        image.debug_tablefinder(table_settings)
        image.save("analis.png")

        # Вывод таблицы (или таблиц)
        for table in tables:
            for row in table:
                print(row)


if __name__ == "__main__":
    anali_pdf()
