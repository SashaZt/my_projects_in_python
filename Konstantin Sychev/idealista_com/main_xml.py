import uuid
from xml.dom import minidom

from lxml import etree


def property_to_xml(property_data):
    # Определение пространств имен
    nsmap = {
        None: "http://wordpress.org/export/1.2/",  # Default namespace
        "excerpt": "http://wordpress.org/export/1.2/excerpt/",
        "content": "http://purl.org/rss/1.0/modules/content/",
        "wfw": "http://wellformedweb.org/CommentAPI/",
        "dc": "http://purl.org/dc/elements/1.1/",
        "wp": "http://wordpress.org/export/1.2/",
    }

    # Корневой элемент с пространствами имен
    rss = etree.Element("rss", version="2.0", nsmap=nsmap)

    channel = etree.SubElement(rss, "channel")

    # Основные метаданные канала (это пример, корректируйте в соответствии с вашими данными)
    etree.SubElement(channel, "title").text = "Your Site Name"
    etree.SubElement(channel, "link").text = "https://example.com"
    etree.SubElement(channel, "description").text = "Your site description"
    etree.SubElement(channel, "pubDate").text = "Mon, 31 Dec 2024 18:15:04 +0000"
    etree.SubElement(channel, "language").text = "en-US"
    etree.SubElement(channel, "wxr_version").text = "1.2"
    etree.SubElement(channel, "base_site_url").text = "https://example.com"
    etree.SubElement(channel, "base_blog_url").text = "https://example.com"

    # Создаем элемент item для свойства
    item = etree.SubElement(channel, "item")

    # Заполняем item данными из property_data
    etree.SubElement(item, "title").text = etree.CDATA(property_data["title"])
    etree.SubElement(item, "link").text = (
        "https://example.com/property/"  # пример ссылки
    )
    etree.SubElement(item, "pubDate").text = (
        "Mon, 31 Dec 2024 18:15:04 +0000"  # пример даты
    )
    etree.SubElement(item, "creator").text = etree.CDATA("admin")  # пример автора
    etree.SubElement(item, "guid", {"isPermaLink": "false"}).text = "example-guid"
    etree.SubElement(item, "description").text = ""
    etree.SubElement(item, "{%s}encoded" % nsmap["content"]).text = etree.CDATA(
        property_data.get("content", "")
    )
    etree.SubElement(item, "{%s}encoded" % nsmap["excerpt"]).text = etree.CDATA(
        property_data.get("excerpt", "")
    )

    # Добавляем id для поста
    etree.SubElement(item, "{%s}post_id" % nsmap["wp"]).text = str(uuid.uuid4())

    # Добавляем даты для поста
    etree.SubElement(item, "{%s}post_date" % nsmap["wp"]).text = etree.CDATA(
        "2024-12-31 18:15:04"
    )
    etree.SubElement(item, "{%s}post_date_gmt" % nsmap["wp"]).text = etree.CDATA(
        "2024-12-31 18:15:04"
    )
    etree.SubElement(item, "{%s}post_modified" % nsmap["wp"]).text = etree.CDATA(
        "2024-12-31 18:15:04"
    )
    etree.SubElement(item, "{%s}post_modified_gmt" % nsmap["wp"]).text = etree.CDATA(
        "2024-12-31 18:15:04"
    )

    # Прочие метаданные поста
    etree.SubElement(item, "{%s}comment_status" % nsmap["wp"]).text = etree.CDATA(
        "closed"
    )
    etree.SubElement(item, "{%s}ping_status" % nsmap["wp"]).text = etree.CDATA("closed")
    etree.SubElement(item, "{%s}post_name" % nsmap["wp"]).text = etree.CDATA(
        property_data["title"].lower().replace(" ", "-")
    )
    etree.SubElement(item, "{%s}status" % nsmap["wp"]).text = etree.CDATA(
        property_data.get("status", "publish")
    )
    etree.SubElement(item, "{%s}post_parent" % nsmap["wp"]).text = "0"
    etree.SubElement(item, "{%s}menu_order" % nsmap["wp"]).text = "0"
    etree.SubElement(item, "{%s}post_type" % nsmap["wp"]).text = etree.CDATA(
        property_data.get("type", "property")
    )
    etree.SubElement(item, "{%s}post_password" % nsmap["wp"]).text = etree.CDATA("")
    etree.SubElement(item, "{%s}is_sticky" % nsmap["wp"]).text = "0"

    # Добавляем метаданные
    if "meta" in property_data:
        for key, value in property_data["meta"].items():
            if isinstance(value, list):
                for item_id in value:
                    postmeta = etree.SubElement(item, "{%s}postmeta" % nsmap["wp"])
                    etree.SubElement(postmeta, "{%s}meta_key" % nsmap["wp"]).text = (
                        etree.CDATA(key)
                    )
                    etree.SubElement(postmeta, "{%s}meta_value" % nsmap["wp"]).text = (
                        etree.CDATA(str(item_id.get("id", "")))
                    )

    # Преобразуем XML в строку с красивым форматированием
    xml_string = minidom.parseString(etree.tostring(rss)).toprettyxml(indent="  ")

    return xml_string


# Пример использования
property_data = {
    "status": "publish",
    "type": "property",
    "title": "Flat / apartment for sale in calle de Tòquio",
    "content": "<p>Описание объекта недвижимости...</p>",
    "excerpt": "<p>Краткое описание...</p>",
    "meta": {"fave_property_images": [{"id": "17548"}]},
}

xml_output = property_to_xml(property_data)
print(xml_output)

# Сохранение XML в файл
with open("property_export.xml", "w", encoding="utf-8") as xml_file:
    xml_file.write(xml_output)

print("XML файл создан: property_export.xml")
