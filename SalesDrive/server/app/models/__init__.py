#app/models/__init__.py
from app.models.enums import (
    OrderStatus, OrderType, Organization, ShippingMethod, PaymentMethod,
    Campaign, Manager, TipProdajuType, ClientSourceType, Stock
)

# Сначала импортируем модели контактов, так как они независимы
from app.models.contacts import (
    Contact, ContactPhone, ContactEmail, OrderContact
)

# Затем импортируем модели заказов, которые могут зависеть от моделей контактов
from app.models.orders import (
    Order, DeliveryData, NovaPoshtaData, OrderCheck
)

# И наконец, модели товаров
from app.models.products import (
    Product, ProductStockBalance, ProductComplect, OrderProduct
)

# Экспортируем все модели
__all__ = [
    # Справочники
    "OrderStatus", "OrderType", "Organization", "ShippingMethod", "PaymentMethod",
    "Campaign", "Manager", "TipProdajuType", "ClientSourceType", "Stock",
    
    # Контакты
    "Contact", "ContactPhone", "ContactEmail", "OrderContact",
    
    # Заказы
    "Order", "DeliveryData", "NovaPoshtaData", "OrderCheck",
    
    # Товары
    "Product", "ProductStockBalance", "ProductComplect", "OrderProduct",
]