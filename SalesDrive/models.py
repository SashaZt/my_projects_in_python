from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union


@dataclass
class DeliveryData:
    """Модель данных о доставке заказа."""

    order_id: int
    senderId: Optional[int] = None
    backDelivery: Optional[int] = None
    cityName: Optional[str] = None
    provider: Optional[str] = None
    payForDelivery: Optional[str] = None
    type: Optional[str] = None
    trackingNumber: Optional[str] = None
    statusCode: Optional[int] = None
    deliveryDateAndTime: Optional[str] = None
    idEntity: Optional[int] = None
    branchNumber: Optional[int] = None
    address: Optional[str] = None


@dataclass
class Contact:
    """Модель данных о контакте."""

    id: int
    order_id: int
    formId: Optional[int] = None
    version: Optional[int] = None
    active: Optional[int] = None
    con_uGC: Optional[str] = None
    con_bloger: Optional[str] = None
    lName: Optional[str] = None
    fName: Optional[str] = None
    mName: Optional[str] = None
    telegram: Optional[str] = None
    instagramNick: Optional[str] = None
    counterpartyId: Optional[int] = None
    comment: Optional[str] = None
    userId: Optional[int] = None
    createTime: Optional[str] = None
    leadsCount: Optional[int] = None
    leadsSalesCount: Optional[int] = None
    leadsSalesAmount: Optional[float] = None
    company: Optional[str] = None
    con_povnaOplata: Optional[str] = None
    phone: List[str] = field(default_factory=list)
    email: List[str] = field(default_factory=list)


@dataclass
class Product:
    """Модель данных о продукте в заказе."""

    order_id: int
    amount: Optional[int] = None
    percentCommission: Optional[float] = None
    preSale: Optional[int] = None
    productId: Optional[int] = None
    price: Optional[float] = None
    stockId: Optional[int] = None
    costPrice: Optional[float] = None
    discount: Optional[float] = None
    description: Optional[str] = None
    commission: Optional[float] = None
    percentDiscount: Optional[float] = None
    parameter: Optional[str] = None
    text: Optional[str] = None
    barcode: Optional[str] = None
    documentName: Optional[str] = None
    manufacturer: Optional[str] = None
    sku: Optional[str] = None
    uktzed: Optional[str] = None


@dataclass
class Order:
    """Модель данных о заказе."""

    id: int
    formId: Optional[int] = None
    version: Optional[int] = None
    organizationId: Optional[int] = None
    shipping_method: Optional[str] = None
    payment_method: Optional[str] = None
    shipping_address: Optional[str] = None
    comment: Optional[str] = None
    timeEntryOrder: Optional[str] = None
    holderTime: Optional[str] = None
    document_ord_check: Optional[str] = None
    discountAmount: Optional[float] = None
    orderTime: Optional[str] = None
    updateAt: Optional[str] = None
    statusId: Optional[str] = None
    paymentDate: Optional[str] = None
    rejectionReason: Optional[str] = None
    userId: Optional[int] = None
    paymentAmount: Optional[float] = None
    commissionAmount: Optional[float] = None
    costPriceAmount: Optional[float] = None
    shipping_costs: Optional[float] = None
    expensesAmount: Optional[float] = None
    profitAmount: Optional[float] = None
    typeId: Optional[str] = None
    payedAmount: Optional[float] = None
    restPay: Optional[float] = None
    call: Optional[str] = None
    sajt: Optional[int] = None
    externalId: Optional[str] = None
    utmPage: Optional[str] = None
    utmMedium: Optional[str] = None
    campaignId: Optional[int] = None
    utmSourceFull: Optional[str] = None
    utmSource: Optional[str] = None
    utmCampaign: Optional[str] = None
    utmContent: Optional[str] = None
    utmTerm: Optional[str] = None
    uploaded_to_sheets: bool = False
    last_update_exported: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    orderTimeLook: Optional[str] = None
    delivery_data: List[DeliveryData] = field(default_factory=list)
    primary_contact: Optional[Contact] = None
    contacts: List[Contact] = field(default_factory=list)
    products: List[Product] = field(default_factory=list)
    tip_prodazu: List[str] = field(default_factory=list)
    dzerelo_komentar: List[str] = field(default_factory=list)


@dataclass
class SaleAnalytic:
    """Модель данных аналитики продаж."""

    id: Optional[int] = None
    order_id: int = 0
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    quantity: int = 0
    price: float = 0
    discount: float = 0
    percent_discount: float = 0
    price_with_discount: float = 0
    total_amount: float = 0
    sale_date: Optional[str] = None
    day: Optional[int] = None
    month: Optional[int] = None
    quarter: Optional[int] = None
    year: Optional[int] = None
    month_year: Optional[str] = None


@dataclass
class Metadata:
    """Модель для метаданных, получаемых от SalesDrive API."""

    tipProdazu1: Dict[Union[int, str], str] = field(default_factory=dict)
    typeId: Dict[Union[int, str], str] = field(default_factory=dict)
    statusId: Dict[Union[int, str], str] = field(default_factory=dict)
    shipping_method: Dict[Union[int, str], str] = field(default_factory=dict)
    payment_method: Dict[Union[int, str], str] = field(default_factory=dict)


@dataclass
class Config:
    """Модель конфигурации приложения."""

    database: Dict[str, str]
    google_sheets: Dict[str, str]
    salesdrive: Dict[str, str]
