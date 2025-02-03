import pandas as pd
from sqlalchemy import Column, Integer, String, create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base
import pandas as pd
from sqlalchemy import Column, Integer, String, Text, create_engine, inspect, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# Создаем Base глобально
Base = declarative_base()

def create_db_connection(user="python_mysql", password="python_mysql", host="localhost", db="kg"):
    """Create database connection and return engine"""
    engine = create_engine(
        f"mysql+pymysql://{user}:{password}@{host}/{db}", echo=True
    )
    return engine

def define_models(Base):
    """Define all database models"""
    
    class LoadingKyrgyzstan(Base):
        __tablename__ = "loading_kyrgyzstan"
        id = Column(Integer, primary_key=True, autoincrement=True)
        naimenovanie = Column(Text)
        dr_nazva = Column(Text)
        naimenovanie_polnoe = Column(Text)
        adres = Column(Text)
        rukovodstvo = Column(Text)
        rukovodstvo_dolzhnost = Column(Text)
        telefon = Column(Text)
        elektronnyi_adres = Column(Text)
        sait = Column(Text)
        data_registratsii = Column(Text)
        data_pervonachalnoi_registratsii = Column(Text)
        sovladeltcy = Column(Text)
        inn = Column(String(255), index=True)
        registratsionnyi_nomer = Column(Text)
        kod_statistiki = Column(Text)
        region_registratsii = Column(Text)
        vid_deyatelnosti_otrasl = Column(Text)
        organizatsionno_pravovaya_forma = Column(Text)
        srednespisochnaia_chislennost_rabotnikov = Column(Text)

    class OsooKg(Base):
        __tablename__ = "osoo_kg"
        id = Column(Integer, primary_key=True, autoincrement=True)
        nazvanie = Column(Text)
        status = Column(Text)
        inn = Column(String(20), index=True)  # оставляем String для INN, так как это фиксированный формат
        vid_deyatelnosti = Column(Text)
        direktor = Column(Text)
        dop_info1 = Column(Text)
        dop_info2 = Column(Text)
        dop_info3 = Column(Text)
        dop_info4 = Column(Text)
        dop_info5 = Column(Text)
        poslednee_obnovlenie = Column(Text)
        forma = Column(Text)
        forma_sobstvennosti = Column(Text)
        kolichestvo_uchastnikov = Column(Text)
        registratsionnyi_nomer = Column(Text)
        okpo = Column(Text)
        adres = Column(Text)
        telefon = Column(Text)

    class OutputHtml(Base):
        __tablename__ = "output_html"
        id = Column(Integer, primary_key=True, autoincrement=True)
        bik = Column(Text)
        bank = Column(Text)
        data_registratsii = Column(Text)
        dolzhnost = Column(Text)
        inn = Column(String(20), index=True)  # оставляем String для INN
        naimenovanie_organizatsii = Column(Text)
        naselennyi_punkt = Column(Text)
        organizatsionno_pravovaya_forma = Column(Text)
        official_info = Column(Text)
        rschet = Column(Text)
        rabochii_telefon = Column(Text)
        rol = Column(Text)
        status = Column(Text)
        fio_polzovatelya = Column(Text)
        factual_address = Column(Text)
        elektronnaia_pochta = Column(Text)

    class Consolidated(Base):
        __tablename__ = "consolidated"
        id = Column(Integer, primary_key=True, autoincrement=True)
        inn = Column(String(20), unique=True)  # оставляем String для INN
        
        # Поля из osoo_kg
        osoo_nazvanie = Column(Text)
        osoo_status = Column(Text)
        osoo_vid_deyatelnosti = Column(Text)
        osoo_direktor = Column(Text)
        dop_info1 = Column(Text)
        dop_info2 = Column(Text)
        dop_info3 = Column(Text)
        dop_info4 = Column(Text)
        dop_info5 = Column(Text)
        poslednee_obnovlenie = Column(Text)
        forma = Column(Text)
        forma_sobstvennosti = Column(Text)
        kolichestvo_uchastnikov = Column(Text)
        osoo_registratsionnyi_nomer = Column(Text)
        okpo = Column(Text)
        osoo_adres = Column(Text)
        osoo_telefon = Column(Text)
        
        # Поля из Loading Kyrgyzstan
        loading_naimenovanie = Column(Text)
        dr_nazva = Column(Text)
        naimenovanie_polnoe = Column(Text)
        loading_rukovodstvo = Column(Text)
        loading_rukovodstvo_dolzhnost = Column(Text)
        loading_elektronnyi_adres = Column(Text)
        loading_sait = Column(Text)
        loading_data_registratsii = Column(Text)
        data_pervonachalnoi_registratsii = Column(Text)
        sovladeltcy = Column(Text)
        kod_statistiki = Column(Text)
        region_registratsii = Column(Text)
        vid_deyatelnosti_otrasl = Column(Text)
        loading_org_pravovaya_forma = Column(Text)
        srednespisochnaia_chislennost_rabotnikov = Column(Text)
        
        # Поля из output_html
        bik = Column(Text)
        bank = Column(Text)
        html_data_registratsii = Column(Text)
        html_dolzhnost = Column(Text)
        naimenovanie_organizatsii = Column(Text)
        naselennyi_punkt = Column(Text)
        html_org_pravovaya_forma = Column(Text)
        official_info = Column(Text)
        rschet = Column(Text)
        rabochii_telefon = Column(Text)
        rol = Column(Text)
        html_status = Column(Text)
        fio_polzovatelya = Column(Text)
        factual_address = Column(Text)
        elektronnaia_pochta = Column(Text)

    return LoadingKyrgyzstan, OsooKg, OutputHtml, Consolidated

