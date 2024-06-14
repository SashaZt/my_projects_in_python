import pdfplumber
import matplotlib.pyplot as plt
import camelot
import tabula


def anali_pdf():
    pdf_path = "pdf1.pdf"

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
    pdf_path = "pdf1.pdf"

    with pdfplumber.open(pdf_path) as pdf:
        for page_no, page in enumerate(pdf.pages):
            # Настройки для обнаружения таблиц
            vertical_lines = [18, 192]  # Координаты x для вертикальных линий
            horizontal_lines = [
                15,
                25,
                40,
                51,
                63,
                76,
                88,
            ]  # Координаты y для горизонтальных линий
            # Стратегии могут быть: "lines", "text", "explicit"
            # Настройки для обнаружения таблиц
            table_settings = {
                "vertical_strategy": "explicit",
                "explicit_vertical_lines": vertical_lines,
                "horizontal_strategy": "explicit",
                "explicit_horizontal_lines": horizontal_lines,
                "snap_tolerance": 5,  # Толерантность при поиске линий (в пикселях)
                "join_tolerance": 5,  # Толерантность при объединении линий
                "edge_min_length": 50,  # Минимальная длина линий
                "min_words_vertical": 1,  # Минимальное количество слов для вертикальной линии
                "min_words_horizontal": 1,  # Минимальное количество слов для горизонтальной линии
            }
            tables = page.extract_tables(table_settings)

            # Выводим данные всех найденных таблиц
            for table_no, table in enumerate(tables):
                print(f"Страница №{page_no + 1}, Таблица №{table_no + 1}:")
                for row in table:
                    print(row)
                print("\n")  # Добавляем пустую строку для разделения таблиц

            # Визуализация поиска таблиц с настройками
            image = page.to_image()
            image.debug_tablefinder(table_settings)
            image.save("analis.png")


def visualize_page_layout():
    pdf_path = "pdf1.pdf"
    grid_step = 10
    page_number = 0
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_number]

        # Получаем текст и позиции слов на странице
        words = page.extract_words()

        # Визуализация разметки страницы с сеткой
        plt.figure(figsize=(20, 20))

        # Рисуем сетку
        for x in range(0, int(page.width), grid_step):
            plt.axvline(x, color="gray", linestyle="--", linewidth=0.5)
        for y in range(0, int(page.height), grid_step):
            plt.axhline(y, color="gray", linestyle="--", linewidth=0.5)

        # Рисуем текстовые блоки и их границы
        for word in words:
            x0, y0, x1, y1 = word["x0"], word["top"], word["x1"], word["bottom"]
            plt.plot([x0, x1], [y0, y0], "r-")  # Верхняя линия
            plt.plot([x0, x1], [y1, y1], "r-")  # Нижняя линия
            plt.plot([x0, x0], [y0, y1], "r-")  # Левая линия
            plt.plot([x1, x1], [y0, y1], "r-")  # Правая линия

            plt.text(x0, y0, word["text"], fontsize=8, color="blue")

        # Устанавливаем метки на шкале
        plt.xticks(range(0, int(page.width), grid_step))
        plt.yticks(range(0, int(page.height), grid_step))

        plt.xlim(0, page.width)
        plt.ylim(page.height, 0)  # Инвертируем ось Y для правильного отображения
        plt.title(f"Page {page_number + 1} Layout with {grid_step}px Grid")
        plt.xlabel("X (pixels)")
        plt.ylabel("Y (pixels)")
        plt.show()


def extract_tables_with_camelot():
    pdf_path = "pdf1.pdf"
    tables = camelot.read_pdf(pdf_path, pages="1", flavor="stream")

    for i, table in enumerate(tables):
        print(f"Таблица №{i + 1}:")
        print(table.df)
        print("\n")

    # Сохранение таблиц в CSV
    tables.export("tables.csv", f="csv", compress=True)


def extract_tables_with_tabula():
    pdf_path = "pdf1.pdf"

    # Задаем параметры для извлечения таблиц
    read_options = {
        "pages": "1",  # Страницы для извлечения
        "multiple_tables": True,  # Извлечение нескольких таблиц
        "guess": False,  # Отключить автоматическое распознавание границ
        "area": [
            50,
            50,
            800,
            600,
        ],  # Указать координаты области [top, left, bottom, right]
        "columns": [150, 300, 450],  # Указать позиции вертикальных границ колонок
        "stream": True,  # Использовать метод потока для извлечения
    }

    tables = tabula.read_pdf(pdf_path, **read_options)

    for i, table in enumerate(tables):
        print(f"Таблица №{i + 1}:")
        print(table)
        print("\n")

    # Сохранение таблиц в CSV
    tabula.convert_into(pdf_path, "tables.csv", output_format="csv", pages="1")


if __name__ == "__main__":
    # anali_pdf()
    anali_pdf_02()
    # visualize_page_layout()
    # extract_tables_with_camelot()
    # extract_tables_with_tabula()
