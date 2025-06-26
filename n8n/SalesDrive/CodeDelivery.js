// Получаем входные данные
const input = $input.first().json;

// Проверяем наличие body
const body = input.body || {};

// Функция для поиска текста по значению в options
function getTextFromOptions(fieldName, value, metaFields) {
    if (metaFields && metaFields[fieldName] && metaFields[fieldName].options) {
        const option = metaFields[fieldName].options.find(opt => opt.value === value);
        return option ? option.text : value;
    }
    return value;
}

// Проверяем наличие meta и fields
const metaFields = body.meta && body.meta.fields ? body.meta.fields : {};

// Проверяем наличие data
const data = body.data || {};

// Обрабатываем все товары
const products = data.products || [];
const processedProducts = products.map((product, index) => {
    // Формируем extraTags для ИКПУ и кода единицы измерения
    let extraTags = null;
    if (product.uktzed || product.packageCode) {
        const tagsData = {};
        if (product.ikpu) tagsData.ikpu = product.ikpu;
        if (product.packageCode) tagsData.packageCode = product.packageCode;
        extraTags = JSON.stringify(tagsData);
    }

    return {
        productId: product.productId || null,
        name: product.name || null,
        amount: product.amount || 0,
        price: product.price || 0,
        mass: product.mass || 0,
        uktzed: product.uktzed || null,
        sku: product.sku || null,
        totalPrice: (product.price || 0) * (product.amount || 0),

        // Новые фискальные поля
        ikpu: product.ikpu || null, // ИКПУ код
        packageCode: product.packageCode || null, // Код единицы измерения
        asilBelgi: product.asilBelgi || product.governmentCode || null, // Честный знак
        extraTags: extraTags, // JSON строка для ИКПУ и packageCode

        // Дополнительные поля если есть
        manufacturer: product.manufacturer || null,
        description: product.description || null,
        barcode: product.barcode || product.uktzed || null,
        categoryName: product.categoryName || null
    };
});

// Вычисляем суммарные данные по всем товарам
const totalAmount = products.reduce((sum, product) => sum + (product.amount || 0), 0);
const totalProductsPrice = products.reduce((sum, product) => sum + ((product.price || 0) * (product.amount || 0)), 0);
const totalMass = products.reduce((sum, product) => sum + ((product.mass || 0) * (product.amount || 0)), 0);

// Получаем сумму доставки из данных (если есть)
const summaDostavki = data.summaDostavki || 0;

// Вычисляем общую сумму заказа включая доставку
const totalPrice = totalProductsPrice + summaDostavki;

// Создаем строку с названиями всех товаров
const productNames = products.map(product => product.name).filter(name => name).join(', ');

// Создаем детальное описание товаров
const productDetails = products.map((product, index) =>
    `${index + 1}. ${product.name || 'Неизвестный товар'} (${product.amount || 0} шт., ${product.price || 0} грн./шт., вес: ${product.mass || 0} кг)`
).join('\n');

// Создаем основной объект результата
const output = {
    // Основная информация о заказе
    orderId: data.id || null,
    receiver_town: getTextFromOptions('naselennyjPunkt', data.naselennyjPunkt, metaFields),
    receiver_address: data.shipping_address || null,
    payment_method: getTextFromOptions('payment_method', data.payment_method, metaFields),
    comment: data.comment || null,

    // Статус заказа
    statusOrder: getTextFromOptions('statusId', data.statusId, metaFields),

    // Информация о контакте
    contactName: data.contacts && data.contacts[0] ? `${data.contacts[0].fName || ''} ${data.contacts[0].lName || ''}`.trim() : null,
    contactPhone: data.contacts && data.contacts[0] && data.contacts[0].phone ? data.contacts[0].phone[0] : null,

    // Агрегированная информация о товарах
    totalProducts: products.length,
    totalAmount: totalAmount,
    totalProductsPrice: totalProductsPrice, // Сумма только товаров
    summaDostavki: summaDostavki, // Сумма доставки
    totalPrice: totalPrice, // Общая сумма (товары + доставка)
    totalMass: totalMass,

    // Массив всех товаров (детальная информация)
    products: processedProducts,
};

// Возвращаем результат
return [{ json: output }];