def create_tables_if_not_exist(engine, Base):
    """Create tables if they don't exist"""
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    if not all(table in existing_tables for table in ['loading_kyrgyzstan', 'osoo_kg', 'output_html', 'consolidated']):
        Base.metadata.create_all(engine)
        print("Tables created successfully.")
    else:
        print("All tables already exist.")

def create_session(engine):
    """Create and return a new session"""
    Session = sessionmaker(bind=engine)
    return Session()

def import_loading_kyrgyzstan_data(session, LoadingKyrgyzstan, csv_path):
    """Import data into LoadingKyrgyzstan table"""
    loading_df = pd.read_csv(csv_path, sep=";", low_memory=False)
    # Заменяем nan на None
    loading_df = loading_df.replace({pd.NA: None, pd.NaT: None})
    loading_df = loading_df.where(pd.notna(loading_df), None)
    
    loading_records = []
    
    for _, row in loading_df.iterrows():
        # Создаем словарь с данными
        record_data = {
            'naimenovanie': row.get("Наименование"),
            'dr_nazva': row.get("ДР +Назва"),
            'naimenovanie_polnoe': row.get("Наименование полное"),
            'adres': row.get("Адрес"),
            'rukovodstvo': row.get("Руководство"),
            'rukovodstvo_dolzhnost': row.get("Руководство - должность"),
            'telefon': row.get("Телефон"),
            'elektronnyi_adres': row.get("Электронный адрес"),
            'sait': row.get("Сайт в сети Интернет"),
            'data_registratsii': row.get("Дата регистрации"),
            'data_pervonachalnoi_registratsii': row.get("Дата первичной регистрации"),
            'sovladeltcy': row.get("Совладельцы"),
            'inn': row.get("INN"),
            'registratsionnyi_nomer': row.get("Регистрационный номер"),
            'kod_statistiki': row.get("Код статистики"),
            'region_registratsii': row.get("Регион регистрации"),
            'vid_deyatelnosti_otrasl': row.get("Вид деятельности/отрасль"),
            'organizatsionno_pravovaya_forma': row.get("Организационно-правовая форма"),
            'srednespisochnaia_chislennost_rabotnikov': row.get("Среднесписочная численность работников")
        }
        
        # Заменяем nan на None
        record_data = {k: None if pd.isna(v) else v for k, v in record_data.items()}
        
        # Создаем запись
        record = LoadingKyrgyzstan(**record_data)
        loading_records.append(record)
    
    session.bulk_save_objects(loading_records)
    session.commit()
    print("LoadingKyrgyzstan data imported successfully")

