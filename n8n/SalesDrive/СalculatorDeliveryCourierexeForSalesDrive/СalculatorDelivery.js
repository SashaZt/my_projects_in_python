// Получаем входные данные
const input = $input.first().json;

// Извлекаем <price> с помощью regex
const xmlString = input.data;
const priceMatch = xmlString.match(/<price>(\d+)<\/price>/);
const price = priceMatch ? priceMatch[1] : null;

// Логирование для отладки
console.log('Extracted price:', price);

// Возвращаем результат
return [{ json: { deliveryPrice: price } }];