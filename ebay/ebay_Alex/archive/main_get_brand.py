# Извлекам только бренды с eBay
import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup


def extract_brands_from_html(html_content):
    """
    Извлекает бренды из HTML структуры фильтров eBay

    Args:
        html_content (str): HTML содержимое страницы

    Returns:
        dict: Словарь {brand_name: brand_url}
    """
    brands = {}

    try:
        soup = BeautifulSoup(html_content, "lxml")

        # Ищем все ссылки брендов
        # Селектор: ссылки с классом brwr__inputs__actions и href содержащим Car-and-Truck-ECUs
        brand_links = soup.find_all(
            "a",
            {
                "class": "brwr__inputs__actions",
                "href": re.compile(r"Car-and-Truck-ECUs|Car-Truck-ABS-System-Parts"),
            },
        )

        print(f"Найдено {len(brand_links)} ссылок брендов")

        for link in brand_links:
            # Извлекаем URL
            href = link.get("href")
            if not href:
                continue

            # Извлекаем название бренда из span с классом textual-display
            brand_span = link.find("span", class_="textual-display")
            if not brand_span:
                continue

            brand_name = brand_span.get_text().strip()

            # Очищаем URL от параметров
            base_url = href.split("?")[0] if "?" in href else href

            # Добавляем в словарь
            brands[brand_name] = base_url
            print(f"Найден бренд: {brand_name} -> {base_url}")

        return brands

    except Exception as e:
        print(f"Ошибка при извлечении брендов: {str(e)}")
        return {}


def extract_brands_from_filter_menu(html_content):
    """
    Извлекает бренды из меню фильтров Brand
    """
    brands = {}

    try:
        soup = BeautifulSoup(html_content, "lxml")

        # Ищем контейнер фильтра Brand
        brand_container = soup.find("span", {"class": "filter-menu-button"})
        if not brand_container:
            print("Контейнер фильтра Brand не найден")
            return brands

        # Ищем все элементы списка с брендами
        brand_items = brand_container.find_all("li", class_="brwr__inputs")

        print(f"Найдено {len(brand_items)} элементов брендов")

        for item in brand_items:
            # Ищем ссылку внутри элемента
            link = item.find("a", class_="brwr__inputs__actions")
            if not link:
                continue

            # Извлекаем URL
            href = link.get("href")
            if not href:
                continue

            # Извлекаем название бренда
            brand_span = link.find("span", class_="textual-display")
            if not brand_span:
                continue

            brand_name = brand_span.get_text().strip()

            # Очищаем URL
            base_url = href.split("?")[0] if "?" in href else href

            brands[brand_name] = base_url
            print(f"Найден бренд: {brand_name} -> {base_url}")

        return brands

    except Exception as e:
        print(f"Ошибка при извлечении из меню фильтров: {str(e)}")
        return {}