def import_osoo_kg_data(session, OsooKg, csv_path):
    """Import data into OsooKg table"""
    osoo_df = pd.read_csv(csv_path, sep=";", low_memory=False)
    # Заменяем nan на None
    osoo_df = osoo_df.replace({pd.NA: None, pd.NaT: None})
    osoo_df = osoo_df.where(pd.notna(osoo_df), None)
    
    osoo_records = []
    
    for _, row in osoo_df.iterrows():
        # Создаем словарь с данными
        record_data = {
            'nazvanie': row.get("Название"),
            'status': row.get("Статус"),
            'inn': row.get("INN"),
            'vid_deyatelnosti': row.get("Вид деятельности"),
            'direktor': row.get("Директор"),
            'dop_info1': row.get("Дополнительная информация 1"),
            'dop_info2': row.get("Дополнительная информация 2"),
            'dop_info3': row.get("Дополнительная информация 3"),
            'dop_info4': row.get("Дополнительная информация 4"),
            'dop_info5': row.get("Дополнительная информация 5"),
            'poslednee_obnovlenie': row.get("Последнее обновление"),
            'forma': row.get("Форма"),
            'forma_sobstvennosti': row.get("Форма собственности"),
            'kolichestvo_uchastnikov': row.get("Количество участников"),
            'registratsionnyi_nomer': row.get("Регистрационный номер"),
            'okpo': row.get("ОКПО"),
            'adres': row.get("Адрес"),
            'telefon': row.get("Телефон")
        }
        
        # Заменяем nan на None
        record_data = {k: None if pd.isna(v) else v for k, v in record_data.items()}
        
        # Создаем запись
        record = OsooKg(**record_data)
        osoo_records.append(record)
    
    session.bulk_save_objects(osoo_records)
    session.commit()
    print("OsooKg data imported successfully")

def import_output_html_data(session, OutputHtml, csv_path):
    """Import data into OutputHtml table"""
    output_df = pd.read_csv(csv_path, sep=";", low_memory=False)
    # Заменяем nan на None
    output_df = output_df.replace({pd.NA: None, pd.NaT: None})
    output_df = output_df.where(pd.notna(output_df), None)
    
    output_records = []
    
    for _, row in output_df.iterrows():
        # Создаем словарь с данными
        record_data = {
            'bik': row.get("БИК"),
            'bank': row.get("Банк"),
            'data_registratsii': row.get("Дата регистрации"),
            'dolzhnost': row.get("Должность"),
            'inn': row.get("INN"),
            'naimenovanie_organizatsii': row.get("Наименование организации"),
            'naselennyi_punkt': row.get("Населённый пункт"),
            'organizatsionno_pravovaya_forma': row.get("Организационно-правовая форма"),
            'official_info': row.get("Официальное информационное письмо по банковскому реквизиту"),
            'rschet': row.get("Р/счет"),
            'rabochii_telefon': row.get("Рабочий телефон"),
            'rol': row.get("Роль"),
            'status': row.get("Статус"),
            'fio_polzovatelya': row.get("ФИО пользователя"),
            'factual_address': row.get("Фактический адрес"),
            'elektronnaia_pochta': row.get("Электронная почта")
        }
        
        # Заменяем nan на None
        record_data = {k: None if pd.isna(v) else v for k, v in record_data.items()}
        
        # Создаем запись
        record = OutputHtml(**record_data)
        output_records.append(record)
    
    session.bulk_save_objects(output_records)
    session.commit()
    print("OutputHtml data imported successfully")

