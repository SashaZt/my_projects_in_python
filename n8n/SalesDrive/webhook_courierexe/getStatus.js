// Простое извлечение основных данных
const webhookData = $input.first().json;
const order = webhookData.body?.order || {};

// Извлекаем нужные поля
const orderNo = order.$?.orderno || '';
const currentStatus = order.status?._ || '';
const historyStatus = order.statushistory?.status?._ || '';

return [{
    json: {
        orderNo: orderNo,
        currentStatus: currentStatus,
        historyStatus: historyStatus,
    }
}];