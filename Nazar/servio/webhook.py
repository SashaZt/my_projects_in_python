import asyncio
import asyncpg
import aiohttp
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from config.config import Config
from config.logger import logger


class HotelDatabaseManager:
    """Менеджер для работы с базой данных отеля"""
    
    def __init__(self, config: Config):
        self.config = config
        self.connection_string = config.db.get_connection_string()
        
    async def get_connection(self):
        """Получить соединение с базой данных"""
        return await asyncpg.connect(
            host=self.config.db.host,
            port=self.config.db.port,
            user=self.config.db.user,
            password=self.config.db.password,
            database=self.config.db.database
        )
    
    def _map_guest_data(self, guest_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Преобразует словарь с украинскими ключами в словарь с английскими ключами для БД
        """
        # Маппинг украинских ключей на английские поля БД
        field_mapping = {
            '№': 'guest_number',
            'О/рахунок': 'account_number',
            'Готель': 'hotel_code',
            'ПІБ': 'guest_name',
            'Заїзд': 'check_in_date',
            'Виїзд': 'check_out_date',
            'Др/Дт/ДО': 'room_config',
            'Кат.': 'category',
            'Комент.': 'comments',
            'До спл., грн.': 'amount_to_pay',
            'Кімн.': 'room_number',
            'Прайс.': 'price_code',
            'Компанія-оператор': 'operator_company',
            'Група': 'group_name',
            'Гр.': 'country_code',
            'Статус': 'status',
            'Тип опл.': 'payment_type',
            'Телефон': 'phone'
        }
        
        mapped_data = {}
        
        for uk_key, eng_key in field_mapping.items():
            if uk_key in guest_dict:
                value = guest_dict[uk_key]
                
                # Обработка специальных полей
                if eng_key in ['check_in_date', 'check_out_date']:
                    # Преобразование строки даты в datetime
                    if isinstance(value, str):
                        try:
                            mapped_data[eng_key] = datetime.strptime(value, '%d.%m.%Y %H:%M:%S')
                        except ValueError:
                            logger.warning(f"Не удалось преобразовать дату: {value}")
                            mapped_data[eng_key] = None
                    else:
                        mapped_data[eng_key] = value
                        
                elif eng_key == 'amount_to_pay':
                    # Преобразование суммы в decimal
                    if isinstance(value, str):
                        try:
                            # Убираем пробелы и заменяем запятую на точку
                            clean_value = value.replace(' ', '').replace(',', '.')
                            mapped_data[eng_key] = float(clean_value)
                        except ValueError:
                            logger.warning(f"Не удалось преобразовать сумму: {value}")
                            mapped_data[eng_key] = 0.0
                    else:
                        mapped_data[eng_key] = value
                        
                else:
                    # Обычные поля
                    mapped_data[eng_key] = value if value else None
        
        # Добавляем webhook_status по умолчанию
        mapped_data['webhook_status'] = False
        
        return mapped_data
    
    async def insert_guests(self, guests_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Вставляет массив данных гостей в базу данных
        
        Args:
            guests_data: Список словарей с данными гостей
            
        Returns:
            Словарь с результатами операции
        """
        logger.info(f"Начинаем вставку {len(guests_data)} записей гостей")
        
        result = {
            'total_records': len(guests_data),
            'inserted': 0,
            'updated': 0,
            'errors': 0,
            'error_details': []
        }
        
        conn = None
        try:
            conn = await self.get_connection()
            
            # SQL для вставки/обновления (UPSERT)
            upsert_sql = """
                INSERT INTO hotel_guests (
                    guest_number, account_number, hotel_code, guest_name,
                    check_in_date, check_out_date, room_config, category,
                    comments, amount_to_pay, room_number, price_code,
                    operator_company, group_name, country_code, status,
                    payment_type, phone, webhook_status
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19
                )
                ON CONFLICT (account_number) 
                DO UPDATE SET
                    guest_number = EXCLUDED.guest_number,
                    hotel_code = EXCLUDED.hotel_code,
                    guest_name = EXCLUDED.guest_name,
                    check_in_date = EXCLUDED.check_in_date,
                    check_out_date = EXCLUDED.check_out_date,
                    room_config = EXCLUDED.room_config,
                    category = EXCLUDED.category,
                    comments = EXCLUDED.comments,
                    amount_to_pay = EXCLUDED.amount_to_pay,
                    room_number = EXCLUDED.room_number,
                    price_code = EXCLUDED.price_code,
                    operator_company = EXCLUDED.operator_company,
                    group_name = EXCLUDED.group_name,
                    country_code = EXCLUDED.country_code,
                    status = EXCLUDED.status,
                    payment_type = EXCLUDED.payment_type,
                    phone = EXCLUDED.phone,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id, (xmax = 0) AS inserted
            """
            
            for i, guest_dict in enumerate(guests_data):
                try:
                    # Преобразуем данные
                    mapped_data = self._map_guest_data(guest_dict)
                    
                    # Подготавливаем параметры для запроса
                    params = [
                        mapped_data.get('guest_number'),
                        mapped_data.get('account_number'),
                        mapped_data.get('hotel_code'),
                        mapped_data.get('guest_name'),
                        mapped_data.get('check_in_date'),
                        mapped_data.get('check_out_date'),
                        mapped_data.get('room_config'),
                        mapped_data.get('category'),
                        mapped_data.get('comments'),
                        mapped_data.get('amount_to_pay'),
                        mapped_data.get('room_number'),
                        mapped_data.get('price_code'),
                        mapped_data.get('operator_company'),
                        mapped_data.get('group_name'),
                        mapped_data.get('country_code'),
                        mapped_data.get('status'),
                        mapped_data.get('payment_type'),
                        mapped_data.get('phone'),
                        mapped_data.get('webhook_status', False)
                    ]
                    
                    # Выполняем запрос
                    db_result = await conn.fetchrow(upsert_sql, *params)
                    
                    if db_result['inserted']:
                        result['inserted'] += 1
                        logger.debug(f"Вставлена новая запись для счета: {mapped_data.get('account_number')}")
                    else:
                        result['updated'] += 1
                        logger.debug(f"Обновлена запись для счета: {mapped_data.get('account_number')}")
                        
                except Exception as e:
                    result['errors'] += 1
                    error_msg = f"Ошибка при обработке записи {i+1}: {str(e)}"
                    result['error_details'].append(error_msg)
                    logger.error(error_msg)
                    logger.error(f"Проблемная запись: {guest_dict}")
            
            logger.info(f"Вставка завершена. Вставлено: {result['inserted']}, Обновлено: {result['updated']}, Ошибок: {result['errors']}")
            
        except Exception as e:
            logger.error(f"Критическая ошибка при работе с БД: {e}")
            result['errors'] = len(guests_data)
            result['error_details'].append(f"Критическая ошибка: {str(e)}")
            
        finally:
            if conn:
                await conn.close()
        
        return result
    
    async def send_webhooks(self, webhook_url: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        Отправляет webhook для всех записей со статусом webhook_status = FALSE
        
        Args:
            webhook_url: URL для отправки POST запросов
            max_retries: Максимальное количество попыток отправки
            
        Returns:
            Словарь с результатами операции
        """
        logger.info(f"Начинаем отправку webhook на URL: {webhook_url}")
        
        result = {
            'total_pending': 0,
            'sent_successfully': 0,
            'failed': 0,
            'error_details': []
        }
        
        conn = None
        try:
            conn = await self.get_connection()
            
            # Получаем все записи с webhook_status = FALSE
            select_sql = """
                SELECT id, guest_number, account_number, hotel_code, guest_name,
                       check_in_date, check_out_date, room_config, category,
                       comments, amount_to_pay, room_number, price_code,
                       operator_company, group_name, country_code, status,
                       payment_type, phone, created_at, updated_at
                FROM hotel_guests 
                WHERE webhook_status = FALSE
                ORDER BY created_at ASC
            """
            
            pending_records = await conn.fetch(select_sql)
            result['total_pending'] = len(pending_records)
            
            logger.info(f"Найдено {result['total_pending']} записей для отправки webhook")
            
            if result['total_pending'] == 0:
                return result
            
            # SQL для обновления статуса webhook
            update_sql = """
                UPDATE hotel_guests 
                SET webhook_status = TRUE, updated_at = CURRENT_TIMESTAMP 
                WHERE id = $1
            """
            
            # Отправляем webhook для каждой записи
            async with aiohttp.ClientSession() as session:
                for record in pending_records:
                    record_id = record['id']
                    account_number = record['account_number']
                    
                    try:
                        # Подготавливаем данные для отправки
                        webhook_data = {
                            'id': record_id,
                            'guest_number': record['guest_number'],
                            'account_number': account_number,
                            'hotel_code': record['hotel_code'],
                            'guest_name': record['guest_name'],
                            'check_in_date': record['check_in_date'].isoformat() if record['check_in_date'] else None,
                            'check_out_date': record['check_out_date'].isoformat() if record['check_out_date'] else None,
                            'room_config': record['room_config'],
                            'category': record['category'],
                            'comments': record['comments'],
                            'amount_to_pay': float(record['amount_to_pay']) if record['amount_to_pay'] else 0.0,
                            'room_number': record['room_number'],
                            'price_code': record['price_code'],
                            'operator_company': record['operator_company'],
                            'group_name': record['group_name'],
                            'country_code': record['country_code'],
                            'status': record['status'],
                            'payment_type': record['payment_type'],
                            'phone': record['phone'],
                            'created_at': record['created_at'].isoformat() if record['created_at'] else None,
                            'updated_at': record['updated_at'].isoformat() if record['updated_at'] else None
                        }
                        
                        # Попытки отправки с повторами
                        success = False
                        last_error = None
                        
                        for attempt in range(max_retries):
                            try:
                                logger.debug(f"Отправка webhook для счета {account_number}, попытка {attempt + 1}")
                                
                                async with session.post(
                                    webhook_url,
                                    json=webhook_data,
                                    headers={'Content-Type': 'application/json'},
                                    timeout=aiohttp.ClientTimeout(total=30)
                                ) as response:
                                    
                                    if response.status == 200:
                                        # Успешная отправка - обновляем статус в БД
                                        await conn.execute(update_sql, record_id)
                                        result['sent_successfully'] += 1
                                        success = True
                                        logger.info(f"Webhook успешно отправлен для счета {account_number}")
                                        break
                                    else:
                                        last_error = f"HTTP {response.status}: {await response.text()}"
                                        logger.warning(f"Неуспешный ответ для счета {account_number}: {last_error}")
                                        
                            except asyncio.TimeoutError:
                                last_error = "Timeout при отправке webhook"
                                logger.warning(f"Timeout для счета {account_number}, попытка {attempt + 1}")
                                
                            except Exception as e:
                                last_error = f"Ошибка отправки: {str(e)}"
                                logger.warning(f"Ошибка отправки для счета {account_number}, попытка {attempt + 1}: {last_error}")
                            
                            # Пауза между попытками
                            if attempt < max_retries - 1:
                                await asyncio.sleep(2 ** attempt)  # Экспоненциальная задержка
                        
                        if not success:
                            result['failed'] += 1
                            error_msg = f"Не удалось отправить webhook для счета {account_number} после {max_retries} попыток. Последняя ошибка: {last_error}"
                            result['error_details'].append(error_msg)
                            logger.error(error_msg)
                            
                    except Exception as e:
                        result['failed'] += 1
                        error_msg = f"Критическая ошибка при отправке webhook для счета {account_number}: {str(e)}"
                        result['error_details'].append(error_msg)
                        logger.error(error_msg)
            
            logger.info(f"Отправка webhook завершена. Успешно: {result['sent_successfully']}, Неудачно: {result['failed']}")
            
        except Exception as e:
            logger.error(f"Критическая ошибка при отправке webhook: {e}")
            result['error_details'].append(f"Критическая ошибка: {str(e)}")
            
        finally:
            if conn:
                await conn.close()
        
        return result


# Удобные функции для использования
async def save_guests_to_db(guests_data: List[Dict[str, Any]], config: Config) -> Dict[str, Any]:
    """
    Удобная функция для сохранения данных гостей в БД
    
    Args:
        guests_data: Список словарей с данными гостей
        config: Конфигурация приложения
        
    Returns:
        Результат операции
    """
    db_manager = HotelDatabaseManager(config)
    return await db_manager.insert_guests(guests_data)


async def send_pending_webhooks(webhook_url: str, config: Config, max_retries: int = 3) -> Dict[str, Any]:
    """
    Удобная функция для отправки всех pending webhook
    
    Args:
        webhook_url: URL для отправки webhook
        config: Конфигурация приложения
        max_retries: Максимальное количество попыток
        
    Returns:
        Результат операции
    """
    db_manager = HotelDatabaseManager(config)
    return await db_manager.send_webhooks(webhook_url, max_retries)


# Пример использования
async def main():
    """Пример использования функций"""
    
    # Загружаем конфигурацию
    config = Config.load()
    
    # Пример данных (как в вашем примере)
    sample_data = [
        {
            '№': '1',
            'О/рахунок': '0000006655',
            'Готель': 'ГЛС',
            'ПІБ': 'Анжеліка Кириченко',
            'Заїзд': '26.05.2025 13:37:33',
            'Виїзд': '30.05.2025 12:00:00',
            'Др/Дт/ДО': '1/0/0',
            'Кат.': 'РЗ',
            'Комент.': 'booked rate: 3d (27635450)\n. This client prefer a non-smoking room\nExtra Info:\nGENIUS RATE',
            'До спл., грн.': '0,00',
            'Кімн.': '303/1 1мБ',
            'Прайс.': 'RRB',
            'Компанія-оператор': 'Booking.com C0000000006',
            'Група': '',
            'Гр.': 'UKR',
            'Статус': 'ПР',
            'Тип опл.': 'ГОТ',
            'Телефон': '+380 66 136 3996'
        }
    ]
    
    # Сохраняем данные в БД
    logger.info("Сохраняем данные гостей...")
    result = await save_guests_to_db(sample_data, config)
    logger.info(f"Результат сохранения: {result}")
    
    # Отправляем webhook
    webhook_url = "https://development.bibosserp.com/webhooks/servio"
    logger.info("Отправляем webhook...")
    webhook_result = await send_pending_webhooks(webhook_url, config)
    logger.info(f"Результат отправки webhook: {webhook_result}")


if __name__ == "__main__":
    asyncio.run(main())