def create_consolidated_data(session, OsooKg, LoadingKyrgyzstan, OutputHtml, Consolidated):
    # """Create consolidated data from all tables"""
    # # Получаем все уникальные INN из всех таблиц
    # osoo_inns = set(row[0] for row in session.query(OsooKg.inn).all())
    # loading_inns = set(row[0] for row in session.query(LoadingKyrgyzstan.inn).all())
    # output_inns = set(row[0] for row in session.query(OutputHtml.inn).all())
    
    # # Объединяем все INN
    # all_inns = osoo_inns.union(loading_inns).union(output_inns)
    # print(f"Всего уникальных INN: {len(all_inns)}")
    # print(f"INN в OsooKg: {len(osoo_inns)}")
    # print(f"INN в LoadingKyrgyzstan: {len(loading_inns)}")
    # print(f"INN в OutputHtml: {len(output_inns)}")
    
    # for inn_val in all_inns:
    #     # Проверяем существование записи
    #     consolidated = session.query(Consolidated).filter(Consolidated.inn == inn_val).first()
        
    #     # Если записи нет - создаем новую
    #     if not consolidated:
    #         consolidated = Consolidated(inn=inn_val)
    #         session.add(consolidated)
        
    #     # Получаем и добавляем данные из OsooKg
    #     osoo = session.query(OsooKg).filter(OsooKg.inn == inn_val).first()
    #     if osoo:
    #         if consolidated.osoo_nazvanie is None:
    #             consolidated.osoo_nazvanie = osoo.nazvanie
    #         if consolidated.osoo_status is None:
    #             consolidated.osoo_status = osoo.status
    #         if consolidated.osoo_vid_deyatelnosti is None:
    #             consolidated.osoo_vid_deyatelnosti = osoo.vid_deyatelnosti
    #         if consolidated.osoo_direktor is None:
    #             consolidated.osoo_direktor = osoo.direktor
    #         if consolidated.dop_info1 is None:
    #             consolidated.dop_info1 = osoo.dop_info1
    #         if consolidated.dop_info2 is None:
    #             consolidated.dop_info2 = osoo.dop_info2
    #         if consolidated.dop_info3 is None:
    #             consolidated.dop_info3 = osoo.dop_info3
    #         if consolidated.dop_info4 is None:
    #             consolidated.dop_info4 = osoo.dop_info4
    #         if consolidated.dop_info5 is None:
    #             consolidated.dop_info5 = osoo.dop_info5
    #         if consolidated.poslednee_obnovlenie is None:
    #             consolidated.poslednee_obnovlenie = osoo.poslednee_obnovlenie
    #         if consolidated.forma is None:
    #             consolidated.forma = osoo.forma
    #         if consolidated.forma_sobstvennosti is None:
    #             consolidated.forma_sobstvennosti = osoo.forma_sobstvennosti
    #         if consolidated.kolichestvo_uchastnikov is None:
    #             consolidated.kolichestvo_uchastnikov = osoo.kolichestvo_uchastnikov
    #         if consolidated.osoo_registratsionnyi_nomer is None:
    #             consolidated.osoo_registratsionnyi_nomer = osoo.registratsionnyi_nomer
    #         if consolidated.okpo is None:
    #             consolidated.okpo = osoo.okpo
    #         if consolidated.osoo_adres is None:
    #             consolidated.osoo_adres = osoo.adres
    #         if consolidated.osoo_telefon is None:
    #             consolidated.osoo_telefon = osoo.telefon
        
    #     # Получаем и добавляем данные из LoadingKyrgyzstan
    #     loading = session.query(LoadingKyrgyzstan).filter(LoadingKyrgyzstan.inn == inn_val).first()
    #     if loading:
    #         if consolidated.loading_naimenovanie is None:
    #             consolidated.loading_naimenovanie = loading.naimenovanie
    #         if consolidated.dr_nazva is None:
    #             consolidated.dr_nazva = loading.dr_nazva
    #         if consolidated.naimenovanie_polnoe is None:
    #             consolidated.naimenovanie_polnoe = loading.naimenovanie_polnoe
    #         if consolidated.loading_rukovodstvo is None:
    #             consolidated.loading_rukovodstvo = loading.rukovodstvo
    #         if consolidated.loading_rukovodstvo_dolzhnost is None:
    #             consolidated.loading_rukovodstvo_dolzhnost = loading.rukovodstvo_dolzhnost
    #         if consolidated.loading_elektronnyi_adres is None:
    #             consolidated.loading_elektronnyi_adres = loading.elektronnyi_adres
    #         if consolidated.loading_sait is None:
    #             consolidated.loading_sait = loading.sait
    #         if consolidated.loading_data_registratsii is None:
    #             consolidated.loading_data_registratsii = loading.data_registratsii
    #         if consolidated.data_pervonachalnoi_registratsii is None:
    #             consolidated.data_pervonachalnoi_registratsii = loading.data_pervonachalnoi_registratsii
    #         if consolidated.sovladeltcy is None:
    #             consolidated.sovladeltcy = loading.sovladeltcy
    #         if consolidated.kod_statistiki is None:
    #             consolidated.kod_statistiki = loading.kod_statistiki
    #         if consolidated.region_registratsii is None:
    #             consolidated.region_registratsii = loading.region_registratsii
    #         if consolidated.vid_deyatelnosti_otrasl is None:
    #             consolidated.vid_deyatelnosti_otrasl = loading.vid_deyatelnosti_otrasl
    #         if consolidated.loading_org_pravovaya_forma is None:
    #             consolidated.loading_org_pravovaya_forma = loading.organizatsionno_pravovaya_forma
    #         if consolidated.srednespisochnaia_chislennost_rabotnikov is None:
    #             consolidated.srednespisochnaia_chislennost_rabotnikov = loading.srednespisochnaia_chislennost_rabotnikov

    #     # Получаем и добавляем данные из OutputHtml
    #     output = session.query(OutputHtml).filter(OutputHtml.inn == inn_val).first()
    #     if output:
    #         if consolidated.bik is None:
    #             consolidated.bik = output.bik
    #         if consolidated.bank is None:
    #             consolidated.bank = output.bank
    #         if consolidated.html_data_registratsii is None:
    #             consolidated.html_data_registratsii = output.data_registratsii
    #         if consolidated.html_dolzhnost is None:
    #             consolidated.html_dolzhnost = output.dolzhnost
    #         if consolidated.naimenovanie_organizatsii is None:
    #             consolidated.naimenovanie_organizatsii = output.naimenovanie_organizatsii
    #         if consolidated.naselennyi_punkt is None:
    #             consolidated.naselennyi_punkt = output.naselennyi_punkt
    #         if consolidated.html_org_pravovaya_forma is None:
    #             consolidated.html_org_pravovaya_forma = output.organizatsionno_pravovaya_forma
    #         if consolidated.official_info is None:
    #             consolidated.official_info = output.official_info
    #         if consolidated.rschet is None:
    #             consolidated.rschet = output.rschet
    #         if consolidated.rabochii_telefon is None:
    #             consolidated.rabochii_telefon = output.rabochii_telefon
    #         if consolidated.rol is None:
    #             consolidated.rol = output.rol
    #         if consolidated.html_status is None:
    #             consolidated.html_status = output.status
    #         if consolidated.fio_polzovatelya is None:
    #             consolidated.fio_polzovatelya = output.fio_polzovatelya
    #         if consolidated.factual_address is None:
    #             consolidated.factual_address = output.factual_address
    #         if consolidated.elektronnaia_pochta is None:
    #             consolidated.elektronnaia_pochta = output.elektronnaia_pochta
        
    #     # Сохраняем изменения каждые 1000 записей
    #     if len(all_inns) % 1000 == 0:
    #         session.commit()
    #         print(f"Обработано {len(all_inns)} записей")

    # # Сохраняем оставшиеся изменения
    # session.commit()
    
    # Объединяем дублирующиеся записи
    merge_duplicate_inns(session, Consolidated)
    
    print("Консолидированные данные успешно созданы")
