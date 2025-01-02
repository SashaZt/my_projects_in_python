import json

import requests

# URL для вашего WordPress REST API
api_url = "https://allproperty.ai/wp-json/wp/v2/properties"

# Данные о недвижимости
# property_data = {
#     "title": "Single family home",  # Заголовок объявления о недвижимости
#     "content": "Ваш контент здесь...",  # Основное описание недвижимости (может быть HTML), здесь замените на реальное описание
#     "status": "publish",  # Статус публикации (publish - опубликован, draft - черновик и т.д.)
#     "type": "property",  # Тип поста, указывает, что это объект недвижимости
#     "property_type": [
#         60
#     ],  # Массив ID типов недвижимости (из таксономии property_type), 60 - это ID типа "Single Family Home"
#     "property_status": [
#         30
#     ],  # Массив ID статусов недвижимости (из таксономии property_status), 30 - это ID статуса "For Sale"
#     "property_feature": [
#         13,
#         17,
#         27,
#         32,
#         36,
#         37,
#         41,
#         51,
#         54,
#         57,
#         63,
#         64,
#         67,
#         69,
#         70,
#     ],  # Массив ID особенностей недвижимости, каждое число - это ID определенной особенности в таксономии property_feature
#     "property_label": [49],  # Массив ID меток (лейблов), 49 - это ID метки "Open House"
#     "property_country": [65],  # Массив ID стран, 65 - это ID страны "United States"
#     "property_state": [35],  # Массив ID штатов, 35 - это ID штата "Illinois"
#     "property_city": [24],  # Массив ID городов, 24 - это ID города "Chicago"
#     "property_area": [
#         14
#     ],  # Массив ID районов/округов, 14 - это ID района "Albany Park"
#     "class_list": [
#         "post-361",
#         "property",
#         "type-property",
#         "status-publish",
#         "has-post-thumbnail",
#         "hentry",
#         "property_type-single-family-home",
#         "property_status-for-sale",
#         "property_feature-air-conditioning",
#         "property_feature-barbeque",
#         "property_feature-dryer",
#         "property_feature-gym",
#         "property_feature-laundry",
#         "property_feature-lawn",
#         "property_feature-microwave",
#         "property_feature-outdoor-shower",
#         "property_feature-refrigerator",
#         "property_feature-sauna",
#         "property_feature-swimming-pool",
#         "property_feature-tv-cable",
#         "property_feature-washer",
#         "property_feature-wifi",
#         "property_feature-window-coverings",
#         "property_label-open-house",
#         "property_country-united-states",
#         "property_state-illinois",
#         "property_city-chicago",
#         "property_area-albany-park",
#     ],
#     "meta": {  # Метаданные для записи, специфичные для плагина Houzez
#         "fave_property_size": [
#             "1200",  # Размер недвижимости в квадратных футах
#             "1200",  # Вероятно, дублирование для каких-то внутренних нужд плагина или для истории изменений
#         ],
#         "fave_property_size_prefix": [
#             "Sq Ft",  # Единица измерения размера
#             "Sq Ft",  # Дублирование (возможно, для истории или проверки консистентности данных)
#         ],
#         "fave_property_bedrooms": [
#             "4",  # Количество спален
#             "4",  # Дублирование
#         ],
#         "fave_property_bathrooms": [
#             "2",  # Количество ванных комнат
#             "2",  # Дублирование
#         ],
#         "fave_property_garage": [
#             "1",  # Наличие гаража (1 - есть, 0 - нет)
#             "1",  # Дублирование
#         ],
#         "fave_property_garage_size": [
#             "200 SqFt",  # Размер гаража
#             "200 SqFt",  # Дублирование
#         ],
#         "fave_property_year": [
#             "2016",  # Год постройки или последнего ремонта
#             "2016",  # Дублирование
#         ],
#         "fave_property_id": [
#             "HZ33",  # Уникальный идентификатор недвижимости, заданный пользователем или системой
#             "HZ33",  # Дублирование
#         ],
#         "fave_property_price": [
#             "670000",  # Цена недвижимости
#             "670000",  # Дублирование
#         ],
#         "fave_property_price_postfix": [
#             "mo",  # Постфикс цены, указывает, что цена указана за месяц аренды
#             "mo",  # Дублирование
#         ],
#         "fave_property_map": [
#             "1",  # Включение карты на странице объекта (1 - вкл, 0 - выкл)
#             "1",  # Дублирование
#         ],
#         "fave_property_map_address": [
#             "3001 W Ainslie St, Chicago, IL 60625, USA",  # Адрес объекта
#             "3001 W Ainslie St, Chicago, IL 60625, USA",  # Дублирование
#         ],
#         "fave_property_location": [
#             "41.9703082,-87.70394090000002,14",  # Координаты и зум для карты (широта, долгота, уровень зума)
#             "41.9703082,-87.70394090000002,14",  # Дублирование
#         ],
#         "houzez_geolocation_lat": [
#             "41.9703082",  # Широта для геолокации
#             "41.9703082",  # Дублирование
#             "41.9703082",  # Дублирование (возможно, для истории изменений или резервного копирования)
#         ],
#         "houzez_geolocation_long": [
#             "-87.70394090000002",  # Долгота для геолокации
#             "-87.70394090000002",  # Дублирование
#             "-87.70394090000002",  # Дублирование
#         ],
#         "fave_property_country": [
#             "US",  # Код страны
#             "US",  # Дублирование
#         ],
#         "fave_agents": [
#             "156",  # ID агента или ID пользователя, связанного с объектом
#             "156",  # Дублирование
#         ],
#         "fave_additional_features_enable": [
#             "enable",  # Включение дополнительных функций или характеристик
#             "enable",  # Дублирование
#         ],
#         "fave_featured": [
#             "0",  # Флаг, указывающий, является ли объявление выделенным (0 - нет, 1 - да)
#             "0",  # Дублирование
#         ],
#         "houzez_featured_listing_date": [
#             ""  # Дата, когда объявление стало выделенным (пустая строка - не было выделено)
#         ],
#         "fave_property_address": [
#             "3001 W Ainslie St",  # Уличный адрес недвижимости
#             "3001 W Ainslie St",  # Дублирование
#         ],
#         "fave_property_zip": ["60625", "60625"],  # Почтовый индекс  # Дублирование
#         # "fave_video_url": [
#         #     "https://www.youtube.com/watch?v=-NInBEdSvp8",  # URL видеоролика на YouTube для данного объекта
#         #     "https://www.youtube.com/watch?v=-NInBEdSvp8",  # Дублирование
#         # ],
#         # "fave_payment_status": [
#         #     "not_paid",  # Статус оплаты за объявление (не оплачено)
#         #     "not_paid",  # Дублирование
#         # ],
#         "fave_property_map_street_view": [
#             "show",  # Показать или скрыть уличный вид на карте (show - показать)
#             "show",  # Дублирование
#         ],
#         # "_dp_original": [
#         #     "357",  # Вероятно, оригинальный ID или ссылка на что-то в системе, используется для внутренних целей плагина
#         #     "357",  # Дублирование
#         # ],
#         "fave_property_sec_price": [
#             "1300",  # Вторичная цена или цена за другую единицу измерения (возможно, за квадратный фут или месячная аренда)
#             "1300",  # Дублирование
#         ],
#         "houzez_total_property_views": [
#             "18144",  # Общее количество просмотров объявления
#             "18144",  # Дублирование
#         ],
#         "fave_multiunit_plans_enable": [
#             "disable",  # Включены ли планы для многоквартирных домов (disable - отключено)
#             "disable",  # Дублирование
#         ],
#         "featured_media": 17406,  # ID изображения
#         "_thumbnail_id": ["17406", "17406"],
#         # "fave_attachments": [
#         #     "99"  # ID вложения (может быть файлом или документом, связанным с объектом)
#         # ],
#         "rs_page_bg_color": [
#             ""  # Вероятно, поле для хранения цвета фона страницы, пустое значение указывает на отсутствие установленного цвета или использование значения по умолчанию
#         ],
#     },
#     "_links": {
#         "self": [
#             {
#                 "href": "https://allproperty.ai/wp-json/wp/v2/properties/400",
#                 "targetHints": {"allow": ["GET"]},
#             }
#         ],
#         "collection": [{"href": "https://allproperty.ai/wp-json/wp/v2/properties"}],
#         "about": [{"href": "https://allproperty.ai/wp-json/wp/v2/types/property"}],
#         "author": [
#             {"embeddable": True, "href": "https://allproperty.ai/wp-json/wp/v2/users/1"}
#         ],
#         "version-history": [
#             {
#                 "count": 0,
#                 "href": "https://allproperty.ai/wp-json/wp/v2/properties/400/revisions",
#             }
#         ],
#         "wp:featuredmedia": [
#             {
#                 "embeddable": True,
#                 "href": "https://allproperty.ai/wp-json/wp/v2/media/17406",
#             }
#         ],
#         "wp:attachment": [
#             {"href": "https://allproperty.ai/wp-json/wp/v2/media?parent=400"}
#         ],
#         "wp:term": [
#             {
#                 "taxonomy": "property_type",
#                 "embeddable": True,
#                 "href": "https://allproperty.ai/wp-json/wp/v2/property_type?post=400",
#             },
#             {
#                 "taxonomy": "property_status",
#                 "embeddable": True,
#                 "href": "https://allproperty.ai/wp-json/wp/v2/property_status?post=400",
#             },
#             {
#                 "taxonomy": "property_feature",
#                 "embeddable": True,
#                 "href": "https://allproperty.ai/wp-json/wp/v2/property_feature?post=400",
#             },
#             {
#                 "taxonomy": "property_label",
#                 "embeddable": True,
#                 "href": "https://allproperty.ai/wp-json/wp/v2/property_label?post=400",
#             },
#             {
#                 "taxonomy": "property_country",
#                 "embeddable": True,
#                 "href": "https://allproperty.ai/wp-json/wp/v2/property_country?post=400",
#             },
#             {
#                 "taxonomy": "property_state",
#                 "embeddable": True,
#                 "href": "https://allproperty.ai/wp-json/wp/v2/property_state?post=400",
#             },
#             {
#                 "taxonomy": "property_city",
#                 "embeddable": True,
#                 "href": "https://allproperty.ai/wp-json/wp/v2/property_city?post=400",
#             },
#             {
#                 "taxonomy": "property_area",
#                 "embeddable": True,
#                 "href": "https://allproperty.ai/wp-json/wp/v2/property_area?post=400",
#             },
#         ],
#         "curies": [
#             {"name": "wp", "href": "https://api.w.org/{rel}", "templated": True}
#         ],
#     },
# }
property_data = {
    # "id": 361,
    # "date": "2016-03-09T18:46:16",
    # "date_gmt": "2016-03-09T18:46:16",
    # "guid": {"rendered": "https://default.houzez.co/?post_type=property&amp;p=361"},
    # "modified": "2016-03-09T18:46:16",
    # "modified_gmt": "2016-03-09T18:46:16",
    # "slug": "luxury-family-home-4",
    "status": "publish",
    "type": "property",
    "title": "Flat / apartment for sale in calle de Tòquio",  # Заголовок в виде строки
    "content": (
        "<p>Lorem ipsum dolor sit amet, consectetuer adipiscing elit, sed diam nonummy nibh "
        "euismod tincidunt ut laoreet dolore magna aliquam erat volutpat. Ut wisi enim ad minim "
        "veniam, quis nostrud exerci tation ullamcorper suscipit lobortis nisl ut aliquip ex ea "
        "commodo consequat. Duis autem vel eum iriure dolor in hendrerit in vulputate velit esse "
        "molestie consequat, vel illum dolore eu feugiat nulla facilisis at vero eros et accumsan "
        "et iusto odio dignissim qui blandit praesent luptatum zzril delenit augue duis dolore te "
        "feugait nulla facilisi.</p>\n<p>Nam liber tempor cum soluta nobis eleifend option congue "
        "nihil imperdiet doming id quod mazim placerat facer possim assum. Typi non habent "
        "claritatem insitam; est usus legentis in iis qui facit eorum claritatem. Investigationes "
        "demonstraverunt lectores legere me lius quod ii legunt saepius. Claritas est etiam "
        "processus dynamicus, qui sequitur mutationem consuetudium lectorum. Mirum est notare quam "
        "littera gothica, quam nunc putamus parum claram, anteposuerit litterarum formas "
        "humanitatis per seacula quarta decima et quinta decima. Eodem modo typi, qui nunc nobis "
        "videntur parum clari, fiant sollemnes in futurum.</p>\n"
    ),  # Контент в виде строки
    "excerpt": (
        "<p>Lorem ipsum dolor sit amet, consectetuer adipiscing elit, sed diam nonummy nibh euismod "
        "tincidunt ut laoreet dolore magna aliquam erat volutpat. Ut wisi enim ad minim veniam, "
        "quis nostrud exerci tation ullamcorper suscipit lobortis nisl ut aliquip ex ea commodo "
        "consequat. Duis autem vel eum iriure dolor in hendrerit in vulputate velit esse molestie "
        "consequat, [&hellip;]</p>\n"
    ),  # Краткое описание в виде строки
    # "author": 1,
    # "featured_media": 16124,
    # "parent": 0,
    # "menu_order": 0,
    # "template": "",
    "property_type": [60],
    "property_status": [30],
    "property_feature": [13, 17, 27, 32, 36, 37, 41, 51, 54, 57, 63, 64, 67, 69, 70],
    "property_label": [49],
    "property_country": [65],
    "property_state": [35],
    "property_city": [24],
    "property_area": [14],
    "class_list": [
        "post-361",
        "property",
        "type-property",
        "status-publish",
        "has-post-thumbnail",
        "hentry",
        "property_type-single-family-home",
        "property_status-for-sale",
        "property_feature-air-conditioning",
        "property_feature-barbeque",
        "property_feature-dryer",
        "property_feature-gym",
        "property_feature-laundry",
        "property_feature-lawn",
        "property_feature-microwave",
        "property_feature-outdoor-shower",
        "property_feature-refrigerator",
        "property_feature-sauna",
        "property_feature-swimming-pool",
        "property_feature-tv-cable",
        "property_feature-washer",
        "property_feature-wifi",
        "property_feature-window-coverings",
        "property_label-open-house",
        "property_country-united-states",
        "property_state-illinois",
        "property_city-chicago",
        "property_area-albany-park",
    ],
    "property_meta": {
        "fave_currency_info": ["", "", ""],
        "_thumbnail_id": ["16124", "16124"],
        "slide_template": ["", ""],
        "fave_property_size": ["1200", "1200"],
        "fave_property_size_prefix": ["Sq Ft", "Sq Ft"],
        "fave_property_bedrooms": ["4", "4"],
        "fave_property_bathrooms": ["2", "2"],
        "fave_property_garage": ["1", "1"],
        "fave_property_garage_size": ["200 SqFt", "200 SqFt"],
        "fave_property_year": ["2016", "2016"],
        "fave_property_id": ["HZ33", "HZ33"],
        "fave_property_price": ["670000", "670000"],
        "fave_property_price_postfix": ["mo", "mo"],
        "fave_property_map": ["1", "1"],
        "fave_property_map_address": [
            "3001 W Ainslie St, Chicago, IL 60625, USA",
            "3001 W Ainslie St, Chicago, IL 60625, USA",
        ],
        "fave_property_location": [
            "41.9703082,-87.70394090000002,14",
            "41.9703082,-87.70394090000002,14",
        ],
        "houzez_geolocation_lat": ["41.9703082", "41.9703082", "41.9703082"],
        "houzez_geolocation_long": [
            "-87.70394090000002",
            "-87.70394090000002",
            "-87.70394090000002",
        ],
        "fave_property_country": ["US", "US"],
        "fave_agents": ["156", "156"],
        # "fave_additional_features_enable": ["enable", "enable"],
        # "additional_features": [
        #     'a:6:{i:0;a:2:{s:29:"fave_additional_feature_title";s:7:"Deposit";s:29:"fave_additional_feature_value";s:3:"20%";}i:1;a:2:{s:29:"fave_additional_feature_title";s:9:"Pool Size";s:29:"fave_additional_feature_value";s:8:"300 Sqft";}i:2;a:2:{s:29:"fave_additional_feature_title";s:17:"Last remodel year";s:29:"fave_additional_feature_value";s:4:"1987";}i:3;a:2:{s:29:"fave_additional_feature_title";s:9:"Amenities";s:29:"fave_additional_feature_value";s:9:"Clubhouse";}i:4;a:2:{s:29:"fave_additional_feature_title";s:17:"Additional Rooms:";s:29:"fave_additional_feature_value";s:10:"Guest Bath";}i:5;a:2:{s:29:"fave_additional_feature_title";s:9:"Equipment";s:29:"fave_additional_feature_value";s:11:"Grill - Gas";}}',
        #     'a:6:{i:0;a:2:{s:29:"fave_additional_feature_title";s:7:"Deposit";s:29:"fave_additional_feature_value";s:3:"20%";}i:1;a:2:{s:29:"fave_additional_feature_title";s:9:"Pool Size";s:29:"fave_additional_feature_value";s:8:"300 Sqft";}i:2;a:2:{s:29:"fave_additional_feature_title";s:17:"Last remodel year";s:29:"fave_additional_feature_value";s:4:"1987";}i:3;a:2:{s:29:"fave_additional_feature_title";s:9:"Amenities";s:29:"fave_additional_feature_value";s:9:"Clubhouse";}i:4;a:2:{s:29:"fave_additional_feature_title";s:17:"Additional Rooms:";s:29:"fave_additional_feature_value";s:10:"Guest Bath";}i:5;a:2:{s:29:"fave_additional_feature_title";s:9:"Equipment";s:29:"fave_additional_feature_value";s:11:"Grill - Gas";}}',
        # ],
        # "fave_floor_plans_enable": ["enable", "enable"],
        # "floor_plans": [
        #     'a:2:{i:0;a:7:{s:15:"fave_plan_title";s:11:"First Floor";s:15:"fave_plan_rooms";s:8:"670 Sqft";s:19:"fave_plan_bathrooms";s:8:"530 Sqft";s:15:"fave_plan_price";s:5:"1,650";s:14:"fave_plan_size";s:9:"1267 Sqft";s:15:"fave_plan_image";s:75:"https://sandbox.favethemes.com/houzez/wp-content/uploads/2016/01/plan-1.jpg";s:21:"fave_plan_description";s:290:"Plan description. Lorem ipsum dolor sit amet, consectetuer adipiscing elit, sed diam nonummy nibh euismod tincidunt ut laoreet dolore magna aliquam erat volutpat. Ut wisi enim ad minim veniam, quis nostrud exerci tation ullamcorper suscipit lobortis nisl ut aliquip ex ea commodo consequat.";}i:1;a:7:{s:15:"fave_plan_title";s:12:"Second Floor";s:15:"fave_plan_rooms";s:8:"543 Sqft";s:19:"fave_plan_bathrooms";s:8:"238 Sqft";s:15:"fave_plan_price";s:5:"1,600";s:14:"fave_plan_size";s:9:"1345 Sqft";s:15:"fave_plan_image";s:75:"https://sandbox.favethemes.com/houzez/wp-content/uploads/2016/01/plan-2.jpg";s:21:"fave_plan_description";s:290:"Plan description. Lorem ipsum dolor sit amet, consectetuer adipiscing elit, sed diam nonummy nibh euismod tincidunt ut laoreet dolore magna aliquam erat volutpat. Ut wisi enim ad minim veniam, quis nostrud exerci tation ullamcorper suscipit lobortis nisl ut aliquip ex ea commodo consequat.";}}',
        #     'a:2:{i:0;a:7:{s:15:"fave_plan_title";s:11:"First Floor";s:15:"fave_plan_rooms";s:8:"670 Sqft";s:19:"fave_plan_bathrooms";s:8:"530 Sqft";s:15:"fave_plan_price";s:5:"1,650";s:14:"fave_plan_size";s:9:"1267 Sqft";s:15:"fave_plan_image";s:75:"https://sandbox.favethemes.com/houzez/wp-content/uploads/2016/01/plan-1.jpg";s:21:"fave_plan_description";s:290:"Plan description. Lorem ipsum dolor sit amet, consectetuer adipiscing elit, sed diam nonummy nibh euismod tincidunt ut laoreet dolore magna aliquam erat volutpat. Ut wisi enim ad minim veniam, quis nostrud exerci tation ullamcorper suscipit lobortis nisl ut aliquip ex ea commodo consequat.";}i:1;a:7:{s:15:"fave_plan_title";s:12:"Second Floor";s:15:"fave_plan_rooms";s:8:"543 Sqft";s:19:"fave_plan_bathrooms";s:8:"238 Sqft";s:15:"fave_plan_price";s:5:"1,600";s:14:"fave_plan_size";s:9:"1345 Sqft";s:15:"fave_plan_image";s:75:"https://sandbox.favethemes.com/houzez/wp-content/uploads/2016/01/plan-2.jpg";s:21:"fave_plan_description";s:290:"Plan description. Lorem ipsum dolor sit amet, consectetuer adipiscing elit, sed diam nonummy nibh euismod tincidunt ut laoreet dolore magna aliquam erat volutpat. Ut wisi enim ad minim veniam, quis nostrud exerci tation ullamcorper suscipit lobortis nisl ut aliquip ex ea commodo consequat.";}}',
        # ],
        "fave_featured": ["0", "0"],
        "houzez_featured_listing_date": [""],
        "fave_property_address": ["3001 W Ainslie St", "3001 W Ainslie St"],
        "fave_property_zip": ["60625", "60625"],
        # "fave_video_url": [
        #     "https://www.youtube.com/watch?v=-NInBEdSvp8",
        #     "https://www.youtube.com/watch?v=-NInBEdSvp8",
        # ],
        "fave_payment_status": ["not_paid", "not_paid"],
        "fave_property_map_street_view": ["show", "show"],
        "_dp_original": ["357", "357"],
        "fave_property_sec_price": ["1300", "1300"],
        "houzez_total_property_views": ["18148", "18148"],
        "fave_multiunit_plans_enable": ["disable", "disable"],
        # "houzez_views_by_date": [
        #     'a:61:{s:10:"12-19-2019";i:5;s:10:"12-20-2019";i:7;s:10:"12-21-2019";i:2;s:10:"12-22-2019";i:3;s:10:"12-23-2019";i:3;s:10:"12-24-2019";i:3;s:10:"12-25-2019";i:2;s:10:"12-26-2019";i:2;s:10:"12-27-2019";i:2;s:10:"12-28-2019";i:2;s:10:"12-29-2019";i:3;s:10:"12-30-2019";i:3;s:10:"12-31-2019";i:3;s:10:"01-01-2020";i:2;s:10:"01-02-2020";i:2;s:10:"01-03-2020";i:3;s:10:"01-04-2020";i:4;s:10:"01-05-2020";i:3;s:10:"01-06-2020";i:2;s:10:"01-07-2020";i:2;s:10:"01-08-2020";i:2;s:10:"01-09-2020";i:3;s:10:"01-10-2020";i:3;s:10:"01-11-2020";i:2;s:10:"01-12-2020";i:7;s:10:"01-13-2020";i:4;s:10:"01-14-2020";i:3;s:10:"01-15-2020";i:2;s:10:"01-16-2020";i:3;s:10:"01-17-2020";i:4;s:10:"01-18-2020";i:2;s:10:"01-19-2020";i:4;s:10:"01-20-2020";i:2;s:10:"01-21-2020";i:1;s:10:"01-22-2020";i:7;s:10:"01-23-2020";i:3;s:10:"01-24-2020";i:5;s:10:"01-25-2020";i:2;s:10:"01-26-2020";i:2;s:10:"01-27-2020";i:4;s:10:"01-28-2020";i:2;s:10:"01-29-2020";i:3;s:10:"01-30-2020";i:2;s:10:"01-31-2020";i:2;s:10:"02-10-2020";i:1;s:10:"02-12-2020";i:2;s:10:"02-18-2020";i:5;s:10:"02-24-2020";i:1;s:10:"03-02-2020";i:1;s:10:"03-05-2020";i:1;s:10:"10-14-2024";i:1;s:10:"10-18-2024";i:1;s:10:"11-14-2024";i:1;s:10:"11-16-2024";i:1;s:10:"11-18-2024";i:1;s:10:"11-22-2024";i:1;s:10:"11-24-2024";i:1;s:10:"11-26-2024";i:1;s:10:"12-07-2024";i:1;s:10:"12-26-2024";i:1;s:10:"12-30-2024";i:6;}',
        #     'a:61:{s:10:"12-19-2019";i:5;s:10:"12-20-2019";i:7;s:10:"12-21-2019";i:2;s:10:"12-22-2019";i:3;s:10:"12-23-2019";i:3;s:10:"12-24-2019";i:3;s:10:"12-25-2019";i:2;s:10:"12-26-2019";i:2;s:10:"12-27-2019";i:2;s:10:"12-28-2019";i:2;s:10:"12-29-2019";i:3;s:10:"12-30-2019";i:3;s:10:"12-31-2019";i:3;s:10:"01-01-2020";i:2;s:10:"01-02-2020";i:2;s:10:"01-03-2020";i:3;s:10:"01-04-2020";i:4;s:10:"01-05-2020";i:3;s:10:"01-06-2020";i:2;s:10:"01-07-2020";i:2;s:10:"01-08-2020";i:2;s:10:"01-09-2020";i:3;s:10:"01-10-2020";i:3;s:10:"01-11-2020";i:2;s:10:"01-12-2020";i:7;s:10:"01-13-2020";i:4;s:10:"01-14-2020";i:3;s:10:"01-15-2020";i:2;s:10:"01-16-2020";i:3;s:10:"01-17-2020";i:4;s:10:"01-18-2020";i:2;s:10:"01-19-2020";i:4;s:10:"01-20-2020";i:2;s:10:"01-21-2020";i:1;s:10:"01-22-2020";i:7;s:10:"01-23-2020";i:3;s:10:"01-24-2020";i:5;s:10:"01-25-2020";i:2;s:10:"01-26-2020";i:2;s:10:"01-27-2020";i:4;s:10:"01-28-2020";i:2;s:10:"01-29-2020";i:3;s:10:"01-30-2020";i:2;s:10:"01-31-2020";i:2;s:10:"02-10-2020";i:1;s:10:"02-12-2020";i:2;s:10:"02-18-2020";i:5;s:10:"02-24-2020";i:1;s:10:"03-02-2020";i:1;s:10:"03-05-2020";i:1;s:10:"10-14-2024";i:1;s:10:"10-18-2024";i:1;s:10:"11-14-2024";i:1;s:10:"11-16-2024";i:1;s:10:"11-18-2024";i:1;s:10:"11-22-2024";i:1;s:10:"11-24-2024";i:1;s:10:"11-26-2024";i:1;s:10:"12-07-2024";i:1;s:10:"12-26-2024";i:1;s:10:"12-30-2024";i:6;}',
        # ],
        # "fave_video_image": ["280", "280"],
        # "houzez_recently_viewed": ["2024-12-31 01:21:28", "2024-12-31 01:21:28"],
        # "fave_virtual_tour": [
        #     '\u003Ciframe width="853" height="480" src="https://my.matterport.com/show/?m=zEWsxhZpGba&play=1&qs=1" frameborder="0" allowfullscreen="allowfullscreen"\u003E\u003C/iframe\u003E',
        #     '\u003Ciframe width="853" height="480" src="https://my.matterport.com/show/?m=zEWsxhZpGba&play=1&qs=1" frameborder="0" allowfullscreen="allowfullscreen"\u003E\u003C/iframe\u003E',
        # ],
        "fave_single_top_area": ["global", "global"],
        "fave_single_content_area": ["global", "global"],
        "fave_property_agency": ["2790", "2790"],
        "fave_agent_display_option": ["agency_info", "agency_info"],
        "fave_rating": [
            "a:5:{i:1;i:0;i:2;i:0;i:3;i:0;i:4;i:0;i:5;i:0;}",
            "a:5:{i:1;i:0;i:2;i:0;i:3;i:0;i:4;i:0;i:5;i:0;}",
        ],
        # "fave_booking_shortcode": [
        #     "[bookingcalendar nummonths=2]",
        #     "[bookingcalendar nummonths=2]",
        # ],
        "fave_property_images": [
            "16107",
            "16106",
            "16105",
            "16108",
            "16109",
            "16110",
            "16111",
            "16124",
            "16112",
        ],
        "fave_attachments": ["99"],
        "rs_page_bg_color": [""],
        "_edit_lock": ["1735595488:1"],
    },
    "_links": {
        "self": [
            {
                "href": "https://allproperty.ai/wp-json/wp/v2/properties/361",
                "targetHints": {"allow": ["GET"]},
            }
        ],
        "collection": [{"href": "https://allproperty.ai/wp-json/wp/v2/properties"}],
        "about": [{"href": "https://allproperty.ai/wp-json/wp/v2/types/property"}],
        "author": [
            {"embeddable": True, "href": "https://allproperty.ai/wp-json/wp/v2/users/1"}
        ],
        "version-history": [
            {
                "count": 0,
                "href": "https://allproperty.ai/wp-json/wp/v2/properties/361/revisions",
            }
        ],
        "wp:featuredmedia": [
            {
                "embeddable": True,
                "href": "https://allproperty.ai/wp-json/wp/v2/media/16124",
            }
        ],
        "wp:attachment": [
            {"href": "https://allproperty.ai/wp-json/wp/v2/media?parent=361"}
        ],
        "wp:term": [
            {
                "taxonomy": "property_type",
                "embeddable": True,
                "href": "https://allproperty.ai/wp-json/wp/v2/property_type?post=361",
            },
            {
                "taxonomy": "property_status",
                "embeddable": True,
                "href": "https://allproperty.ai/wp-json/wp/v2/property_status?post=361",
            },
            {
                "taxonomy": "property_feature",
                "embeddable": True,
                "href": "https://allproperty.ai/wp-json/wp/v2/property_feature?post=361",
            },
            {
                "taxonomy": "property_label",
                "embeddable": True,
                "href": "https://allproperty.ai/wp-json/wp/v2/property_label?post=361",
            },
            {
                "taxonomy": "property_country",
                "embeddable": True,
                "href": "https://allproperty.ai/wp-json/wp/v2/property_country?post=361",
            },
            {
                "taxonomy": "property_state",
                "embeddable": True,
                "href": "https://allproperty.ai/wp-json/wp/v2/property_state?post=361",
            },
            {
                "taxonomy": "property_city",
                "embeddable": True,
                "href": "https://allproperty.ai/wp-json/wp/v2/property_city?post=361",
            },
            {
                "taxonomy": "property_area",
                "embeddable": True,
                "href": "https://allproperty.ai/wp-json/wp/v2/property_area?post=361",
            },
        ],
        # "curies": [
        #     {"name": "wp", "href": "https://api.w.org/{rel}", "templated": True}
        # ],
    },
}
property_data = {
    "status": "publish",
    "type": "property",
    "title": "Flat / apartment for sale in calle de Tòquio",
    "content": (
        "<p>Lorem ipsum dolor sit amet, consectetuer adipiscing elit, sed diam nonummy nibh "
        "euismod tincidunt ut laoreet dolore magna aliquam erat volutpat. Ut wisi enim ad minim "
        "veniam, quis nostrud exerci tation ullamcorper suscipit lobortis nisl ut aliquip ex ea "
        "commodo consequat.</p>"
    ),
    "excerpt": "<p>Lorem ipsum dolor sit amet...</p>",
    "featured_media": 17407,  # ID изображения
    "property_type": [60],
    "property_status": [30],
    "property_feature": [13, 17, 27, 32, 36, 37, 41, 51, 54, 57, 63, 64, 67, 69, 70],
    "property_label": [49],
    "property_country": [65],
    "property_state": [35],
    "property_city": [24],
    "property_area": [14],
    "class_list": [
        "post-361",
        "property",
        "type-property",
        "status-publish",
        "has-post-thumbnail",
        "hentry",
        "property_type-single-family-home",
        "property_status-for-sale",
        "property_feature-air-conditioning",
        "property_feature-barbeque",
        "property_feature-dryer",
        "property_feature-gym",
        "property_feature-laundry",
        "property_feature-lawn",
        "property_feature-microwave",
        "property_feature-outdoor-shower",
        "property_feature-refrigerator",
        "property_feature-sauna",
        "property_feature-swimming-pool",
        "property_feature-tv-cable",
        "property_feature-washer",
        "property_feature-wifi",
        "property_feature-window-coverings",
        "property_label-open-house",
        "property_country-united-states",
        "property_state-illinois",
        "property_city-chicago",
        "property_area-albany-park",
    ],
    "property_meta": {
        "fave_property_images": [
            17548,
        ]
    },
}
property_data = {
    "status": "publish",
    "type": "property",
    "title": "Flat / apartment for sale in calle de Tòquio",
    "content": "<p>Описание объекта недвижимости...</p>",
    "excerpt": "<p>Краткое описание...</p>",
    "meta": {"fave_property_images": [{"id": "17548"}]},
}
property_data = {
    "status": "publish",
    "type": "property",
    "title": {"rendered": "Flat / apartment for sale in calle de Tòquio"},
    "content": "<p>КУ_КУ КУ_КУ</p>",
    "excerpt": "<p>ку</p>",
    "author": 1,
    "featured_media": 16124,
    "parent": 0,
    "menu_order": 0,
    "template": "",
    "property_type": [60],
    "property_status": [30],
    "property_feature": [13, 17, 27, 32, 36, 37, 41, 51, 54, 57, 63, 64, 67, 69, 70],
    "property_label": [49],
    "property_country": [65],
    "property_state": [35],
    "property_city": [24],
    "property_area": [14],
    "class_list": [
        "post-361",
        "property",
        "type-property",
        "status-publish",
        "has-post-thumbnail",
        "hentry",
        "property_type-single-family-home",
        "property_status-for-sale",
        "property_feature-air-conditioning",
        "property_feature-barbeque",
        "property_feature-dryer",
        "property_feature-gym",
        "property_feature-laundry",
        "property_feature-lawn",
        "property_feature-microwave",
        "property_feature-outdoor-shower",
        "property_feature-refrigerator",
        "property_feature-sauna",
        "property_feature-swimming-pool",
        "property_feature-tv-cable",
        "property_feature-washer",
        "property_feature-wifi",
        "property_feature-window-coverings",
        "property_label-open-house",
        "property_country-united-states",
        "property_state-illinois",
        "property_city-chicago",
        "property_area-albany-park",
    ],
    "property_meta": {
        "fave_property_price": ["670000", "670000"],
        "author": 1,
        "featured_media": 16124,
        "parent": 0,
        "menu_order": 0,
        "template": "",
        "property_type": [60],
        "property_status": [30],
        "property_feature": [
            13,
            17,
            27,
            32,
            36,
            37,
            41,
            51,
            54,
            57,
            63,
            64,
            67,
            69,
            70,
        ],
        "property_label": [49],
        "property_country": [65],
        "property_state": [35],
        "property_city": [24],
        "property_area": [14],
        "class_list": [
            "post-361",
            "property",
            "type-property",
            "status-publish",
            "has-post-thumbnail",
            "hentry",
            "property_type-single-family-home",
            "property_status-for-sale",
            "property_feature-air-conditioning",
            "property_feature-barbeque",
            "property_feature-dryer",
            "property_feature-gym",
            "property_feature-laundry",
            "property_feature-lawn",
            "property_feature-microwave",
            "property_feature-outdoor-shower",
            "property_feature-refrigerator",
            "property_feature-sauna",
            "property_feature-swimming-pool",
            "property_feature-tv-cable",
            "property_feature-washer",
            "property_feature-wifi",
            "property_feature-window-coverings",
            "property_label-open-house",
            "property_country-united-states",
            "property_state-illinois",
            "property_city-chicago",
            "property_area-albany-park",
        ],
        "fave_property_images": ["17548", "17407", "17406", "17399"],
        "fave_attachments": ["99"],
        "rs_page_bg_color": [""],
        "_edit_lock": ["1735748551:1"],
    },
    "fave_property_images": "16107",
}
# Загрузка токена
TOKEN_FILE = "token.json"
with open(TOKEN_FILE, "r", encoding="utf-8") as token_file:
    token_data = json.load(token_file)
    token = token_data.get("token")

# Заголовки для запроса
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}

# Отправка запроса с использованием токена
response = requests.post(api_url, headers=headers, json=property_data, timeout=30)

# Обработка ответа
if response.status_code == 201:
    print("Property created successfully!")
    print(response.json())
else:
    print(f"Failed to create property. Status code: {response.status_code}")
    print(response.text)
