// XML запрос для получения списка городов
const xmlRequest = `<?xml version="1.0" encoding="UTF-8"?>
<townlist>
<auth extra="245" />
<limit>
<limitfrom>0</limitfrom>
<limitcount>50000</limitcount>
<countall>YES</countall>
</limit>
<conditions>
<country>UZ</country>
<namecontains></namecontains>
</conditions>
</townlist>`;

try {
    // Отправляем HTTP запрос
    const response = await helpers.httpRequest({
        method: 'POST',
        url: 'https://home.courierexe.ru/api/',
        headers: {
            'Content-Type': 'application/xml; charset=utf-8'
        },
        body: xmlRequest
    });

    // В n8n данные приходят напрямую в response, а не в response.body
    const xmlData = response;

    return [{
        json: {
            success: true,
            statusCode: 200,
            xmlResponse: xmlData,
            xmlSent: xmlRequest,
            message: 'Список городов получен',
            responseLength: xmlData ? xmlData.length : 0,
            responseType: typeof xmlData,
            responsePreview: xmlData ? xmlData.substring(0, 500) : 'no data'
        }
    }];

} catch (error) {
    return [{
        json: {
            success: false,
            error: error.message,
            details: error,
            xmlSent: xmlRequest
        }
    }];
}