def merge_duplicate_inns(session, Consolidated):
    """
    Объединяет записи с одинаковыми INN в таблице Consolidated
    """
    print("Начинаем поиск и объединение дублирующихся INN...")
    
    # Находим все INN, которые встречаются более одного раза
    duplicate_inns = session.query(Consolidated.inn).group_by(Consolidated.inn).having(func.count(Consolidated.inn) > 1).all()
    
    print(f"Найдено {len(duplicate_inns)} INN с дублирующимися записями")
    
    for (inn,) in duplicate_inns:
        # Получаем все записи для текущего INN
        records = session.query(Consolidated).filter(Consolidated.inn == inn).all()
        if len(records) <= 1:
            continue
            
        # Берем первую запись как основную
        base_record = records[0]
        
        # Объединяем данные из остальных записей
        for record in records[1:]:
            # Проходим по всем атрибутам записи
            for attr in dir(record):
                # Пропускаем служебные атрибуты и методы
                if attr.startswith('_') or callable(getattr(record, attr)):
                    continue
                    
                # Получаем значение атрибута
                value = getattr(record, attr)
                
                # Если в базовой записи значение пустое, а в текущей есть - копируем
                if value is not None and getattr(base_record, attr) is None:
                    setattr(base_record, attr, value)
            
            # Удаляем дополнительную запись
            session.delete(record)
        
        # Сохраняем изменения
        session.commit()
        
    print("Объединение дублирующихся записей завершено")
