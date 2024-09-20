from pathlib import Path
import os
from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    select,
    update,
)
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from dotenv import load_dotenv
from configuration.logger_setup import logger

# Подготовка данных из CSV
current_directory = Path.cwd()
csv_import = current_directory / "bmw_import_0708.csv"

df = pd.read_csv(csv_import, delimiter=";", encoding="utf-8")

# Преобразуем необходимые столбцы в нужные типы данных
df["qty"] = df["qty"].astype(float)
df["is_in_stock"] = df["is_in_stock"].astype(int)
df["manage_stock"] = df["manage_stock"].astype(int)
df["price"] = df["price"].astype(float)
df["weight"] = df["weight"].astype(float)

# Подключение к базе данных
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)
DATABASE_URI = os.getenv("DATABASE_URI")
engine = create_engine(DATABASE_URI, pool_pre_ping=True)
Session = sessionmaker(bind=engine)
metadata = MetaData()

# Определяем таблицы
catalog_product_entity = Table("catalog_product_entity", metadata, autoload_with=engine)
catalog_product_entity_varchar = Table(
    "catalog_product_entity_varchar", metadata, autoload_with=engine
)
catalog_product_entity_int = Table(
    "catalog_product_entity_int", metadata, autoload_with=engine
)
catalog_product_entity_text = Table(
    "catalog_product_entity_text", metadata, autoload_with=engine
)
catalog_product_entity_decimal = Table(
    "catalog_product_entity_decimal", metadata, autoload_with=engine
)
cataloginventory_stock_item = Table(
    "cataloginventory_stock_item", metadata, autoload_with=engine
)
eav_attribute = Table("eav_attribute", metadata, autoload_with=engine)
catalog_product_entity_media_gallery = Table(
    "catalog_product_entity_media_gallery", metadata, autoload_with=engine
)
catalog_product_entity_media_gallery_value_to_entity = Table(
    "catalog_product_entity_media_gallery_value_to_entity",
    metadata,
    autoload_with=engine,
)
eav_attribute_set = Table("eav_attribute_set", metadata, autoload_with=engine)


def get_attribute_id(session, attribute_code, entity_type_id=4):
    result = session.execute(
        select(eav_attribute.c.attribute_id)
        .where(eav_attribute.c.attribute_code == attribute_code)
        .where(eav_attribute.c.entity_type_id == entity_type_id)
    ).fetchone()
    return result[0] if result else None


def update_or_insert_attribute(
    session, entity_id, store_id, attribute_code, value, table
):
    attribute_id = get_attribute_id(session, attribute_code)
    if attribute_id:
        result = session.execute(
            select(table.c.value_id).where(
                table.c.entity_id == entity_id,
                table.c.attribute_id == attribute_id,
                table.c.store_id == store_id,
            )
        ).fetchone()
        if result:
            stmt = (
                update(table)
                .where(
                    table.c.entity_id == entity_id,
                    table.c.attribute_id == attribute_id,
                    table.c.store_id == store_id,
                )
                .values(value=value)
            )
        else:
            stmt = table.insert().values(
                entity_id=entity_id,
                attribute_id=attribute_id,
                store_id=store_id,
                value=value,
            )
        session.execute(stmt)
    else:
        logger.warning(
            f"Код атрибута '{attribute_code}' не найден для entity_id {entity_id}."
        )


def add_image_to_media_gallery(session, file_path, media_gallery_attribute_id):
    result = session.execute(
        select(catalog_product_entity_media_gallery.c.value_id).where(
            catalog_product_entity_media_gallery.c.value == file_path
        )
    ).fetchone()
    if result:
        value_id = result[0]
    else:
        stmt = catalog_product_entity_media_gallery.insert().values(
            attribute_id=media_gallery_attribute_id,
            value=file_path,
            media_type="image",
            disabled=0,
        )
        result = session.execute(stmt)
        value_id = result.inserted_primary_key[0]
    return value_id


def associate_image_with_product(session, value_id, entity_id):
    result = session.execute(
        select(catalog_product_entity_media_gallery_value_to_entity.c.value_id).where(
            catalog_product_entity_media_gallery_value_to_entity.c.value_id == value_id,
            catalog_product_entity_media_gallery_value_to_entity.c.entity_id
            == entity_id,
        )
    ).fetchone()
    if not result:
        stmt = catalog_product_entity_media_gallery_value_to_entity.insert().values(
            value_id=value_id,
            entity_id=entity_id,
        )
        session.execute(stmt)


