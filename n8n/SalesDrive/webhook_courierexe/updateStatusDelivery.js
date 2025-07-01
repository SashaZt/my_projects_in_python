try {
    const response = await helpers.httpRequest({
        method: 'POST',
        url: 'https://uni.salesdrive.me/api/order/update/',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'aUOkwSTeZTuqvDWNFhjSC7cOy7I1hx6O_u2D73SAgMuZ5iP_NvOjpqMekbKFCXrCkEZYR08tSqa_rSWDcmaSJOoeMW46uk-YJ0sG',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://uni.salesdrive.me',
            'Referer': 'https://uni.salesdrive.me'
        },
        body: JSON.stringify({
            "form": "mv4E0VUYAlH8FD4DqrFOl4jLMTdw3we9LtkpzY60JgLiVPbqFE00ZAUeX_fgZg4ZYnvZ",
            "id": $('getStatus').first().json.orderNo,
            "data": {
                "statusPosylki2": $input.first().json.status_id,
            }
        })
    });

    return {
        success: true,
        statusCode: response.statusCode,
        data: response.body
    };

} catch (error) {
    return {
        success: false,
        error: error.message,
        details: error
    };
}