def clear_table(session, table_class):
    """Очистить указанную таблицу"""
    try:
        session.query(table_class).delete()
        session.commit()
        print(f"Таблица {table_class.__tablename__} успешно очищена")
    except Exception as e:
        print(f"Ошибка при очистке таблицы {table_class.__tablename__}: {str(e)}")
        session.rollback()

def drop_tables(engine):
    """Удаляет все существующие таблицы"""
    Base.metadata.drop_all(engine)
    print("Все таблицы успешно удалены")
def export_consolidated_to_excel(session, Consolidated, output_file="consolidated_data.xlsx"):
    """
    Экспортирует данные из таблицы consolidated в Excel файл
    
    Args:
        session: SQLAlchemy сессия
        Consolidated: модель таблицы Consolidated
        output_file: путь к выходному файлу Excel
    """
    try:
        # Получаем все записи из таблицы
        print("Загрузка данных из базы...")
        records = session.query(Consolidated).all()
        
        # Преобразуем в список словарей
        data = []
        for record in records:
            data.append({
                'ИНН': record.inn,
                
                # Данные из osoo_kg
                'Название (osoo)': record.osoo_nazvanie,
                'Статус (osoo)': record.osoo_status,
                'Вид деятельности (osoo)': record.osoo_vid_deyatelnosti,
                'Директор': record.osoo_direktor,
                'Доп. информация 1': record.dop_info1,
                'Доп. информация 2': record.dop_info2,
                'Доп. информация 3': record.dop_info3,
                'Доп. информация 4': record.dop_info4,
                'Доп. информация 5': record.dop_info5,
                'Последнее обновление': record.poslednee_obnovlenie,
                'Форма': record.forma,
                'Форма собственности': record.forma_sobstvennosti,
                'Количество участников': record.kolichestvo_uchastnikov,
                'Рег. номер (osoo)': record.osoo_registratsionnyi_nomer,
                'ОКПО': record.okpo,
                'Адрес (osoo)': record.osoo_adres,
                'Телефон (osoo)': record.osoo_telefon,
                
                # Данные из Loading Kyrgyzstan
                'Наименование (loading)': record.loading_naimenovanie,
                'ДР +Назва': record.dr_nazva,
                'Полное наименование': record.naimenovanie_polnoe,
                'Руководство': record.loading_rukovodstvo,
                'Должность руководства': record.loading_rukovodstvo_dolzhnost,
                'Электронный адрес': record.loading_elektronnyi_adres,
                'Сайт': record.loading_sait,
                'Дата регистрации (loading)': record.loading_data_registratsii,
                'Дата первичной регистрации': record.data_pervonachalnoi_registratsii,
                'Совладельцы': record.sovladeltcy,
                'Код статистики': record.kod_statistiki,
                'Регион регистрации': record.region_registratsii,
                'Вид деятельности/отрасль': record.vid_deyatelnosti_otrasl,
                'Орг.-правовая форма (loading)': record.loading_org_pravovaya_forma,
                'Среднесписочная численность': record.srednespisochnaia_chislennost_rabotnikov,
                
                # Данные из output_html
                'БИК': record.bik,
                'Банк': record.bank,
                'Дата регистрации (html)': record.html_data_registratsii,
                'Должность': record.html_dolzhnost,
                'Наименование организации': record.naimenovanie_organizatsii,
                'Населенный пункт': record.naselennyi_punkt,
                'Орг.-правовая форма (html)': record.html_org_pravovaya_forma,
                'Банковские реквизиты': record.official_info,
                'Р/счет': record.rschet,
                'Рабочий телефон': record.rabochii_telefon,
                'Роль': record.rol,
                'Статус (html)': record.html_status,
                'ФИО пользователя': record.fio_polzovatelya,
                'Фактический адрес': record.factual_address,
                'Электронная почта': record.elektronnaia_pochta
            })
        
        # Создаем DataFrame
        print("Создание Excel файла...")
        df = pd.DataFrame(data)
        
        # Записываем в Excel
        writer = pd.ExcelWriter(output_file, engine='openpyxl')
        df.to_excel(writer, index=False)
        
        # Автоматическая ширина столбцов
        worksheet = writer.sheets['Sheet1']
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).apply(len).max(),
                len(col)
            )
            worksheet.column_dimensions[worksheet.cell(row=1, column=idx+1).column_letter].width = max_length + 2
        
        writer.close()
        print(f"Данные успешно экспортированы в файл: {output_file}")
        print(f"Всего записей: {len(data)}")
        
    except Exception as e:
        print(f"Ошибка при экспорте данных: {str(e)}")
