# src/category_manager.py
from pathlib import Path

from config_utils import load_config
from logger import logger


class CategoryManager:
    """Менеджер для работы с категориями товаров"""

    def __init__(self):
        """Инициализация менеджера категорий"""
        self.config = load_config()
        self.categories = self.config.get("categories", {})
        self.current_category = None

    def get_categories(self):
        """Возвращает список доступных категорий"""
        return {
            category_id: {
                "name": category_info.get("name", "Без названия"),
                "id": category_info.get("id", ""),
            }
            for category_id, category_info in self.categories.items()
        }

    def set_current_category(self, category_id):
        """Устанавливает текущую категорию"""
        if category_id not in self.categories:
            logger.error(f"Категория {category_id} не найдена в конфигурации")
            return False

        self.current_category = category_id
        logger.info(f"Установлена текущая категория: {category_id}")
        return True

    def get_current_category_info(self):
        """Возвращает информацию о текущей категории"""
        if not self.current_category:
            logger.error("Текущая категория не установлена")
            return None

        return self.categories.get(self.current_category)

    def get_category_url(self):
        """Возвращает URL для текущей категории"""
        category_info = self.get_current_category_info()
        if not category_info:
            return None

        return category_info.get("url", "")

    def get_category_start_page(self):
        """Возвращает URL для текущей категории"""
        category_info = self.get_current_category_info()
        if not category_info:
            return None

        return category_info.get("start", "")

    def get_category_url_pages(self):
        """Возвращает URL для текущей категории"""
        category_info = self.get_current_category_info()
        if not category_info:
            return None

        return category_info.get("pages", "")

    def get_category_url_delay(self):
        """Возвращает URL для текущей категории"""
        category_info = self.get_current_category_info()
        if not category_info:
            return None

        return category_info.get("delay", "")

    def get_category_template(self):
        """Возвращает шаблон для товаров текущей категории"""
        category_info = self.get_current_category_info()
        if not category_info:
            return {}

        return category_info.get("template", {})

    def get_category_html_dir(self):
        """Возвращает директорию для HTML-файлов текущей категории"""
        if not self.current_category:
            logger.error("Текущая категория не установлена")
            return None

        base_dir = Path.cwd()
        html_dir = (
            base_dir
            / self.config["directories"]["html_product"]
            / self.current_category
        )
        html_dir.mkdir(parents=True, exist_ok=True)
        return html_dir

    def get_category_page_dir(self):
        """Возвращает директорию для HTML-страниц текущей категории"""
        if not self.current_category:
            logger.error("Текущая категория не установлена")
            return None

        base_dir = Path.cwd()
        html_dir = (
            base_dir / self.config["directories"]["html_page"] / self.current_category
        )
        html_dir.mkdir(parents=True, exist_ok=True)
        return html_dir

    def get_category_json_dir(self):
        """Возвращает директорию для JSON-файлов текущей категории"""
        if not self.current_category:
            logger.error("Текущая категория не установлена")
            return None

        base_dir = Path.cwd()
        json_dir = base_dir / self.config["directories"]["json"] / self.current_category
        json_dir.mkdir(parents=True, exist_ok=True)
        return json_dir

    def get_category_data_files(self):
        """Возвращает пути к файлам данных для текущей категории"""
        if not self.current_category:
            logger.error("Текущая категория не установлена")
            return None

        base_dir = Path.cwd()
        data_dir = base_dir / self.config["directories"]["data"]
        data_dir.mkdir(parents=True, exist_ok=True)

        return {
            "output_xlsx": data_dir / f"{self.current_category}_output.xlsx",
            "new_output_xlsx": data_dir / f"{self.current_category}_new_output.xlsx",
            "output_json": data_dir / f"{self.current_category}_output.json",
            "bd_json": data_dir / f"{self.current_category}_bd_json.json",
            "temp_json": data_dir / f"{self.current_category}_temp_json.json",
        }

    def format_item_template(self, product_data):
        """
        Форматирует шаблон товара с данными продукта

        Args:
            product_data: Словарь с данными продукта (имя, цена, url и т.д.)

        Returns:
            dict: Отформатированный шаблон товара
        """
        logger.debug(f"Получены данные продукта: {product_data}")
        template = self.get_category_template()
        if not template:
            logger.error("Шаблон для текущей категории не найден")
            return {}

        # Создаем результирующий словарь для сохранения порядка полей
        item = {}

        # Обрабатываем поля из шаблона в том порядке, в котором они там есть
        for key, value in template.items():
            # Если поле содержит плейсхолдеры, заменяем их значениями из product_data
            if isinstance(value, str) and "{" in value and "}" in value:
                formatted_value = value
                for pd_key, pd_value in product_data.items():
                    placeholder = "{" + pd_key + "}"
                    if placeholder in formatted_value and pd_value is not None:
                        formatted_value = formatted_value.replace(
                            placeholder, str(pd_value)
                        )

                item[key] = formatted_value
            else:
                # Для полей без плейсхолдеров просто копируем значение
                item[key] = value

        # Специальная обработка для поля "Код_товару"
        if (
            "cleaned_name" in product_data
            and "Код_товару" in item
            and "{cleaned_name}" in item["Код_товару"]
        ):
            item["Код_товару"] = product_data["cleaned_name"]

        # Удаляем все плейсхолдеры, которые не были заменены
        for key, value in item.items():
            if isinstance(value, str) and "{" in value and "}" in value:
                # Удаляем все оставшиеся плейсхолдеры с помощью регулярного выражения
                import re

                item[key] = re.sub(r"\{[^{}]*\}", "", value)

        logger.debug(f"Сформирован шаблон товара: {item}")
        return item


# Создаем глобальный экземпляр для использования в приложении
category_manager = CategoryManager()