def update_or_insert_stock_item(session, product_id, data):
    result = session.execute(
        select(cataloginventory_stock_item.c.item_id).where(
            cataloginventory_stock_item.c.product_id == product_id
        )
    ).fetchone()
    if result:
        stmt = (
            update(cataloginventory_stock_item)
            .where(cataloginventory_stock_item.c.product_id == product_id)
            .values(data)
        )
    else:
        stmt = cataloginventory_stock_item.insert().values(data)
    session.execute(stmt)


def get_visibility_value(visibility_str):
    visibility_mapping = {
        "Not Visible Individually": 1,
        "Catalog": 2,
        "Search": 3,
        "Catalog, Search": 4,
        "1": 1,
        "2": 2,
        "3": 3,
        "4": 4,
    }
    if isinstance(visibility_str, str):
        visibility_value = visibility_mapping.get(visibility_str.strip(), None)
        if visibility_value is None:
            logger.error(f"Неизвестное значение visibility '{visibility_str}'")
            return 4  # Значение по умолчанию
    else:
        visibility_value = int(visibility_str)
    return visibility_value


def process_row(row):
    session = Session()
    try:
        sku = row["sku"]
        result = session.execute(
            select(catalog_product_entity.c.entity_id).where(
                catalog_product_entity.c.sku == sku
            )
        ).fetchone()
        if result:
            entity_id = result[0]
            store_id = 0  # Глобальный уровень

            visibility_value = get_visibility_value(row["visibility"])

            # Обновляем атрибуты
            update_or_insert_attribute(
                session,
                entity_id,
                store_id,
                "name",
                row["name"],
                catalog_product_entity_varchar,
            )
            update_or_insert_attribute(
                session,
                entity_id,
                store_id,
                "brand",
                row["brand"],
                catalog_product_entity_varchar,
            )
            update_or_insert_attribute(
                session,
                entity_id,
                store_id,
                "tags",
                row["tags"],
                catalog_product_entity_varchar,
            )
            update_or_insert_attribute(
                session,
                entity_id,
                store_id,
                "description",
                row["description"],
                catalog_product_entity_text,
            )
            update_or_insert_attribute(
                session,
                entity_id,
                store_id,
                "short_description",
                row["short_description"],
                catalog_product_entity_text,
            )
            update_or_insert_attribute(
                session,
                entity_id,
                store_id,
                "price",
                row["price"],
                catalog_product_entity_decimal,
            )
            update_or_insert_attribute(
                session,
                entity_id,
                store_id,
                "weight",
                row["weight"],
                catalog_product_entity_decimal,
            )
            update_or_insert_attribute(
                session,
                entity_id,
                store_id,
                "visibility",
                visibility_value,
                catalog_product_entity_int,
            )

            # Обновляем информацию о запасах
            stock_data = {
                "qty": row["qty"],
                "is_in_stock": row["is_in_stock"],
                "manage_stock": row["manage_stock"],
                "use_config_manage_stock": int(row["use_config_manage_stock"]),
                "website_id": int(row["website_id"]),
            }
            update_or_insert_stock_item(session, entity_id, stock_data)

            # Обрабатываем изображения
            media_gallery_attribute_id = get_attribute_id(session, "media_gallery")
            if media_gallery_attribute_id is None:
                logger.error("Attribute 'media_gallery' not found.")
            else:
                base_image_path = row["base_image"]
                if base_image_path:
                    value_id = add_image_to_media_gallery(
                        session, base_image_path, media_gallery_attribute_id
                    )
                    associate_image_with_product(session, value_id, entity_id)

                    update_or_insert_attribute(
                        session,
                        entity_id,
                        store_id,
                        "image",
                        base_image_path,
                        catalog_product_entity_varchar,
                    )
                    update_or_insert_attribute(
                        session,
                        entity_id,
                        store_id,
                        "small_image",
                        base_image_path,
                        catalog_product_entity_varchar,
                    )
                    update_or_insert_attribute(
                        session,
                        entity_id,
                        store_id,
                        "thumbnail",
                        base_image_path,
                        catalog_product_entity_varchar,
                    )

            session.commit()
            logger.info(f"SKU {sku} успешно обновлен.")
        else:
            entity_id = create_product(session, row)
            if entity_id:
                session.commit()  # Коммитим изменения только если entity_id был успешно получен
                logger.info(f"SKU {sku} успешно создан с entity_id {entity_id}.")
            else:
                session.rollback()  # Откатываем транзакцию, если entity_id не был получен
                logger.error(f"SKU {sku} не создан. Ошибка получения entity_id.")

    except Exception as e:
        logger.error(f"Ошибка при обработке SKU {sku}: {e}")
        session.rollback()
    finally:
        session.close()