# Функция объединения данных
def consolidate_data(session, models):
    """
    Объединяет данные из таблиц OsooKg, LoadingKyrgyzstan и OutputHtml.
    В результате для каждого уникального нормализованного INN создаётся одна запись
    в таблице Consolidated. В качестве базы берём записи из OsooKg, но если в других таблицах
    присутствуют INN, которых нет в OsooKg, они тоже добавляются.
    """
    LoadingKyrgyzstan, OsooKg, OutputHtml, Consolidated = models

    # Словарь для объединения: ключ – нормализованный INN, значение – словарь с данными
    merged = {}

    # Обрабатываем таблицу OsooKg (базовая)
    for rec in session.query(OsooKg).all():
        norm_inn = normalize_inn(rec.inn)
        if not norm_inn:
            continue
        merged.setdefault(norm_inn, {})["osoo"] = rec

    # Обрабатываем таблицу LoadingKyrgyzstan
    for rec in session.query(LoadingKyrgyzstan).all():
        norm_inn = normalize_inn(rec.inn)
        if not norm_inn:
            continue
        merged.setdefault(norm_inn, {})["loading"] = rec

    # Обрабатываем таблицу OutputHtml
    for rec in session.query(OutputHtml).all():
        norm_inn = normalize_inn(rec.inn)
        if not norm_inn:
            continue
        merged.setdefault(norm_inn, {})["output"] = rec

    consolidated_records = []
    for norm_inn, data in merged.items():
        # Заполняем поля из OsooKg, если есть
        osoo = data.get("osoo")
        loading = data.get("loading")
        output = data.get("output")
        
        cons = Consolidated(
            inn=norm_inn,
            # Из OsooKg:
            osoo_nazvanie = osoo.nazvanie if osoo else None,
            osoo_status = osoo.status if osoo else None,
            osoo_vid_deyatelnosti = osoo.vid_deyatelnosti if osoo else None,
            osoo_direktor = osoo.direktor if osoo else None,
            dop_info1 = osoo.dop_info1 if osoo else None,
            dop_info2 = osoo.dop_info2 if osoo else None,
            dop_info3 = osoo.dop_info3 if osoo else None,
            dop_info4 = osoo.dop_info4 if osoo else None,
            dop_info5 = osoo.dop_info5 if osoo else None,
            poslednee_obnovlenie = osoo.poslednee_obnovlenie if osoo else None,
            forma = osoo.forma if osoo else None,
            forma_sobstvennosti = osoo.forma_sobstvennosti if osoo else None,
            kolichestvo_uchastnikov = osoo.kolichestvo_uchastnikov if osoo else None,
            osoo_registratsionnyi_nomer = osoo.registratsionnyi_nomer if osoo else None,
            okpo = osoo.okpo if osoo else None,
            osoo_adres = osoo.adres if osoo else None,
            osoo_telefon = osoo.telefon if osoo else None,
            
            # Из LoadingKyrgyzstan:
            loading_naimenovanie = loading.naimenovanie if loading else None,
            dr_nazva = loading.dr_nazva if loading else None,
            naimenovanie_polnoe = loading.naimenovanie_polnoe if loading else None,
            loading_rukovodstvo = loading.rukovodstvo if loading else None,
            loading_rukovodstvo_dolzhnost = loading.rukovodstvo_dolzhnost if loading else None,
            loading_elektronnyi_adres = loading.elektronnyi_adres if loading else None,
            loading_sait = loading.sait if loading else None,
            loading_data_registratsii = loading.data_registratsii if loading else None,
            data_pervonachalnoi_registratsii = loading.data_pervonachalnoi_registratsii if loading else None,
            sovladeltcy = loading.sovladeltcy if loading else None,
            kod_statistiki = loading.kod_statistiki if loading else None,
            region_registratsii = loading.region_registratsii if loading else None,
            vid_deyatelnosti_otrasl = loading.vid_deyatelnosti_otrasl if loading else None,
            loading_org_pravovaya_forma = loading.organizatsionno_pravovaya_forma if loading else None,
            srednespisochnaia_chislennost_rabotnikov = loading.srednespisochnaia_chislennost_rabotnikov if loading else None,
            
            # Из OutputHtml:
            bik = output.bik if output else None,
            bank = output.bank if output else None,
            html_data_registratsii = output.data_registratsii if output else None,
            html_dolzhnost = output.dolzhnost if output else None,
            naimenovanie_organizatsii = output.naimenovanie_organizatsii if output else None,
            naselennyi_punkt = output.naselennyi_punkt if output else None,
            html_org_pravovaya_forma = output.organizatsionno_pravovaya_forma if output else None,
            official_info = output.official_info if output else None,
            rschet = output.rschet if output else None,
            rabochii_telefon = output.rabochii_telefon if output else None,
            rol = output.rol if output else None,
            html_status = output.status if output else None,
            fio_polzovatelya = output.fio_polzovatelya if output else None,
            factual_address = output.factual_address if output else None,
            elektronnaia_pochta = output.elektronnaia_pochta if output else None,
        )
        consolidated_records.append(cons)
    
    session.bulk_save_objects(consolidated_records)
    session.commit()
    print("Сводная таблица создана с", len(consolidated_records), "записями.")

