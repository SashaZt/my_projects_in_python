// Получаем данные из двух источников
// $('GetCityCode') - данные о городе
// $('CodeDelivery') - данные заказа

const cityData = $('GetCityCode').first().json;
const orderData = $('CodeDelivery').first().json;

// Объединяем данные
const mergedData = {
    // Данные заказа
    ...orderData,

    // Данные города
    city_code: cityData.city_code,
    city_name: cityData.city_name,
    region_code: cityData.region_code,
    region_name: cityData.region_name
};

console.log('Merged data:', {
    orderId: mergedData.orderId,
    city_name: mergedData.city_name,
    region_code: mergedData.region_code,
    totalProducts: mergedData.totalProducts,
    productsCount: mergedData.products ? mergedData.products.length : 0
});

return [{
    json: mergedData
}];