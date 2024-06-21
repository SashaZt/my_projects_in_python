import pdfplumber
from bs4 import BeautifulSoup
import os


def save_image(img, page_num, img_index):
    img_path = f"images/page_{page_num+1}_img_{img_index+1}.png"
    os.makedirs(os.path.dirname(img_path), exist_ok=True)
    img.save(img_path)
    return img_path


def pdf_to_html(pdf_path, html_path):
    # Открываем PDF файл
    with pdfplumber.open(pdf_path) as pdf:
        # Создаем HTML документ
        soup = BeautifulSoup(
            "<html><head><title>PDF to HTML</title></head><body></body></html>",
            "html.parser",
        )
        body = soup.body

        for page_num, page in enumerate(pdf.pages):
            # Создаем элемент <div> для каждой страницы
            page_div = soup.new_tag("div")
            page_div["class"] = "page"
            page_div["id"] = f"page_{page_num + 1}"

            # Извлекаем текст и таблицы с текущей страницы
            text = page.extract_text()
            tables = page.extract_tables()

            # Добавляем текст на страницу
            if text:
                for line in text.split("\n"):
                    line_p = soup.new_tag("p")
                    line_p.string = line
                    page_div.append(line_p)

            # Добавляем таблицы на страницу
            for table in tables:
                table_tag = soup.new_tag("table")
                for row in table:
                    row_tag = soup.new_tag("tr")
                    for cell in row:
                        cell_tag = soup.new_tag("td")
                        cell_tag.string = cell if cell else ""
                        row_tag.append(cell_tag)
                    table_tag.append(row_tag)
                page_div.append(table_tag)

            # Добавляем изображения на страницу
            images = page.images
            for img_index, img in enumerate(images):
                x0, y0, x1, y1 = img["x0"], img["y0"], img["x1"], img["y1"]
                img_crop = page.within_bbox((x0, y0, x1, y1)).to_image()
                img_path = save_image(img_crop.original, page_num, img_index)
                img_tag = soup.new_tag("img", src=img_path)
                page_div.append(img_tag)

            body.append(page_div)

    # Сохраняем HTML файл
    with open(html_path, "w", encoding="utf-8") as file:
        file.write(str(soup.prettify()))


if __name__ == "__main__":
    pdf_path = "Rishum_20_478603821Dupixent.pdf"  # Укажите путь к вашему PDF файлу
    html_path = "output.html"  # Укажите путь для сохранения HTML файла
    os.makedirs("images", exist_ok=True)  # Создаем папку для изображений
    pdf_to_html(pdf_path, html_path)
    print(f"PDF файл был успешно преобразован в HTML и сохранен как {html_path}")
