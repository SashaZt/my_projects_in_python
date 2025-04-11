import pyodbc

# Строка подключения
connection_string = (
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=allegrosearchservice.database.windows.net,1433;"
    "Database=AlegroSearchService;"
    "UID=Igor;"
    "PWD=ZGIA_01078445iv;"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=30;"
)

try:
    # Устанавливаем соединение
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    print("Успешно подключились к базе данных!")

    # SQL-запросы для создания таблиц
    create_tables_query = """
    -- Таблица товаров
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'parts_products')
    BEGIN
        CREATE TABLE parts_products (
            id BIGINT PRIMARY KEY,
            title NVARCHAR(255) NOT NULL,
            active BIT DEFAULT 1,
            available_quantity INT NOT NULL DEFAULT 0,
            price DECIMAL(10, 2),
            price_with_delivery DECIMAL(10, 2),
            currency NVARCHAR(3),
            delivery_price DECIMAL(10, 2),
            delivery_period NVARCHAR(255),
            url NVARCHAR(255),
            seller_id BIGINT,
            seller_login NVARCHAR(100),
            seller_rating DECIMAL(5, 2),
            brandcar NVARCHAR(100),
            model NVARCHAR(100),
            selectedcategoryid NVARCHAR(20),
            created_at DATETIME DEFAULT GETDATE(),
            updated_at DATETIME DEFAULT GETDATE()
        );
    END

    -- Таблица категорий
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'parts_categories')
    BEGIN
        CREATE TABLE parts_categories (
            id NVARCHAR(20) PRIMARY KEY,
            name NVARCHAR(100) NOT NULL,
            url NVARCHAR(255),
            parent_id NVARCHAR(20)
        );
    END

    -- Связь товаров с категориями
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'parts_product_categories')
    BEGIN
        CREATE TABLE parts_product_categories (
            product_id BIGINT,
            category_id NVARCHAR(20),
            PRIMARY KEY (product_id, category_id),
            FOREIGN KEY (product_id) REFERENCES parts_products(id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES parts_categories(id)
        );
    END

    -- Таблица изображений
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'parts_images')
    BEGIN
        CREATE TABLE parts_images (
            id INT IDENTITY(1,1) PRIMARY KEY,
            product_id BIGINT,
            original_url NVARCHAR(255) NOT NULL,
            thumbnail_url NVARCHAR(255),
            embedded_url NVARCHAR(255),
            alt_text NVARCHAR(255),
            position INT,
            FOREIGN KEY (product_id) REFERENCES parts_products(id) ON DELETE CASCADE
        );
    END

    -- Таблица спецификаций (JSON вместо JSONB)
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'parts_specifications')
    BEGIN
        CREATE TABLE parts_specifications (
            id INT IDENTITY(1,1) PRIMARY KEY,
            product_id BIGINT,
            param_group NVARCHAR(100) NOT NULL,
            params NVARCHAR(MAX) NOT NULL, -- JSON хранится как текст
            CONSTRAINT chk_json CHECK (ISJSON(params) = 1),
            UNIQUE (product_id, param_group),
            FOREIGN KEY (product_id) REFERENCES parts_products(id) ON DELETE CASCADE
        );
    END

    -- Таблица секций описания
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'parts_description_sections')
    BEGIN
        CREATE TABLE parts_description_sections (
            id INT IDENTITY(1,1) PRIMARY KEY,
            product_id BIGINT,
            position INT NOT NULL,
            UNIQUE (product_id, position),
            FOREIGN KEY (product_id) REFERENCES parts_products(id) ON DELETE CASCADE
        );
    END

    -- Таблица элементов описания
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'parts_description_items')
    BEGIN
        CREATE TABLE parts_description_items (
            id INT IDENTITY(1,1) PRIMARY KEY,
            section_id INT,
            type NVARCHAR(50) NOT NULL,
            content NVARCHAR(MAX),
            url NVARCHAR(255),
            alt_text NVARCHAR(255),
            position INT NOT NULL,
            UNIQUE (section_id, position),
            FOREIGN KEY (section_id) REFERENCES parts_description_sections(id) ON DELETE CASCADE
        );
    END

    -- Таблица типов параметров
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'parts_parameter_types')
    BEGIN
        CREATE TABLE parts_parameter_types (
            id INT IDENTITY(1,1) PRIMARY KEY,
            name NVARCHAR(100) NOT NULL UNIQUE,
            description NVARCHAR(MAX)
        );
    END

    -- Таблица значений параметров
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'parts_product_parameters')
    BEGIN
        CREATE TABLE parts_product_parameters (
            id INT IDENTITY(1,1) PRIMARY KEY,
            product_id BIGINT,
            parameter_id INT,
            value NVARCHAR(255) NOT NULL, -- Ограничиваем длину для уникального индекса
            FOREIGN KEY (product_id) REFERENCES parts_products(id) ON DELETE CASCADE,
            FOREIGN KEY (parameter_id) REFERENCES parts_parameter_types(id)
        );
    END

    -- Добавляем уникальное ограничение
    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'product_parameters_product_id_parameter_id_value_key' AND object_id = OBJECT_ID('parts_product_parameters'))
    BEGIN
        ALTER TABLE parts_product_parameters
        ADD CONSTRAINT product_parameters_product_id_parameter_id_value_key
        UNIQUE (product_id, parameter_id, value);
    END

    -- Индексы
    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_parts_products_id')
    BEGIN
        CREATE INDEX idx_parts_products_id ON parts_products(id);
    END
    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_parts_products_active')
    BEGIN
        CREATE INDEX idx_parts_products_active ON parts_products(active);
    END
    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_parts_products_seller_id')
    BEGIN
        CREATE INDEX idx_parts_products_seller_id ON parts_products(seller_id);
    END
    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_parts_products_brandcar')
    BEGIN
        CREATE INDEX idx_parts_products_brandcar ON parts_products(brandcar);
    END
    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_parts_products_model')
    BEGIN
        CREATE INDEX idx_parts_products_model ON parts_products(model);
    END
    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_parts_products_selectedcategoryid')
    BEGIN
        CREATE INDEX idx_parts_products_selectedcategoryid ON parts_products(selectedcategoryid);
    END
    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_parts_products_price')
    BEGIN
        CREATE INDEX idx_parts_products_price ON parts_products(price);
    END
    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_parts_images_product_id')
    BEGIN
        CREATE INDEX idx_parts_images_product_id ON parts_images(product_id);
    END
    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_parts_specifications_product_id')
    BEGIN
        CREATE INDEX idx_parts_specifications_product_id ON parts_specifications(product_id);
    END
    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_parts_description_sections_product_id')
    BEGIN
        CREATE INDEX idx_parts_description_sections_product_id ON parts_description_sections(product_id);
    END
    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_parts_description_items_section_id')
    BEGIN
        CREATE INDEX idx_parts_description_items_section_id ON parts_description_items(section_id);
    END
    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_parts_product_parameters_product_id')
    BEGIN
        CREATE INDEX idx_parts_product_parameters_product_id ON parts_product_parameters(product_id);
    END
    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_parts_product_parameters_parameter_id')
    BEGIN
        CREATE INDEX idx_parts_product_parameters_parameter_id ON parts_product_parameters(parameter_id);
    END
    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_parts_product_parameters_value')
    BEGIN
        CREATE INDEX idx_parts_product_parameters_value ON parts_product_parameters(value);
    END

    -- Комментарии
    EXEC sp_addextendedproperty @name=N'MS_Description', @value=N'Таблица товаров автозапчастей', @level0type=N'SCHEMA', @level0name=N'dbo', @level1type=N'TABLE', @level1name=N'parts_products';
    EXEC sp_addextendedproperty @name=N'MS_Description', @value=N'Таблица категорий товаров', @level0type=N'SCHEMA', @level0name=N'dbo', @level1type=N'TABLE', @level1name=N'parts_categories';
    EXEC sp_addextendedproperty @name=N'MS_Description', @value=N'Связь товаров с категориями', @level0type=N'SCHEMA', @level0name=N'dbo', @level1type=N'TABLE', @level1name=N'parts_product_categories';
    EXEC sp_addextendedproperty @name=N'MS_Description', @value=N'Изображения товаров', @level0type=N'SCHEMA', @level0name=N'dbo', @level1type=N'TABLE', @level1name=N'parts_images';
    EXEC sp_addextendedproperty @name=N'MS_Description', @value=N'Спецификации товаров в формате JSON', @level0type=N'SCHEMA', @level0name=N'dbo', @level1type=N'TABLE', @level1name=N'parts_specifications';
    EXEC sp_addextendedproperty @name=N'MS_Description', @value=N'Секции описания товара', @level0type=N'SCHEMA', @level0name=N'dbo', @level1type=N'TABLE', @level1name=N'parts_description_sections';
    EXEC sp_addextendedproperty @name=N'MS_Description', @value=N'Элементы описания товара', @level0type=N'SCHEMA', @level0name=N'dbo', @level1type=N'TABLE', @level1name=N'parts_description_items';
    EXEC sp_addextendedproperty @name=N'MS_Description', @value=N'Типы параметров товаров (Состояние, Производитель и т.д.)', @level0type=N'SCHEMA', @level0name=N'dbo', @level1type=N'TABLE', @level1name=N'parts_parameter_types';
    EXEC sp_addextendedproperty @name=N'MS_Description', @value=N'Значения параметров для товаров', @level0type=N'SCHEMA', @level0name=N'dbo', @level1type=N'TABLE', @level1name=N'parts_product_parameters';
    """

    # Выполняем запрос
    cursor.execute(create_tables_query)
    conn.commit()
    print("Все таблицы успешно созданы!")

except pyodbc.Error as e:
    print(f"Ошибка при создании таблиц: {e}")

finally:
    try:
        cursor.close()
        conn.close()
        print("Соединение закрыто.")
    except:
        pass
