# app/schemas/json_schema.py
from pydantic import BaseModel, Field as PydanticField
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, date


# Общие типы для JSON
class JsonBase(BaseModel):
    """Базовый класс для всех JSON моделей."""
    class Config:
        populate_by_name = True
        extra = "ignore"  # Игнорировать лишние поля


# Модели для справочников
class EnumOption(JsonBase):
    """Модель для опций в справочниках."""
    value: int
    text: str
    active: bool = True


class StockEnumOption(EnumOption):
    """Модель для опций справочника складов."""
    default: bool = False


# Модель для опций поля ord_novaposhta
class NovaPoshtaOption(JsonBase):
    """Модель опции для поля ord_novaposhta."""
    orderId: Optional[int] = None
    idEntity: Optional[int] = None
    cityName: Optional[str] = None
    address: Optional[str] = None
    branchNumber: Optional[int] = None
    warehouseTypeId: Optional[int] = None
    manual: Optional[Union[bool, int, str]] = False
    text: Optional[str] = None
    value: Optional[Any] = None
    active: Optional[bool] = True


# Модели для контактов
class ContactPhone(JsonBase):
    """Модель для телефона контакта."""
    phone: str


class ContactEmail(JsonBase):
    """Модель для email контакта."""
    email: str


class ContactJson(JsonBase):
    """Модель контакта из JSON."""
    id: int
    formId: int
    version: int
    active: bool = True
    con_uGC: Optional[str] = None
    con_bloger: Optional[str] = None
    lName: str
    fName: str
    mName: Optional[str] = None
    company: Optional[str] = None
    con_povnaOplata: Optional[str] = None
    phone: List[str] = []
    email: List[str] = []
    telegram: Optional[str] = None
    instagramNick: Optional[str] = None
    counterpartyId: Optional[int] = None
    comment: Optional[str] = None
    userId: Optional[int] = None
    createTime: datetime
    leadsCount: int = 0
    leadsSalesCount: int = 0
    leadsSalesAmount: float = 0


# Модели для доставки
class DeliveryDataJson(JsonBase):
    """Модель данных доставки из JSON."""
    provider: str
    senderId: Optional[int] = None
    type: Optional[str] = None
    trackingNumber: Optional[str] = None
    cityName: Optional[str] = None
    statusCode: Optional[Union[str, int]] = None
    deliveryDateAndTime: Optional[datetime] = None
    backDelivery: Union[bool, int] = False
    payForDelivery: Optional[Union[float, str]] = None


class NovaPoshtaDataJson(JsonBase):
    """Модель данных Новой Почты из JSON."""
    orderId: int
    idEntity: int
    cityName: Optional[str] = None
    branchNumber: Optional[int] = None
    address: Optional[str] = None
    warehouseTypeId: Optional[int] = None
    backDeliverySum: Optional[float] = None
    manual: Union[bool, int, str] = False


# Модели для товаров
class ProductOptionJson(JsonBase):
    """Модель опции товара из JSON."""
    value: int
    parameter: str
    text: str
    nameTranslate: Optional[str] = None
    barcode: Optional[str] = None
    keywords: Optional[str] = None
    documentName: Optional[str] = None
    defaultPrice: float
    costPrice: float = 0
    active: bool = True
    mass: float = 0
    volume: float = 0
    length: float = 0
    width: float = 0
    height: float = 0
    restCount: int = 0
    currencyId: Optional[int] = None
    costPriceCurrencyId: Optional[int] = None
    manufacturer: Optional[str] = None
    sku: Optional[str] = None
    uktzed: Optional[str] = None
    discount: float = 0
    percentDiscount: float = 0
    discountPeriodFrom: Optional[date] = None
    discountPeriodTo: Optional[date] = None
    isComplect: int = 0
    complect: List[Dict[str, Any]] = []
    options: List[Dict[str, Any]] = []
    stockBalance: Dict[str, int] = {}
    group: Optional[str] = None
    priceTypes: List[Dict[str, Any]] = []


class ProductComplectJson(JsonBase):
    """Модель комплекта товара из JSON."""
    id: str
    formId: str
    complectId: int
    productId: int
    count: int


# Модели для чеков
class OrderCheckJson(JsonBase):
    """Модель чека из JSON."""
    fiscalCode: str
    id: str
    fiscalizationStatus: str
    receiptId: str


# Модели для заказа
class OrderJson(JsonBase):
    """Модель заказа из JSON."""
    id: int
    formId: int
    version: int
    ord_delivery_data: Optional[List[DeliveryDataJson]] = None
    primaryContact: ContactJson
    contacts: List[ContactJson] = []
    organizationId: Optional[int] = None
    products: Optional[List[Dict[str, Any]]] = None
    shipping_method: Optional[int] = None
    payment_method: Optional[int] = None
    shipping_address: Optional[str] = None
    comment: Optional[str] = None
    timeEntryOrder: Optional[str] = None
    holderTime: Optional[datetime] = None
    tipProdazu1: List[int] = []
    document_ord_check: Optional[Union[Dict[str, Any], int]] = None
    discountAmount: Optional[float] = None
    orderTime: datetime
    updateAt: datetime
    statusId: int
    paymentDate: Optional[date] = None
    rejectionReason: Optional[str] = None
    userId: Optional[int] = None
    paymentAmount: Optional[float] = None
    commissionAmount: Optional[float] = None
    costPriceAmount: Optional[float] = None
    shipping_costs: Optional[float] = None
    expensesAmount: float = 0
    profitAmount: float = 0
    typeId: int
    payedAmount: Optional[float] = None
    restPay: float = 0
    call: Optional[bool] = None
    sajt: Optional[Union[str, int]] = None
    externalId: Optional[str] = None
    utmPage: Optional[str] = None
    utmMedium: Optional[str] = None
    campaignId: Optional[int] = None
    utmSourceFull: Optional[str] = None
    utmSource: Optional[str] = None
    utmCampaign: Optional[str] = None
    utmContent: Optional[str] = None
    utmTerm: Optional[str] = None
    dzereloKomentarVidKlienta: List[int] = []


# Модели для мета-данных
class FieldOption(JsonBase):
    """Модель опции поля из мета-данных (общая версия)."""
    text: Optional[str] = None
    value: Optional[Any] = None
    active: Optional[bool] = True


class Field(JsonBase):
    """Модель поля из мета-данных."""
    type: str
    name: str
    label: str
    editable: Optional[int] = None  # Сделали необязательным
    sortable: Optional[bool] = None  # Сделали необязательным
    system: Optional[int] = None  # Сделали необязательным
    forAdminOnly: Optional[int] = None
    options: Optional[List[Union[NovaPoshtaOption, FieldOption]]] = None
    daysWarningDelivery: Optional[int] = None
    allowPrint: Optional[int] = None
    shippingCosts: Optional[int] = None
    printCopyModeA4: Optional[int] = None
    groupName: Optional[str] = None  # Добавили для primaryContact
    fields: Optional[Dict[str, "Field"]] = None  # Добавили для вложенных полей


# Указываем Pydantic, что Field может содержать вложенные Field
Field.model_rebuild()


class MetaData(JsonBase):
    """Модель мета-данных."""
    fields: Dict[str, Field]


# Полная модель JSON-данных
class JsonData(JsonBase):
    """Полная модель данных JSON."""
    data: List[OrderJson]
    meta: MetaData
    pagination: Optional[Dict[str, Any]] = None  # Добавили для поддержки pagination
    totals: Optional[Dict[str, Any]] = None  # Добавили для поддержки totals
    status: Optional[str] = None  # Добавили для поддержки status

    class Config:
        extra = "ignore"  # Игнорировать лишние поля