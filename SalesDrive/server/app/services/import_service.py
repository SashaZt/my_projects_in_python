# app/services/import_service.py
import logging
import json
from typing import Any, Dict, List, Optional, Union
from sqlalchemy import select, insert, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Contact, Order, OrderCheck, OrderContact, DeliveryData, NovaPoshtaData,
    Product, ProductStockBalance, ProductComplect, OrderProduct,
    OrderStatus, OrderType, Organization, ShippingMethod, PaymentMethod,
    Campaign, Manager, TipProdajuType, ClientSourceType, Stock
)
from app.schemas.json_schema import OrderJson, FieldOption, JsonData

logger = logging.getLogger(__name__)

class ImportService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._current_json_data = None

    async def import_from_json(self, json_data_str: str) -> Dict[str, Any]:
        try:
            json_data = json.loads(json_data_str)
            self._current_json_data = JsonData.model_validate(json_data)
            
            await self._import_enums(self._current_json_data.meta.fields)
            
            orders_imported = 0
            for order_data in self._current_json_data.data:
                await self._import_order(order_data)
                orders_imported += 1
            
            return {
                "success": True,
                "orders_imported": orders_imported,
                "errors": []
            }
        except Exception as e:
            logger.exception(f"Error importing data: {str(e)}")
            return {
                "success": False,
                "orders_imported": 0,
                "errors": [str(e)]
            }

    async def _import_enums(self, fields: Dict[str, Any]) -> None:
        """
        Импортирует перечисления из meta.fields в соответствующие таблицы.
        
        Args:
            fields: Словарь с данными перечислений из JSON (meta.fields).
        """
        try:
            # Маппинг полей JSON на модели базы данных
            enum_mapping = {
                "statusId": OrderStatus,
                "typeId": OrderType,
                "userId": Manager,
                "campaignId": Campaign,
                "tipProdaju1": TipProdajuType,  # Предполагается, что это тип продаж
                "dzereloKomentarVidKlienta": ClientSourceType,
                "sajt": Stock,  # Предполагается, что это склад или сайт
            }

            for field_name, field_data in fields.items():
                model = enum_mapping.get(field_name)
                if not model or not hasattr(field_data, "options") or not field_data["options"]:
                    continue  # Пропускаем, если поле не связано с перечислением или нет опций
                
                for option in field_data["options"]:
                    # Проверяем, существует ли запись
                    stmt = select(model).where(model.id == option["value"])
                    result = await self.session.execute(stmt)
                    existing_enum = result.scalar_one_or_none()

                    values = {
                        "text": option["text"],
                        "active": option.get("active", 1),  # По умолчанию активен
                    }
                    # Добавляем дополнительные поля, если они есть
                    if "type" in option:
                        values["type"] = option["type"]
                    if "sort" in option:
                        values["sort"] = option["sort"]

                    if existing_enum:
                        # Обновляем существующую запись
                        stmt = (
                            update(model)
                            .where(model.id == option["value"])
                            .values(**values)
                        )
                        await self.session.execute(stmt)
                        logger.debug(f"Updated {model.__name__} with id {option['value']}")
                    else:
                        # Вставляем новую запись
                        enum_instance = model(
                            id=option["value"],
                            **values
                        )
                        self.session.add(enum_instance)
                        logger.debug(f"Inserted new {model.__name__} with id {option['value']}")

            # Дополнительно обработаем shipping_method и payment_method, если их опции нужно извлечь из данных
            # Это требует отдельной логики, если опции не указаны в meta.fields

        except Exception as e:
            logger.error(f"Error importing enums: {str(e)}")
            raise

    async def _import_order(self, order_data: OrderJson):
        # Импорт первичного контакта
        primary_contact_data = order_data.primaryContact
        stmt = select(Contact).where(Contact.id == primary_contact_data.id)
        result = await self.session.execute(stmt)
        existing_contact = result.scalar_one_or_none()

        if existing_contact:
            stmt = (
                update(Contact)
                .where(Contact.id == primary_contact_data.id)
                .values(
                    form_id=primary_contact_data.formId,
                    version=primary_contact_data.version,
                    active=primary_contact_data.active,
                    con_ugc=primary_contact_data.con_uGC,
                    con_bloger=primary_contact_data.con_bloger,
                    last_name=primary_contact_data.lName,
                    first_name=primary_contact_data.fName,
                    middle_name=primary_contact_data.mName,
                    company=primary_contact_data.company,
                    con_povnaoplata=primary_contact_data.con_povnaOplata,
                    counterparty_id=primary_contact_data.counterpartyId,
                    comment=primary_contact_data.comment,
                    user_id=primary_contact_data.userId,
                    create_time=primary_contact_data.createTime,
                    leads_count=primary_contact_data.leadsCount,
                    leads_sales_count=primary_contact_data.leadsSalesCount,
                    leads_sales_amount=primary_contact_data.leadsSalesAmount,
                )
            )
            await self.session.execute(stmt)
            primary_contact = existing_contact
        else:
            primary_contact = Contact(
                id=primary_contact_data.id,
                form_id=primary_contact_data.formId,
                version=primary_contact_data.version,
                active=primary_contact_data.active,
                con_ugc=primary_contact_data.con_uGC,
                con_bloger=primary_contact_data.con_bloger,
                last_name=primary_contact_data.lName,
                first_name=primary_contact_data.fName,
                middle_name=primary_contact_data.mName,
                company=primary_contact_data.company,
                con_povnaoplata=primary_contact_data.con_povnaOplata,
                counterparty_id=primary_contact_data.counterpartyId,
                comment=primary_contact_data.comment,
                user_id=primary_contact_data.userId,
                create_time=primary_contact_data.createTime,
                leads_count=primary_contact_data.leadsCount,
                leads_sales_count=primary_contact_data.leadsSalesCount,
                leads_sales_amount=primary_contact_data.leadsSalesAmount,
            )
            self.session.add(primary_contact)

        # Создание или обновление заказа
        stmt = select(Order).where(Order.id == order_data.id)
        result = await self.session.execute(stmt)
        order = result.scalar_one_or_none()

        if order:
            stmt = (
                update(Order)
                .where(Order.id == order_data.id)
                .values(
                    form_id=order_data.formId,
                    version=order_data.version,
                    primary_contact_id=primary_contact.id,
                    organization_id=order_data.organizationId,
                    shipping_method=order_data.shipping_method,
                    payment_method=order_data.payment_method,
                    shipping_address=order_data.shipping_address,
                    comment=order_data.comment,
                    time_entry_order=order_data.timeEntryOrder,
                    holder_time=order_data.holderTime,
                    order_time=order_data.orderTime,
                    update_at=order_data.updateAt,
                    status_id=order_data.statusId,
                    payment_date=order_data.paymentDate,
                    rejection_reason=order_data.rejectionReason,
                    user_id=order_data.userId,
                    payment_amount=order_data.paymentAmount,
                    commission_amount=order_data.commissionAmount,
                    cost_price_amount=order_data.costPriceAmount,
                    shipping_costs=order_data.shipping_costs,
                    expenses_amount=order_data.expensesAmount,
                    profit_amount=order_data.profitAmount,
                    type_id=order_data.typeId,
                    payed_amount=order_data.payedAmount,
                    rest_pay=order_data.restPay,
                    call=order_data.call,
                    sajt=order_data.sajt,
                    external_id=order_data.externalId,
                    utm_page=order_data.utmPage,
                    utm_medium=order_data.utmMedium,
                    campaign_id=order_data.campaignId,
                    utm_source_full=order_data.utmSourceFull,
                    utm_source=order_data.utmSource,
                    utm_campaign=order_data.utmCampaign,
                    utm_content=order_data.utmContent,
                    utm_term=order_data.utmTerm,
                )
            )
            await self.session.execute(stmt)
        else:
            order = Order(
                id=order_data.id,
                form_id=order_data.formId,
                version=order_data.version,
                primary_contact_id=primary_contact.id,
                organization_id=order_data.organizationId,
                shipping_method=order_data.shipping_method,
                payment_method=order_data.payment_method,
                shipping_address=order_data.shipping_address,
                comment=order_data.comment,
                time_entry_order=order_data.timeEntryOrder,
                holder_time=order_data.holderTime,
                order_time=order_data.orderTime,
                update_at=order_data.updateAt,
                status_id=order_data.statusId,
                payment_date=order_data.paymentDate,
                rejection_reason=order_data.rejectionReason,
                user_id=order_data.userId,
                payment_amount=order_data.paymentAmount,
                commission_amount=order_data.commissionAmount,
                cost_price_amount=order_data.costPriceAmount,
                shipping_costs=order_data.shipping_costs,
                expenses_amount=order_data.expensesAmount,
                profit_amount=order_data.profitAmount,
                type_id=order_data.typeId,
                payed_amount=order_data.payedAmount,
                rest_pay=order_data.restPay,
                call=order_data.call,
                sajt=order_data.sajt,
                external_id=order_data.externalId,
                utm_page=order_data.utmPage,
                utm_medium=order_data.utmMedium,
                campaign_id=order_data.campaignId,
                utm_source_full=order_data.utmSourceFull,
                utm_source=order_data.utmSource,
                utm_campaign=order_data.utmCampaign,
                utm_content=order_data.utmContent,
                utm_term=order_data.utmTerm,
            )
            self.session.add(order)

        # Импорт связанных данных
        await self._import_contacts(order_data.contacts, order)
        await self._import_delivery_data(order_data.ord_delivery_data, order)
        await self._import_order_checks(order_data.document_ord_check, order)
        await self._import_products(order_data.products, order)
        await self._import_sales_types(order_data.tipProdaju1, order)
        await self._import_client_sources(order_data.dzereloKomentarVidKlienta, order)

        await self.session.commit()  # Фиксируем изменения после импорта

    async def _import_order_checks(self, checks_data: Optional[Union[Dict[str, Any], int]], order: Order):
        if checks_data is None or isinstance(checks_data, int):
            # Если checks_data отсутствует или это int, пропускаем импорт чеков
            logger.debug(f"No valid checks data for order {order.id}, skipping checks import")
            return
        
        if "items" not in checks_data:
            logger.warning(f"Checks data for order {order.id} does not contain 'items', skipping")
            return

        # Логика для обработки словаря checks_data
        stmt = insert(OrderCheck).values(
            order_id=order.id,
            fiscal_code=checks_data.get("fiscalCode"),
            external_id=checks_data.get("id"),
            fiscalization_status=checks_data.get("fiscalizationStatus"),
            receipt_id=checks_data.get("receiptId")
        ).on_conflict_do_update(
            index_elements=["order_id"],
            set_={
                "fiscal_code": checks_data.get("fiscalCode"),
                "external_id": checks_data.get("id"),
                "fiscalization_status": checks_data.get("fiscalizationStatus"),
                "receipt_id": checks_data.get("receiptId")
            }
        )
        await self.session.execute(stmt)
        logger.info(f"Imported check for order {order.id}")
    
    async def _import_contact(self, contact_data, order, is_primary=False) -> None:
        """
        Импортирует данные контакта.
        
        Args:
            contact_data: Данные контакта из JSON.
            order: Объект заказа.
            is_primary: Флаг, указывающий, что это первичный контакт.
        """
        try:
            # Получаем имя менеджера
            manager_name = await self._get_enum_text(Manager, contact_data.userId)
            
            # Проверяем, существует ли контакт
            stmt = select(Contact).where(Contact.id == contact_data.id)
            result = await self.session.execute(stmt)
            contact = result.scalar_one_or_none()
            
            if contact:
                # Обновляем существующий контакт
                contact.form_id = contact_data.formId
                contact.version = contact_data.version
                contact.active = contact_data.active
                contact.con_ugc = contact_data.con_uGC
                contact.con_bloger = contact_data.con_bloger
                contact.last_name = contact_data.lName
                contact.first_name = contact_data.fName
                contact.middle_name = contact_data.mName
                contact.company = contact_data.company
                contact.con_povnaoplata = contact_data.con_povnaOplata
                contact.counterparty_id = contact_data.counterpartyId
                contact.comment = contact_data.comment
                contact.user_id = contact_data.userId
                contact.user_name = manager_name
                contact.create_time = contact_data.createTime
                contact.leads_count = contact_data.leadsCount
                contact.leads_sales_count = contact_data.leadsSalesCount
                contact.leads_sales_amount = contact_data.leadsSalesAmount
            else:
                # Создаем новый контакт
                contact = Contact(
                    id=contact_data.id,
                    form_id=contact_data.formId,
                    version=contact_data.version,
                    active=contact_data.active,
                    con_ugc=contact_data.con_uGC,
                    con_bloger=contact_data.con_bloger,
                    last_name=contact_data.lName,
                    first_name=contact_data.fName,
                    middle_name=contact_data.mName,
                    company=contact_data.company,
                    con_povnaoplata=contact_data.con_povnaOplata,
                    counterparty_id=contact_data.counterpartyId,
                    comment=contact_data.comment,
                    user_id=contact_data.userId,
                    user_name=manager_name,
                    create_time=contact_data.createTime,
                    leads_count=contact_data.leadsCount,
                    leads_sales_count=contact_data.leadsSalesCount,
                    leads_sales_amount=contact_data.leadsSalesAmount
                )
                self.session.add(contact)
            
            # Обрабатываем телефоны контакта
            if contact_data.phone:
                # Сначала удаляем все существующие телефоны
                stmt = select(ContactPhone).where(ContactPhone.contact_id == contact.id)
                result = await self.session.execute(stmt)
                phones = result.scalars().all()
                for phone in phones:
                    await self.session.delete(phone)
                
                # Добавляем новые телефоны
                for phone in contact_data.phone:
                    phone_record = ContactPhone(contact_id=contact.id, phone=phone)
                    self.session.add(phone_record)
            
            # Обрабатываем email контакта
            if contact_data.email:
                # Сначала удаляем все существующие email
                stmt = select(ContactEmail).where(ContactEmail.contact_id == contact.id)
                result = await self.session.execute(stmt)
                emails = result.scalars().all()
                for email in emails:
                    await self.session.delete(email)
                
                # Добавляем новые email
                for email in contact_data.email:
                    email_record = ContactEmail(contact_id=contact.id, email=email)
                    self.session.add(email_record)
            
            # Связываем контакт с заказом
            stmt = select(OrderContact).where(
                OrderContact.order_id == order.id,
                OrderContact.contact_id == contact.id
            )
            result = await self.session.execute(stmt)
            order_contact = result.scalar_one_or_none()
            
            if not order_contact:
                order_contact = OrderContact(
                    order_id=order.id,
                    contact_id=contact.id,
                    is_primary=is_primary
                )
                self.session.add(order_contact)
            else:
                order_contact.is_primary = is_primary
        
        except Exception as e:
            logger.error(f"Error importing contact {contact_data.id}: {str(e)}")
            raise
    
    async def _import_delivery_data(self, delivery_data_list, order) -> None:
        """
        Импортирует данные доставки.
        
        Args:
            delivery_data_list: Список данных доставки из JSON.
            order: Объект заказа.
        """
        try:
            # Сначала удаляем все существующие данные доставки
            stmt = select(DeliveryData).where(DeliveryData.order_id == order.id)
            result = await self.session.execute(stmt)
            delivery_data_records = result.scalars().all()
            for delivery_data_record in delivery_data_records:
                await self.session.delete(delivery_data_record)
            
            # Сохраняем текущие данные JSON в атрибут класса
            if not hasattr(self, '_current_json_data'):
                logger.error("No current JSON data available")
                return
            
            # Если есть данные доставки в order_data
            if delivery_data_list:
                for delivery_data_item in delivery_data_list:
                    delivery_data = DeliveryData(
                        order_id=order.id,
                        provider=delivery_data_item.provider,
                        sender_id=delivery_data_item.senderId,
                        type=delivery_data_item.type,
                        tracking_number=delivery_data_item.trackingNumber,
                        city_name=delivery_data_item.cityName,
                        status_code=delivery_data_item.statusCode,
                        delivery_date_and_time=delivery_data_item.deliveryDateAndTime,
                        back_delivery=bool(delivery_data_item.backDelivery),
                        pay_for_delivery=delivery_data_item.payForDelivery
                    )
                    self.session.add(delivery_data)
            
            # Если данных доставки нет, используем ord_novaposhta из meta
            elif "ord_novaposhta" in self._current_json_data.meta.fields:
                nova_poshta_field = self._current_json_data.meta.fields["ord_novaposhta"]
                for option in nova_poshta_field.options:
                    if isinstance(option, NovaPoshtaOption):  # Проверяем тип опции
                        delivery_data = DeliveryData(
                            order_id=order.id,
                            provider="novaposhta",
                            city_name=option.cityName,
                            tracking_number=f"branch-{option.branchNumber}" if option.branchNumber else None,
                            status_code="pending",  # Установите нужный статус
                            pay_for_delivery=order.shipping_costs or 0
                        )
                        self.session.add(delivery_data)
        
        except Exception as e:
            logger.error(f"Error importing delivery data for order {order.id}: {str(e)}")
            raise
    
    async def _import_order_checks(self, checks_data: Optional[Union[Dict[str, Any], int]], order: Order):
        if checks_data is None or isinstance(checks_data, int):
            # Если checks_data отсутствует или это int, пропускаем импорт чеков
            logger.debug(f"No valid checks data for order {order.id}, skipping checks import")
            return
        
        if "items" not in checks_data:
            logger.warning(f"Checks data for order {order.id} does not contain 'items', skipping")
            return

        # Дальнейшая логика для обработки словаря checks_data
        stmt = insert(OrderCheck).values(
            order_id=order.id,
            fiscal_code=checks_data.get("fiscalCode"),
            external_id=checks_data.get("id"),
            fiscalization_status=checks_data.get("fiscalizationStatus"),
            receipt_id=checks_data.get("receiptId")
        ).on_conflict_do_update(
            index_elements=["order_id"],
            set_={
                "fiscal_code": checks_data.get("fiscalCode"),
                "external_id": checks_data.get("id"),
                "fiscalization_status": checks_data.get("fiscalizationStatus"),
                "receipt_id": checks_data.get("receiptId")
            }
        )
        await self.session.execute(stmt)
        logger.info(f"Imported check for order {order.id}")
    
    async def _import_products(self, products_data, order) -> None:
        """
        Импортирует данные товаров.
        
        Args:
            products_data: Данные товаров из JSON.
            order: Объект заказа.
        """
        # Импорт товаров будет реализован позже
        pass
    
    async def _import_sales_types(self, sales_types_data, order) -> None:
        """
        Импортирует типы продаж.
        
        Args:
            sales_types_data: Список типов продаж из JSON.
            order: Объект заказа.
        """
        # Импорт типов продаж будет реализован позже
        pass
    
    async def _import_client_sources(self, client_sources_data, order) -> None:
        """
        Импортирует источники клиентов.
        
        Args:
            client_sources_data: Список источников клиентов из JSON.
            order: Объект заказа.
        """
        # Импорт источников клиентов будет реализован позже
        pass