def get_brands_from_ebay_simple():
    """
    Загружает страницу eBay и извлекает бренды простым способом
    """
    url = "https://www.ebay.com/b/Car-Truck-ECUs-Computer-Modules/33596/bn_584314"
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    }

    try:
        print(f"Загружаем страницу: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        print(f"Страница загружена, размер: {len(response.text)} символов")

        # Сохраняем HTML для анализа
        with open("ebay_page_simple.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("HTML сохранен в: ebay_page_simple.html")

        # Метод 1: Извлечение из фильтров
        print("\n=== МЕТОД 1: Извлечение из HTML фильтров ===")
        brands1 = extract_brands_from_html(response.text)

        # Метод 2: Извлечение из меню фильтров
        print("\n=== МЕТОД 2: Извлечение из меню фильтров ===")
        brands2 = extract_brands_from_filter_menu(response.text)

        # Объединяем результаты
        all_brands = {}
        all_brands.update(brands1)
        all_brands.update(brands2)

        print(f"\n=== ИТОГО ===")
        print(f"Метод 1: {len(brands1)} брендов")
        print(f"Метод 2: {len(brands2)} брендов")
        print(f"Объединено: {len(all_brands)} уникальных брендов")

        return all_brands

    except Exception as e:
        print(f"Ошибка при загрузке страницы: {str(e)}")
        return {}


def test_with_provided_html():
    """
    Тестирует извлечение на предоставленном HTML фрагменте
    """
    html_fragment = """<span class="filter-menu-button" id="nid-lm1-7"><button class="filter-button filter-button--unselected filter-menu-button__button" type="button" data-interactions="[{&quot;actionKind&quot;:&quot;CLICK&quot;,&quot;interaction&quot;:&quot;wwFVrK2vRE0lhQQ0MDFKVzZCM00xRlg5MllFSFpWMktFUTdETTc0MDFKVzZCM00xR0E5RkIwV1ZCUFhLSjQxOTIAAAwxNjI1OTIKQ0xJQ0sA&quot;}]" _sp="p4384412.m148486.l162592" data-track="{&quot;eventFamily&quot;:&quot;BROWSE&quot;,&quot;eventAction&quot;:&quot;ACTN&quot;,&quot;actionKind&quot;:&quot;CLICK&quot;,&quot;operationId&quot;:&quot;4530678&quot;,&quot;flushImmediately&quot;:false,&quot;eventProperty&quot;:{&quot;enableTrackingStandard&quot;:&quot;true&quot;,&quot;moduledtl&quot;:&quot;global:0|aspectName:aspect-Brand|mi:148486|iid:1|li:162592|luid:1&quot;,&quot;sid&quot;:&quot;p4384412.m148486.l162592&quot;,&quot;trackableId&quot;:&quot;01JW6B3M1FX92YEHZV2KEQ7DM7&quot;,&quot;interaction&quot;:&quot;wwFVrK2vRE0lhQQ0MDFKVzZCM00xRlg5MllFSFpWMktFUTdETTc0MDFKVzZCM00xR0E5RkIwV1ZCUFhLSjQxOTIAAAwxNjI1OTIKQ0xJQ0sA&quot;}}" aria-expanded="false" aria-controls="nid-lm1-7-content"><span class="filter-button__cell"><span><span class="filter-label">Brand</span><svg class="icon icon--12" focusable="false" aria-hidden="true"><use href="#icon-chevron-down-12"></use></svg></span></span></button><span class="filter-menu-button__menu" id="nid-lm1-7-content"><div class="filter-menu-button__content"><ul class="filter-menu-button__content__list"><li class="brwr__inputs"><a data-interactions="[{&quot;actionKind&quot;:&quot;CLICK&quot;,&quot;interaction&quot;:&quot;wwFVrK2vRE0lhQY0MDFKVzZCM00xRlg5MllFSFpWMktFUTdETTc0MDFKVzZCM00xR0E5RkIwV1ZCUFhLSjQxOTI0MDFKVzZCM00xRVIxWTJTR0dFRjRUTTRZNjkAAAwxNTY5NjcKQ0xJQ0sA&quot;}]" _sp="p4384412.m148486.l156967" data-track="{&quot;eventFamily&quot;:&quot;BROWSE&quot;,&quot;eventAction&quot;:&quot;ACTN&quot;,&quot;actionKind&quot;:&quot;CLICK&quot;,&quot;operationId&quot;:&quot;4530678&quot;,&quot;flushImmediately&quot;:false,&quot;eventProperty&quot;:{&quot;enableTrackingStandard&quot;:&quot;true&quot;,&quot;moduledtl&quot;:&quot;aspectURLParamValue:Audi|iid:1|luid:79|global:0|mi:148486|li:156967|selected:1|aspectURLParam:Brand&quot;,&quot;sid&quot;:&quot;p4384412.m148486.l156967&quot;,&quot;trackableId&quot;:&quot;01JW6B3M1ER1Y2SGGEF4TM4Y69&quot;,&quot;interaction&quot;:&quot;wwFVrK2vRE0lhQY0MDFKVzZCM00xRlg5MllFSFpWMktFUTdETTc0MDFKVzZCM00xR0E5RkIwV1ZCUFhLSjQxOTI0MDFKVzZCM00xRVIxWTJTR0dFRjRUTTRZNjkAAAwxNTY5NjcKQ0xJQ0sA&quot;}}" href="https://www.ebay.com/b/Audi-Car-and-Truck-ECUs/33596/bn_584161?mag=1" class="brwr__inputs__actions"><svg class="icon icon--18" focusable="false" aria-hidden="true"><use href="#icon-checkbox-unchecked-18"></use></svg><label class="brwr__inputs--label"><span class="textual-display">Audi</span></label></a></li><li class="brwr__inputs"><a data-interactions="[{&quot;actionKind&quot;:&quot;CLICK&quot;,&quot;interaction&quot;:&quot;wwFVrK2vRE0lhQY0MDFKVzZCM00xRlg5MllFSFpWMktFUTdETTc0MDFKVzZCM00xR0E5RkIwV1ZCUFhLSjQxOTI0MDFKVzZCM00xRVAwSlRWUVdGWVlTMjM3RzkAAAwxNTY5NjcKQ0xJQ0sA&quot;}]" _sp="p4384412.m148486.l156967" data-track="{&quot;eventFamily&quot;:&quot;BROWSE&quot;,&quot;eventAction&quot;:&quot;ACTN&quot;,&quot;actionKind&quot;:&quot;CLICK&quot;,&quot;operationId&quot;:&quot;4530678&quot;,&quot;flushImmediately&quot;:false,&quot;eventProperty&quot;:{&quot;enableTrackingStandard&quot;:&quot;true&quot;,&quot;moduledtl&quot;:&quot;aspectURLParamValue:BMW|iid:1|luid:80|global:0|mi:148486|li:156967|selected:1|aspectURLParam:Brand&quot;,&quot;sid&quot;:&quot;p4384412.m148486.l156967&quot;,&quot;trackableId&quot;:&quot;01JW6B3M1EP0JTVQWFYYS237G9&quot;,&quot;interaction&quot;:&quot;wwFVrK2vRE0lhQY0MDFKVzZCM00xRlg5MllFSFpWMktFUTdETTc0MDFKVzZCM00xR0E5RkIwV1ZCUFhLSjQxOTI0MDFKVzZCM00xRVAwSlRWUVdGWVlTMjM3RzkAAAwxNTY5NjcKQ0xJQ0sA&quot;}}" href="https://www.ebay.com/b/BMW-Car-and-Truck-ECUs/33596/bn_574989?mag=1" class="brwr__inputs__actions"><svg class="icon icon--18" focusable="false" aria-hidden="true"><use href="#icon-checkbox-unchecked-18"></use></svg><label class="brwr__inputs--label"><span class="textual-display">BMW</span></label></a></li><li class="brwr__inputs"><a data-interactions="[{&quot;actionKind&quot;:&quot;CLICK&quot;,&quot;interaction&quot;:&quot;wwFVrK2vRE0lhQY0MDFKVzZCM00xRlg5MllFSFpWMktFUTdETTc0MDFKVzZCM00xR0E5RkIwV1ZCUFhLSjQxOTI0MDFKVzZCM00xRVNXN0RORlNHUUdNODQ5WjcAAAwxNTY5NjcKQ0xJQ0sA&quot;}]" _sp="p4384412.m148486.l156967" data-track="{&quot;eventFamily&quot;:&quot;BROWSE&quot;,&quot;eventAction&quot;:&quot;ACTN&quot;,&quot;actionKind&quot;:&quot;CLICK&quot;,&quot;operationId&quot;:&quot;4530678&quot;,&quot;flushImmediately&quot;:false,&quot;eventProperty&quot;:{&quot;enableTrackingStandard&quot;:&quot;true&quot;,&quot;moduledtl&quot;:&quot;aspectURLParamValue:Bosch|iid:1|luid:81|global:0|mi:148486|li:156967|selected:1|aspectURLParam:Brand&quot;,&quot;sid&quot;:&quot;p4384412.m148486.l156967&quot;,&quot;trackableId&quot;:&quot;01JW6B3M1ESW7DNFSGQGM849Z7&quot;,&quot;interaction&quot;:&quot;wwFVrK2vRE0lhQY0MDFKVzZCM00xRlg5MllFSFpWMktFUTdETTc0MDFKVzZCM00xR0E5RkIwV1ZCUFhLSjQxOTI0MDFKVzZCM00xRVNXN0RORlNHUUdNODQ5WjcAAAwxNTY5NjcKQ0xJQ0sA&quot;}}" href="https://www.ebay.com/b/Bosch-Car-and-Truck-ECUs/33596/bn_580785?mag=1" class="brwr__inputs__actions"><svg class="icon icon--18" focusable="false" aria-hidden="true"><use href="#icon-checkbox-unchecked-18"></use></svg><label class="brwr__inputs--label"><span class="textual-display">Bosch</span></label></a></li><li class="brwr__inputs"><a data-interactions="[{&quot;actionKind&quot;:&quot;CLICK&quot;,&quot;interaction&quot;:&quot;wwFVrK2vRE0lhQY0MDFKVzZCM00xRlg5MllFSFpWMktFUTdETTc0MDFKVzZCM00xR0E5RkIwV1ZCUFhLSjQxOTI0MDFKVzZCM00xRUJSWjFDOFpINVg4N1pKTU4AAAwxNTY5NjcKQ0xJQ0sA&quot;}]" _sp="p4384412.m148486.l156967" data-track="{&quot;eventFamily&quot;:&quot;BROWSE&quot;,&quot;eventAction&quot;:&quot;ACTN&quot;,&quot;actionKind&quot;:&quot;CLICK&quot;,&quot;operationId&quot;:&quot;4530678&quot;,&quot;flushImmediately&quot;:false,&quot;eventProperty&quot;:{&quot;enableTrackingStandard&quot;:&quot;true&quot;,&quot;moduledtl&quot;:&quot;aspectURLParamValue:Chevrolet|iid:1|luid:82|global:0|mi:148486|li:156967|selected:1|aspectURLParam:Brand&quot;,&quot;sid&quot;:&quot;p4384412.m148486.l156967&quot;,&quot;trackableId&quot;:&quot;01JW6B3M1EBRZ1C8ZH5X87ZJMN&quot;,&quot;interaction&quot;:&quot;wwFVrK2vRE0lhQY0MDFKVzZCM00xRlg5MllFSFpWMktFUTdETTc0MDFKVzZCM00xR0E5RkIwV1ZCUFhLSjQxOTI0MDFKVzZCM00xRUJSWjFDOFpINVg4N1pKTU4AAAwxNTY5NjcKQ0xJQ0sA&quot;}}" href="https://www.ebay.com/b/Chevrolet-Car-and-Truck-ECUs/33596/bn_579193?mag=1" class="brwr__inputs__actions"><svg class="icon icon--18" focusable="false" aria-hidden="true"><use href="#icon-checkbox-unchecked-18"></use></svg><label class="brwr__inputs--label"><span class="textual-display">Chevrolet</span></label></a></li></ul></div></span></span>"""

    print("=== ТЕСТ С ПРЕДОСТАВЛЕННЫМ HTML ===\n")

    brands = extract_brands_from_filter_menu(html_fragment)

    print(f"\nРезультат теста: {len(brands)} брендов")
    for brand, url in brands.items():
        print(f"  {brand}: {url}")

    return brands


def save_brands_simple(brands, filename="brands_simple.json"):
    """
    Сохраняет извлеченные бренды
    """
    try:
        # JSON файл
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(brands, f, indent=4, ensure_ascii=False)
        print(f"Бренды сохранены в: {filename}")

        # Python файл для использования в коде
        py_filename = filename.replace(".json", ".py")
        with open(py_filename, "w", encoding="utf-8") as f:
            f.write("# Извлеченные бренды eBay (простой метод)\n")
            f.write("BRAND_URLS = {\n")
            for brand, url in sorted(brands.items()):
                f.write(f'    "{brand}": "{url}",\n')
            f.write("}\n")
        print(f"Python файл сохранен: {py_filename}")

    except Exception as e:
        print(f"Ошибка при сохранении: {str(e)}")


def main():
    """
    Основная функция - простое извлечение брендов
    """
    # print("=== ПРОСТОЕ ИЗВЛЕЧЕНИЕ БРЕНДОВ ИЗ HTML ===\n")

    # # Сначала тестируем на фрагменте
    # print("1. Тест с предоставленным HTML фрагментом:")
    # test_brands = test_with_provided_html()
    #
    # print("\n" + "=" * 60)

    # Затем загружаем полную страницу
    print("2. Извлечение с полной страницы eBay:")
    all_brands = get_brands_from_ebay_simple()

    if all_brands:
        print(f"\n=== НАЙДЕНО {len(all_brands)} БРЕНДОВ ===")

        # Показываем все найденные бренды
        for i, (brand, url) in enumerate(sorted(all_brands.items()), 1):
            print(f"{i:2d}. {brand}")
            print(f"    {url}")

        # Сохраняем
        save_brands_simple(all_brands)

        print(f"\n✅ Успешно! Найдено {len(all_brands)} брендов")
        print("📁 Результаты сохранены в brands_simple.json и brands_simple.py")

        return all_brands
    else:
        print("❌ Бренды не найдены")
        return {}


if __name__ == "__main__":
    extracted_brands = main()
