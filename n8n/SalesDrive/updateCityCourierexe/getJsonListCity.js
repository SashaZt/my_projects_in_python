// Получаем XML данные из предыдущего узла
const responseData = $input.first().json;
const xmlData = responseData.xmlResponse;

// Парсер XML для городов
function parseXmlCities(xmlString) {
    const cities = [];

    if (!xmlString || typeof xmlString !== 'string') {
        return cities;
    }

    try {
        // Ищем все блоки <town>...</town>
        const townRegex = /<town[^>]*>([\s\S]*?)<\/town>/g;
        let townMatch;

        while ((townMatch = townRegex.exec(xmlString)) !== null) {
            const townContent = townMatch[1];

            // Извлекаем код города (первый <code> в блоке town)
            const cityCodeMatch = townContent.match(/<code[^>]*>(\d+)<\/code>/);
            const cityCode = cityCodeMatch ? cityCodeMatch[1] : null;

            // Извлекаем название города (последний <name> вне блока <city>)
            const townWithoutCity = townContent.replace(/<city[^>]*>[\s\S]*?<\/city>/g, '');
            const cityNameMatch = townWithoutCity.match(/<name[^>]*>([^<]+)<\/name>/);
            const cityName = cityNameMatch ? cityNameMatch[1].trim() : null;

            // Извлекаем данные региона из блока <city>
            const cityBlockMatch = townContent.match(/<city[^>]*>([\s\S]*?)<\/city>/);
            let regionCode = null;
            let regionName = null;

            if (cityBlockMatch) {
                const cityBlockContent = cityBlockMatch[1];

                // Код региона (первый <code> в блоке <city>)
                const regionCodeMatch = cityBlockContent.match(/<code[^>]*>(\d+)<\/code>/);
                regionCode = regionCodeMatch ? regionCodeMatch[1] : null;

                // Название региона (<name> в блоке <city>)
                const regionNameMatch = cityBlockContent.match(/<name[^>]*>([^<]+)<\/name>/);
                regionName = regionNameMatch ? regionNameMatch[1].trim() : null;
            }

            if (cityCode && cityName) {
                cities.push({
                    city_code: parseInt(cityCode),
                    city_name: cityName,
                    region_code: regionCode ? parseInt(regionCode) : null,
                    region_name: regionName
                });
            }
        }
    } catch (error) {
        console.log('Error parsing XML:', error.message);
    }

    return cities;
}

// Парсим города
const cities = parseXmlCities(xmlData);

return [{
    json: {
        cities: cities
    }
}];