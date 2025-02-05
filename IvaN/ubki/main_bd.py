import pandas as pd
from sqlalchemy import create_engine, Column, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path
from loguru import logger
import sys


current_directory = Path.cwd()
configuration_directory = current_directory / "configuration"
log_directory = current_directory / "log"
log_directory.mkdir(parents=True, exist_ok=True)

log_file_path = log_directory / "log_message.log"

logger.remove()
# 🔹 Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# 🔹 Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)

def create_db_connection(user="python_mysql", password="python_mysql", host="localhost", db="ubki"):
    """
    Создаёт подключение к базе данных и возвращает engine.
    """
    engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}/{db}", echo=True)
    return engine

# Базовый класс для моделей
Base = declarative_base()

# Модель для объединённой таблицы UBKI
class UBKI(Base):
    __tablename__ = 'ubki'
    id = Column(Integer, primary_key=True, autoincrement=True)
    # Общие поля (присутствуют в обоих CSV)
    title = Column(Text)
    registration = Column(Text)
    data_registr = Column(Text)
    record_number = Column(Text)
    tax_debt_date = Column(Text)
    tax_debt_status = Column(Text)
    arrears_date = Column(Text)
    arrears_status = Column(Text)
    main_code = Column(Text)
    additional_codes = Column(Text)
    edrpo = Column(Text)
    address = Column(Text)
    # Дополнительные поля (присутствуют только в legal.csv)
    title_mini = Column(Text)
    registration_date = Column(Text)
    authorized_person = Column(Text)
    founder = Column(Text)
    statutory_fund = Column(Text)
    bankruptcy_info = Column(Text)
    year = Column(Text)
    assets = Column(Text)
    liabilities = Column(Text)
    employees = Column(Text)
    profit = Column(Text)
    income = Column(Text)
    inn = Column(Text)

# Объединённое множество имён столбцов (без id)
UBKI_COLUMNS = {
    "title", "registration", "data_registr", "record_number", "tax_debt_date",
    "tax_debt_status", "arrears_date", "arrears_status", "main_code", "additional_codes",
    "edrpo", "address", "title_mini", "registration_date", "authorized_person", "founder",
    "statutory_fund", "bankruptcy_info", "year", "assets", "liabilities", "employees",
    "profit", "income", "inn"
}

def load_csv_to_db(session, csv_path: Path, model, union_columns: set):
    """
    Загружает данные из CSV-файла по указанному пути в таблицу, определённую моделью model.
    Для каждой записи, если какого-либо столбца из union_columns нет, устанавливает значение None.
    """
    # Читаем CSV с разделителем ';', все столбцы как строки
    df = pd.read_csv(csv_path, sep=';', dtype=str)
    # Заменяем NaN на None для корректной загрузки в БД
    df = df.where(pd.notnull(df), None)
    
    # Преобразуем DataFrame в список словарей (один словарь — одна запись)
    records = df.to_dict(orient='records')
    
    # Для каждой записи заполняем недостающие ключи значением None
    for record in records:
        for col in union_columns:
            if col not in record:
                record[col] = None

    # Массивная вставка данных в таблицу
    session.bulk_insert_mappings(model, records)
    session.commit()
# Таблица для данных из prozorro.csv
class Prozorro(Base):
    __tablename__ = 'prozorro'
    id = Column(Integer, primary_key=True, autoincrement=True)
    edrpo = Column(Text)
    quantity = Column(Text)
    sum = Column(Text)
    seller_tel = Column(Text)
    seller_email = Column(Text)
    # Множество столбцов для таблицы Prozorro
PROZORRO_COLUMNS = {"edrpo", "quantity", "sum", "seller_tel", "seller_email"}
def export_to_excel(engine, output_file):
    """
    Экспортирует данные из таблиц 'ubki' и 'prozorro' в один Excel-файл,
    объединяя данные по столбцу 'edrpo'.
    
    Для каждой записи из таблицы ubki, если в таблице prozorro существует запись с таким же edrpo,
    данные из prozorro будут добавлены в ту же строку.
    
    Параметры:
      engine: SQLAlchemy engine для подключения к БД.
      output_file: Путь к выходному Excel-файлу.
    """
    # Загружаем данные из таблицы ubki
    df_ubki = pd.read_sql_table("ubki", con=engine)
    
    # Загружаем данные из таблицы prozorro
    df_prozorro = pd.read_sql_table("prozorro", con=engine)
    
    # Объединяем DataFrame по столбцу edrpo (left join: все строки из df_ubki,
    # а данные из df_prozorro добавляются для совпадающих edrpo)
    df_merged = pd.merge(df_ubki, df_prozorro, on="edrpo", how="left")
    
    # Экспортируем объединённые данные в Excel-файл
    df_merged.to_excel(output_file, index=False)
    print(f"Данные успешно экспортированы в файл: {output_file}")

def main():
    # Создаём подключение к БД и создаём таблицу (если ещё не создана)
    engine = create_db_connection()
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Определяем пути к CSV-файлам с помощью pathlib
    base_path = Path('.')  # можно изменить на нужную директорию
    fop_csv = base_path / 'fop.csv'
    legal_csv = base_path / 'legal.csv'
    prozorro_csv = base_path / 'prozorro.csv'
    
    # Загружаем данные из обоих CSV в единую таблицу UBKI
    load_csv_to_db(session, fop_csv, UBKI, UBKI_COLUMNS)
    load_csv_to_db(session, legal_csv, UBKI, UBKI_COLUMNS)
    # Загружаем данные из prozorro.csv в таблицу Prozorro
    load_csv_to_db(session, prozorro_csv, Prozorro, PROZORRO_COLUMNS)
    

    # Определяем путь для Excel-файла
    output_file = Path("merged_data.xlsx")
    
    # Вызываем функцию экспорта
    export_to_excel(engine, output_file)

if __name__ == '__main__':
    main()