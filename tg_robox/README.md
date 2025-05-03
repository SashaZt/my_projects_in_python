./start.sh update-parser threads=50 category=260617
./start.sh update-parser price=200
./start.sh update-parser car_parts=false
./start.sh update-parser category=260617 car_parts=true threads=40 price=150
category=260617 - Указываем категорию
car_parts=true - Указываем по маркам или без марок 
threads=40 -Указываем количество потоков
price=150 -Указываем цену минимальную

Создание бекапа
./backup.sh

Востановление из бекапа
./restore.sh backup_2025_04_22_15_15.backup

Если необходимо сделать изменение в бд
docker exec -i postgres psql -U auto_parts_database_user -d auto_parts_database < migration.sql