def get_attribute_set_id(session, attribute_set_code):
    result = session.execute(
        select(eav_attribute_set.c.attribute_set_id).where(
            eav_attribute_set.c.attribute_set_name == attribute_set_code
        )
    ).fetchone()
    return result[0] if result else None


def create_product(session, row):
    sku = row["sku"]
    attribute_set_id = get_attribute_set_id(
        session, row.get("attribute_set_code", "Default")
    )
    if attribute_set_id is None:
        attribute_set_id = 4  # Значение по умолчанию

    type_id = row.get("product_type", "simple")
    created_at = datetime.now()
    updated_at = datetime.now()

    stmt = catalog_product_entity.insert().values(
        attribute_set_id=attribute_set_id,
        type_id=type_id,
        sku=sku,
        has_options=0,
        required_options=0,
        created_at=created_at,
        updated_at=updated_at,
    )
    result = session.execute(stmt)
    entity_id = result.inserted_primary_key[0]

    store_id = 0  # Глобальный уровень

    # Вставляем атрибуты
    update_or_insert_attribute(
        session,
        entity_id,
        store_id,
        "name",
        row["name"],
        catalog_product_entity_varchar,
    )
    update_or_insert_attribute(
        session,
        entity_id,
        store_id,
        "brand",
        row["brand"],
        catalog_product_entity_varchar,
    )
    update_or_insert_attribute(
        session,
        entity_id,
        store_id,
        "tags",
        row["tags"],
        catalog_product_entity_varchar,
    )
    update_or_insert_attribute(
        session,
        entity_id,
        store_id,
        "description",
        row["description"],
        catalog_product_entity_text,
    )
    update_or_insert_attribute(
        session,
        entity_id,
        store_id,
        "short_description",
        row["short_description"],
        catalog_product_entity_text,
    )
    update_or_insert_attribute(
        session,
        entity_id,
        store_id,
        "price",
        row["price"],
        catalog_product_entity_decimal,
    )
    update_or_insert_attribute(
        session,
        entity_id,
        store_id,
        "weight",
        row["weight"],
        catalog_product_entity_decimal,
    )

    visibility_value = get_visibility_value(row["visibility"])
    update_or_insert_attribute(
        session,
        entity_id,
        store_id,
        "visibility",
        visibility_value,
        catalog_product_entity_int,
    )

    media_gallery_attribute_id = get_attribute_id(session, "media_gallery")
    if media_gallery_attribute_id is None:
        logger.error("Attribute 'media_gallery' not found.")
    else:
        base_image_path = row["base_image"]
        if base_image_path:
            value_id = add_image_to_media_gallery(
                session, base_image_path, media_gallery_attribute_id
            )
            associate_image_with_product(session, value_id, entity_id)

            update_or_insert_attribute(
                session,
                entity_id,
                store_id,
                "image",
                base_image_path,
                catalog_product_entity_varchar,
            )
            update_or_insert_attribute(
                session,
                entity_id,
                store_id,
                "small_image",
                base_image_path,
                catalog_product_entity_varchar,
            )
            update_or_insert_attribute(
                session,
                entity_id,
                store_id,
                "thumbnail",
                base_image_path,
                catalog_product_entity_varchar,
            )

    stock_data = {
        "product_id": entity_id,
        "stock_id": 1,  # Обычно 1
        "qty": row["qty"],
        "is_in_stock": row["is_in_stock"],
        "manage_stock": row["manage_stock"],
        "use_config_manage_stock": int(row["use_config_manage_stock"]),
        "website_id": int(row["website_id"]),
    }
    update_or_insert_stock_item(session, entity_id, stock_data)

    return entity_id


def main():
    data = df.to_dict("records")

    max_workers = 10  # Количество потоков

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_row, row) for row in data]

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"Ошибка в потоке: {e}")


if __name__ == "__main__":
    main()
