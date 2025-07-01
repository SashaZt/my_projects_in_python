// Получаем XML из входных данных
const inputData = $input.first().json;
const xmlData = $json.xmlRequest;

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

    // Извлекаем XML ответ
    let xmlResponse = null;
    if (typeof response === 'string') {
        xmlResponse = response;
    } else if (response && response.body) {
        xmlResponse = response.body;
    } else if (response && response.data) {
        xmlResponse = response.data;
    }

    // Парсим XML ответ
    let parsedResult = {
        success: false,
        orderno: null,
        barcode: null,
        error: null,
        errormsg: null,
        orderprice: null
    };

    if (xmlResponse && typeof xmlResponse === 'string') {
        // Ищем элемент createorder
        const createOrderMatch = xmlResponse.match(/<createorder[^>]*>/);
        if (createOrderMatch) {
            const createOrderTag = createOrderMatch[0];

            // Извлекаем атрибуты
            const ordernoMatch = createOrderTag.match(/orderno="([^"]*)"/);
            const barcodeMatch = createOrderTag.match(/barcode="([^"]*)"/);
            const errorMatch = createOrderTag.match(/error="([^"]*)"/);
            const errormsgMatch = createOrderTag.match(/errormsg="([^"]*)"/);
            const orderpriceMatch = createOrderTag.match(/orderprice="([^"]*)"/);

            parsedResult.orderno = ordernoMatch ? ordernoMatch[1] : null;
            parsedResult.barcode = barcodeMatch ? barcodeMatch[1] : null;
            parsedResult.error = errorMatch ? errorMatch[1] : null;
            parsedResult.errormsg = errormsgMatch ? errormsgMatch[1] : null;
            parsedResult.orderprice = orderpriceMatch ? orderpriceMatch[1] : null;
            parsedResult.success = parsedResult.error === '0';
        } else {
            // Проверяем на ошибки
            if (xmlResponse.includes('authorization error')) {
                parsedResult.error = '1';
                parsedResult.errormsg = 'Authorization error';
            } else if (xmlResponse.includes('expected')) {
                parsedResult.error = 'SYNTAX_ERROR';
                parsedResult.errormsg = 'XML syntax error';
            }
        }
    }

    // Возвращаем результат
    return [{
        json: {
            success: parsedResult.success,
            statusCode: 200,
            rawResponse: xmlResponse,
            orderId: inputData.orderId,
            ttnOrderno: parsedResult.orderno,
            ttnBarcode: parsedResult.barcode,
            ttnError: parsedResult.error,
            ttnErrorMsg: parsedResult.errormsg,
            ttnOrderPrice: parsedResult.orderprice,
            responseLength: xmlResponse ? xmlResponse.length : 0,
            timestamp: new Date().toISOString()
        }
    }];

} catch (error) {
    return [{
        json: {
            success: false,
            error: error.message,
            orderId: inputData.orderId,
            errorType: 'HTTP_REQUEST_ERROR',
            timestamp: new Date().toISOString()
        }
    }];
}