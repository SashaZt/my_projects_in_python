import pdfplumber


def anali_pdf():
    pdf_path = "K000100N40157510.pdf"

    with pdfplumber.open(pdf_path) as pdf:
        first_page = pdf.pages[0]  # Работаем только с первой страницей
        
        # vertical_lines = [145,  140]  # Пример координат X для вертикальных линий
        # horizontal_lines = [175,  230]  # Пример координат Y для горизонтальных линий

        # table_settings = {
        #     "vertical_strategy": "explicit",
        #     "explicit_vertical_lines": vertical_lines,
        #     "horizontal_strategy": "explicit",
        #     "explicit_horizontal_lines": horizontal_lines,
        # }
        image = first_page.to_image()
        image.debug_tablefinder()

        # image.debug_tablefinder(table_settings)
        image.save("analis.png")


if __name__ == "__main__":
    anali_pdf()
