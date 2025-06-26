// Получаем XML из входных данных
const inputData = $input.first().json;
const xmlData = inputData.xmlRequest;

try {
    // Отправляем HTTP запрос
    const response = await helpers.httpRequest({
        method: 'POST',
        url: 'https://home.courierexe.ru/api',
        headers: {
            'Content-Type': 'application/xml; charset=utf-8'
        },
        body: xmlData
    });

    return [{
        json: {
            success: true,
            statusCode: response.statusCode,
            data: response.body,
            orderId: inputData.orderId
        }
    }];

} catch (error) {
    return [{
        json: {
            success: false,
            error: error.message,
            orderId: inputData.orderId,
            details: error
        }
    }];
}