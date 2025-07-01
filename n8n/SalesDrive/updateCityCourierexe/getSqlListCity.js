// Получаем данные городов
const inputData = $input.first().json;
const cities = inputData.cities;

// Формируем SQL для вставки
const values = cities.map(city => {
    const regionCode = city.region_code ? city.region_code : 'NULL';
    const regionName = city.region_name ? `'${city.region_name.replace(/'/g, "''")}'` : 'NULL';

    return `(${city.city_code}, '${city.city_name.replace(/'/g, "''")}', ${regionCode}, ${regionName})`;
}).join(',\n');

const sql = `
DELETE FROM cities;
INSERT INTO cities (city_code, city_name, region_code, region_name) VALUES 
${values};
`;

return [{
    json: {
        sql: sql,
        citiesCount: cities.length
    }
}];