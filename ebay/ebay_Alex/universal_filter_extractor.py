from bs4 import BeautifulSoup


def extract_filter_options(html_content, filter_name):
    """
    Извлекает опции для указанного фильтра из HTML

    Args:
        html_content (str): HTML содержимое страницы
        filter_name (str): Название фильтра (Brand, Condition, Type и т.д.)

    Returns:
        dict: Словарь {option_name: option_url}
    """
    options = []

    try:

        # Ищем контейнер фильтра по названию
        filter_containers = html_content.find_all("span", class_="filter-menu-button")

        target_container = None
        for container in filter_containers:
            # Ищем кнопку с нужным названием фильтра
            filter_label = container.find("span", class_="filter-label")
            if filter_label and filter_label.get_text().strip() == filter_name:
                target_container = container
                break

        if not target_container:
            print(f"Фильтр '{filter_name}' не найден")
            return options
        data = {}
        # Ищем все элементы опций в найденном контейнере
        option_items = target_container.find_all("li", class_="brwr__inputs")

        print(f"Найдено {len(option_items)} опций для фильтра '{filter_name}'")

        for item in option_items:
            # Ищем ссылку внутри элемента
            link = item.find("a", class_="brwr__inputs__actions")
            if not link:
                continue

            # Извлекаем URL
            href = link.get("href")
            if not href:
                continue

            # Извлекаем название опции
            option_span = link.find("span", class_="textual-display")
            if not option_span:
                continue

            option_name = option_span.get_text().strip()

            # Очищаем URL от HTML entities
            clean_url = href.replace("&amp;", "&")
            base_url = clean_url.split("?")[0] if "?" in clean_url else clean_url

            data[option_name] = base_url  # Сохраняем базовый URL без параметров
            options[option_name] = clean_url  # Сохраняем полный URL с параметрами
            options.append(data)
            print(f"Найдена опция: {option_name} -> {clean_url}")

        return options

    except Exception as e:
        print(f"Ошибка при извлечении фильтра '{filter_name}': {str(e)}")
        return {}


# def extract_all_filters(html_content):
#     """
#     Извлекает все доступные фильтры с их опциями

#     Args:
#         html_content (str): HTML содержимое страницы

#     Returns:
#         dict: Словарь {filter_name: {option_name: option_url}}
#     """
#     all_filters = {}

#     try:
#         soup = BeautifulSoup(html_content, "lxml")

#         # Ищем все контейнеры фильтров
#         filter_containers = soup.find_all("span", class_="filter-menu-button")

#         print(f"Найдено {len(filter_containers)} фильтров")

#         for container in filter_containers:
#             # Получаем название фильтра
#             filter_label = container.find("span", class_="filter-label")
#             if not filter_label:
#                 continue

#             filter_name = filter_label.get_text().strip()
#             print(f"\nОбрабатываем фильтр: {filter_name}")

#             # Извлекаем опции для этого фильтра
#             options = extract_filter_options(str(container), filter_name)

#             if options:
#                 all_filters[filter_name] = options

#         return all_filters

#     except Exception as e:
#         print(f"Ошибка при извлечении всех фильтров: {str(e)}")
#         return {}


# def extract_condition_codes(html_content):
#     """
#     Специальная функция для извлечения кодов состояний товаров

#     Returns:
#         dict: Словарь {condition_name: condition_code}
#     """
#     conditions = {}

#     try:
#         soup = BeautifulSoup(html_content, "lxml")

#         # Ищем контейнер фильтра Condition
#         condition_container = None
#         filter_containers = soup.find_all("span", class_="filter-menu-button")

#         for container in filter_containers:
#             filter_label = container.find("span", class_="filter-label")
#             if filter_label and filter_label.get_text().strip() == "Condition":
#                 condition_container = container
#                 break

#         if not condition_container:
#             print("Фильтр Condition не найден")
#             return conditions

#         # Ищем все ссылки с параметром LH_ItemCondition
#         condition_links = condition_container.find_all(
#             "a", href=re.compile(r"LH_ItemCondition=")
#         )

#         print(f"Найдено {len(condition_links)} состояний")

#         for link in condition_links:
#             href = link.get("href", "")

#             # Извлекаем код состояния из URL
#             match = re.search(r"LH_ItemCondition=(\d+)", href)
#             if not match:
#                 continue

#             condition_code = match.group(1)

#             # Извлекаем название состояния
#             span = link.find("span", class_="textual-display")
#             if not span:
#                 continue

#             condition_name = span.get_text().strip()

#             conditions[condition_name] = condition_code
#             print(f"Найдено состояние: {condition_name} -> {condition_code}")

#         return conditions

#     except Exception as e:
#         print(f"Ошибка при извлечении кодов состояний: {str(e)}")
#         return {}


# def save_filter_data(filter_data, filename="ebay_filters.json"):
#     """
#     Сохраняет данные фильтров в файл
#     """
#     try:
#         # JSON файл
#         with open(filename, "w", encoding="utf-8") as f:
#             json.dump(filter_data, f, indent=4, ensure_ascii=False)
#         print(f"Данные фильтров сохранены в: {filename}")

#         # Python файл для использования в коде
#         py_filename = filename.replace(".json", ".py")
#         with open(py_filename, "w", encoding="utf-8") as f:
#             f.write("# Извлеченные фильтры eBay\n\n")

#             for filter_name, options in filter_data.items():
#                 var_name = filter_name.upper().replace(" ", "_").replace("-", "_")
#                 f.write(f"{var_name} = {{\n")
#                 for option, value in sorted(options.items()):
#                     f.write(f'    "{option}": "{value}",\n')
#                 f.write("}\n\n")

#         print(f"Python файл сохранен: {py_filename}")

#     except Exception as e:
#         print(f"Ошибка при сохранении: {str(e)}")
