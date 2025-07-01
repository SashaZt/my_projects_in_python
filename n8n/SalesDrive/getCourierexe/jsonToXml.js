// Получаем объединенные данные заказа и города
const orderData = $input.first().json;

// Функция для экранирования XML символов
function escapeXml(unsafe) {
    if (!unsafe) return '';
    return unsafe.toString()
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

// Определяем тип оплаты
function getPayType(paymentMethod) {
    if (!paymentMethod) return 'CASH';
    const method = paymentMethod.toLowerCase();
    if (method.includes('без наложк')) return 'NO';
    if (method.includes('наложенный платеж') || method.includes('наложк')) return 'CASH';
    return 'CASH';
}

// Извлекаем данные с проверками
const orderId = orderData.orderId || 'TEST' + Date.now();
const totalProductsPrice = orderData.totalProductsPrice || 0;
const totalProducts = orderData.totalProducts || 0;
const totalMass = orderData.totalMass || 1;
const summaDostavki = orderData.summaDostavki || 0;
const paymentMethod = orderData.payment_method || 'CASH';
const products = orderData.products || [];

const payType = getPayType(paymentMethod);
const cashPrice = payType === 'NO' ? 0 : totalProductsPrice;

// Формируем XML согласно документации
const xmlBody = `<?xml version="1.0" encoding="UTF-8"?><neworder newfolder="YES"><auth extra="245" login="test" pass="test123"></auth><order orderno="${escapeXml(orderId)}"><barcode>${escapeXml(orderId)}</barcode><sender><company>INTER STORE</company><person>Inter Store</person><phone>+998700154377</phone><town country="UZ">Зангиата</town><address>Эмира Тимура, 2А</address></sender><receiver><person>${escapeXml(orderData.contactName || 'Клиент')}</person><phone>${escapeXml(orderData.contactPhone || '')}</phone><town regioncode="${orderData.region_code || ''}" country="UZ">${escapeXml(orderData.city_name || orderData.receiver_town || '')}</town><address>${escapeXml(orderData.receiver_address || 'Адрес не указан')}</address></receiver><price>${cashPrice}</price><inshprice>${totalProductsPrice}</inshprice><paytype>${payType}</paytype><weight>${totalMass}</weight><quantity>${totalProducts}</quantity><service>3</service><type>2</type><items>`;

// Добавляем товары
let itemsXml = '';
if (products && Array.isArray(products) && products.length > 0) {
    products.forEach((product, index) => {
        // Добавляем article с значением из sku
        let itemAttributes = `extcode="${escapeXml(product.sku || product.productId || index + 1)}" quantity="${product.amount || 1}" mass="${product.mass || 0.1}" retprice="${product.price || 0}" `;

        // Добавляем governmentCode если есть ASIL BELGI
        if (product.asilBelgi) {
            itemAttributes += ` governmentCode="${escapeXml(product.asilBelgi)}"`;
        }

        // Добавляем extraTags если есть ИКПУ или packageCode
        if (product.extraTags && product.extraTags !== '{}') {
            itemAttributes += ` extraTags="${escapeXml(product.extraTags)}"`;
        }

        itemsXml += `<item ${itemAttributes}>${escapeXml(product.name || 'Товар')}</item>`;
    });
}
// Добавляем позицию доставки как отдельный товар (только если стоимость доставки больше 0)
if (summaDostavki > 0) {
    itemsXml += `<item extcode="Доставка" quantity="1" mass="0" retprice="${summaDostavki}">Доставка</item>`;
}
const finalXml = xmlBody + itemsXml + `</items></order></neworder>`;

return [{
    json: {
        xmlRequest: finalXml
    }
}];