# Функция для нормализации INN (убираем ведущие нули)
def normalize_inn(inn):
    if not inn:
        return None
    norm = inn.lstrip("0")
    return norm if norm else "0"

def main():
    """
    Основная функция для запуска всего процесса импорта и обработки данных
    """
    try:
        # Создаем подключение к базе данных
        engine = create_db_connection()
        
        # Определяем модели таблиц
        # LoadingKyrgyzstan, OsooKg, OutputHtml, Consolidated = define_models(Base)
        
        # # Удаляем существующие таблицы
        # drop_tables(engine)
        
        # # Создаем таблицы заново
        # Base.metadata.create_all(engine)
        # print("Таблицы успешно созданы")
        
        # Создаем сессию
        session = create_session(engine)
        
        # # Очищаем таблицы перед импортом (опционально)
        # should_clear = input("Очистить существующие данные перед импортом? (да/нет): ").lower()
        # if should_clear == 'да':
        #     clear_table(session, LoadingKyrgyzstan)
        #     clear_table(session, OsooKg)
        #     clear_table(session, OutputHtml)
        #     clear_table(session, Consolidated)
        
        # # Импортируем данные
        # print("\nНачинаем импорт данных...")
        # import_loading_kyrgyzstan_data(session, LoadingKyrgyzstan, "Loading Kyrgyzstan.csv")
        # import_osoo_kg_data(session, OsooKg, "osoo_kg.csv")
        # import_output_html_data(session, OutputHtml, "output_html.csv")
        
        # # Создаем консолидированные данные
        # print("\nНачинаем создание консолидированных данных...")
        # create_consolidated_data(session, OsooKg, LoadingKyrgyzstan, OutputHtml, Consolidated)
        # Определяем модели
        models = define_models(Base)
        LoadingKyrgyzstan, OsooKg, OutputHtml, Consolidated = models
        
        
        export_consolidated_to_excel(session, Consolidated, "consolidated_data.xlsx")

    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
    finally:
        if 'session' in locals():
            session.close()

if __name__ == "__main__":
    main()