# from databases import Database
# import sqlalchemy
from sqlalchemy import create_engine, text
import asyncio
from configuration.config import database, database_name, initial_database_url
from configuration.logging_config import logger


# Функция для создания базы данных
def create_database(engine, db_name):
    with engine.connect() as connection:
        result = connection.execute(text(f"SHOW DATABASES LIKE '{db_name}'"))
        if not result.fetchone():
            connection.execute(text(f"CREATE DATABASE `{db_name}`"))
            logger.info(f"База данных `{db_name}` создана.")
        else:
            logger.info(f"База данных `{db_name}` уже существует.")


# SQL запросы для создания таблиц
create_table_uni_com_all = """
CREATE TABLE IF NOT EXISTS uni_com_all (
    id INT AUTO_INCREMENT PRIMARY KEY,
    accnum TEXT,
    card TEXT,
    mapblocklot TEXT,
    locat TEXT,
    zoning TEXT,
    stateclass TEXT,
    acres TEXT,
    livingunits TEXT,
    ownername TEXT,
    owneradd1 TEXT,
    owneradd2 TEXT,
    owneradd3 TEXT,
    bookpage TEXT,
    deeddate TEXT,
    buildingno TEXT,
    yearbuilt TEXT,
    noofunits TEXT,
    structuretype TEXT,
    grade TEXT,
    identicalunits TEXT,
    land TEXT,
    building TEXT,
    total TEXT,
    netassessment TEXT,
    bookpage1 TEXT,
    date1 TEXT,
    price1 TEXT,
    type1 TEXT,
    validity1 TEXT,
    bookpage2 TEXT,
    date2 TEXT,
    price2 TEXT,
    type2 TEXT,
    validity2 TEXT,
    structurecode1 TEXT,
    width1 TEXT,
    lgth_sf1 TEXT,
    year1 TEXT,
    rcnld1 TEXT,
    structurecode2 TEXT,
    width2 TEXT,
    lgth_sf2 TEXT,
    year2 TEXT,
    rcnld2 TEXT,
    levels1 TEXT,
    size1 TEXT,
    usetype1 TEXT,
    extwalls1 TEXT,
    consttype1 TEXT,
    partitions1 TEXT,
    heating1 TEXT,
    aircond1 TEXT,
    plumbing1 TEXT,
    condition1 TEXT,
    funcutility1 TEXT,
    unadjrcnld1 TEXT,
    levels2 TEXT,
    size2 TEXT,
    usetype2 TEXT,
    extwalls2 TEXT,
    consttype2 TEXT,
    partitions2 TEXT,
    heating2 TEXT,
    aircond2 TEXT,
    plumbing2 TEXT,
    condition2 TEXT,
    funcutility2 TEXT,
    unadjrcnld2 TEXT,
    levels3 TEXT,
    size3 TEXT,
    usetype3 TEXT,
    extwalls3 TEXT,
    consttype3 TEXT,
    partitions3 TEXT,
    heating3 TEXT,
    aircond3 TEXT,
    plumbing3 TEXT,
    condition3 TEXT,
    funcutility3 TEXT,
    unadjrcnld3 TEXT,
    levels4 TEXT,
    size4 TEXT,
    usetype4 TEXT,
    extwalls4 TEXT,
    consttype4 TEXT,
    partitions4 TEXT,
    heating4 TEXT,
    aircond4 TEXT,
    plumbing4 TEXT,
    condition4 TEXT,
    funcutility4 TEXT,
    unadjrcnld4 TEXT,
    levels5 TEXT,
    size5 TEXT,
    usetype5 TEXT,
    extwalls5 TEXT,
    consttype5 TEXT,
    partitions5 TEXT,
    heating5 TEXT,
    aircond5 TEXT,
    plumbing5 TEXT,
    condition5 TEXT,
    funcutility5 TEXT,
    unadjrcnld5 TEXT
)
"""

create_table_uni_res_all = """
CREATE TABLE IF NOT EXISTS uni_res_all (
    id INT AUTO_INCREMENT PRIMARY KEY,
    accnum TEXT,
    card TEXT,
    mapblocklot TEXT,
    locat TEXT,
    zoning TEXT,
    stateclass TEXT,
    acres TEXT,
    livingunits TEXT,
    ownername TEXT,
    owneradd1 TEXT,
    owneradd2 TEXT,
    owneradd3 TEXT,
    bookpage TEXT,
    deeddate TEXT,
    style TEXT,
    story TEXT,
    attic TEXT,
    basement TEXT,
    yearbuilt TEXT,
    groundflrarea TEXT,
    totlivingarea TEXT,
    rooms TEXT,
    bedrooms TEXT,
    fullbaths TEXT,
    halfbaths TEXT,
    land TEXT,
    building TEXT,
    total TEXT,
    netassessment TEXT,
    bookpage1 TEXT,
    date1 TEXT,
    price1 TEXT,
    type1 TEXT,
    validity1 TEXT,
    bookpage2 TEXT,
    date2 TEXT,
    price2 TEXT,
    type2 TEXT,
    validity2 TEXT,
    outbuildingtype1 TEXT,
    qty1 TEXT,
    year1 TEXT,
    size1_1 TEXT,
    size1_2 TEXT,
    grade1 TEXT,
    cond1 TEXT,
    outbuildingtype2 TEXT,
    qty2 TEXT,
    year2 TEXT,
    size2_1 TEXT,
    size2_2 TEXT,
    grade2 TEXT,
    cond2 TEXT
)
"""


async def create_tables():
    await database.connect()
    async with database.transaction():
        tables = ["uni_com_all", "uni_res_all"]
        for table in tables:
            result = await database.fetch_one(text(f"SHOW TABLES LIKE '{table}'"))
            if result:
                logger.info(f"Таблица `{table}` уже существует.")
            else:
                if table == "uni_com_all":
                    await database.execute(create_table_uni_com_all)
                elif table == "uni_res_all":
                    await database.execute(create_table_uni_res_all)
                logger.info(f"Таблица `{table}` создана.")
    await database.disconnect()


# Запуск создания базы данных и таблиц
def initialize_db():
    engine = create_engine(initial_database_url)
    create_database(engine, database_name)

    asyncio.run(create_tables())


if __name__ == "__main__":
    initialize_db()
