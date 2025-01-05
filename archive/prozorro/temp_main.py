# -*- coding: utf-8 -*-

# lots = json_data.get('lots', [{}])
# auctionPeriod = lots[0].get('auctionPeriod', {})
# auctionPeriod_auctionPeriod = lots[0].get('auctionPeriod', {}).get('startDate')
# if auctionPeriod_auctionPeriod:
#     datetime_obj_auctionPeriod = datetime.fromisoformat(auctionPeriod_auctionPeriod)
#
#     date_auctionPeriod = datetime_obj_auctionPeriod.strftime("%d.%m.%Y")
#     time_auctionPeriod = datetime_obj_auctionPeriod.strftime("%H:%M")
# else:
#     date_auctionPeriod = time_auctionPeriod = None


# # "Кінцевий строк подання тендерних пропозицій"
# lots = json_data.get('lots', [{}])
# try:
#     # Пытаемся получить auctionPeriod из первого элемента списка lots
#     auctionPeriod_auctionPeriod = lots[0].get('auctionPeriod', {}).get('shouldStartAfter')
#     if not auctionPeriod_auctionPeriod:  # Если значение отсутствует, принудительно переходим к блоку except
#         raise KeyError("shouldStartAfter is missing")
# except (KeyError, IndexError):  # Обрабатываем отсутствие ключа или доступа к элементу списка
#     auctionPeriod_auctionPeriod = json_data.get('tenderPeriod', {}).get('endDate')
#
# if auctionPeriod_auctionPeriod:
#     datetime_obj = datetime.fromisoformat(auctionPeriod_auctionPeriod)
#
#     date_auctionPeriod_auctionPeriod = (datetime_obj - timedelta(days=1)).strftime("%d.%m.%Y")
#     time_auctionPeriod_auctionPeriod = (datetime_obj - timedelta(minutes=1)).strftime("%H:%M")
# else:
#     date_auctionPeriod_auctionPeriod = time_auctionPeriod_auctionPeriod = None
# try:
#     auctionPeriod_auctionPeriod = lots[0].get('auctionPeriod', {}).get('shouldStartAfter')
#     if auctionPeriod_auctionPeriod:
#         datetime_obj_auctionPeriod_auctionPeriod = datetime.fromisoformat(auctionPeriod_auctionPeriod)
#
#         date_auctionPeriod_auctionPeriod = datetime_obj_auctionPeriod_auctionPeriod - timedelta(days=1)
#         date_auctionPeriod_auctionPeriod = date_auctionPeriod_auctionPeriod.strftime("%d.%m.%Y")
#
#         datetime_obj_minus_one_minute = datetime_obj_auctionPeriod_auctionPeriod - timedelta(minutes=1)
#         time_auctionPeriod_auctionPeriod = datetime_obj_minus_one_minute.strftime("%H:%M")
#     else:
#         date_auctionPeriod_auctionPeriod = time_auctionPeriod_auctionPeriod = None
# except:
#     auctionPeriod_auctionPeriod = json_data['tenderPeriod']['endDate']
#     if auctionPeriod_auctionPeriod:
#         datetime_obj_auctionPeriod_auctionPeriod = datetime.fromisoformat(auctionPeriod_auctionPeriod)
#
#         date_auctionPeriod_auctionPeriod = datetime_obj_auctionPeriod_auctionPeriod - timedelta(days=1)
#         date_auctionPeriod_auctionPeriod = date_auctionPeriod_auctionPeriod.strftime("%d.%m.%Y")
#
#         datetime_obj_minus_one_minute = datetime_obj_auctionPeriod_auctionPeriod - timedelta(minutes=1)
#         time_auctionPeriod_auctionPeriod = datetime_obj_minus_one_minute.strftime("%H:%M")
#     else:
#         date_auctionPeriod_auctionPeriod = time_auctionPeriod_auctionPeriod = None

# # "Звернення за роз’ясненнями"
# enquiryPeriod_endDate = json_data.get('enquiryPeriod', {}).get('endDate')
# if enquiryPeriod_endDate:
#     datetime_obj_enquiryPeriod_endDate = datetime.fromisoformat(enquiryPeriod_endDate)
#
#     date_enquiryPeriod_endDate = datetime_obj_enquiryPeriod_endDate - timedelta(days=1)
#     date_enquiryPeriod_endDate = date_enquiryPeriod_endDate.strftime("%d.%m.%Y")
#
#     datetime_obj_minus_one_minute = datetime_obj_enquiryPeriod_endDate - timedelta(minutes=1)
#     time_enquiryPeriod_endDate = datetime_obj_minus_one_minute.strftime("%H:%M")
# else:
#     date_enquiryPeriod_endDate = time_enquiryPeriod_endDate = None
# """Дата и время победившей ставки"""
# dara_pending = json_data['awards'][0]['date']
# datetime_obj_pending = datetime.fromisoformat(dara_pending)
# """Дата и время победившей ставки"""
# date_pending = datetime_obj_pending.strftime("%d.%m.%Y")
# time_pending = datetime_obj_pending.strftime("%H:%M")
# award_status = json_data.get('awards', [{}])[0].get('status', None)
# if edrpo_customer in dict_comany_edrpo.values():
#     if award_status == 'pending':
#         award_status = None
#     if award_status == 'active':
#         award_status = 'Победа'
#     if award_status == 'unsuccessful':
#         award_status = None
# else:
#     award_status = None


# if json_data.get('guarantee', {}):
#     guarantee_amount = json_data.get('guarantee', {}).get('amount', None)
# else:
#     guarantee_amount = None
# if len(json_data.get('criteria', [])) > 10:
#     criteria = json_data.get('criteria')[10]  # Безопасно получаем элемент с индексом 10
#     requirementGroups = criteria.get('requirementGroups', [{}])[0]  # Безопасно получаем первый элемент списка
#     requirements = requirementGroups.get('requirements', [{}])[0]  # Безопасно получаем первый элемент
#     bank_garantiy = requirements.get('description', None)  # И, наконец, получаем 'description'
#
#     # Проверяем, содержит ли bank_garantiy нужный текст, только если bank_garantiy не None
#     if bank_garantiy:  # Проверяет, не пустая ли строка и не None ли она
#         bank_garantiy = 'Да'
#     else:
#         bank_garantiy = None
# else:
#     bank_garantiy = None  # Если элементов в списке 'criteria' меньше 11, возвращаем None
dateCreated = json_data.get('dateCreated', None)

# # "Початок аукціону"
# lots = json_data.get('lots', [{}])
# # auctionPeriod = lots[0].get('auctionPeriod', {})
# # "Кінцевий строк подання тендерних пропозицій"
# auctionPeriod_auctionPeriod = lots[0].get('auctionPeriod', {}).get('startDate')
# if auctionPeriod_auctionPeriod:
#     datetime_obj_auctionPeriod = datetime.fromisoformat(auctionPeriod_auctionPeriod)
#
#     date_auctionPeriod = datetime_obj_auctionPeriod.strftime("%d.%m.%Y")
#     time_auctionPeriod = datetime_obj_auctionPeriod.strftime("%H:%M")
# else:
#     date_auctionPeriod_auctionPeriod = time_auctionPeriod_auctionPeriod = None

# # "Очікувана вартість"
# price_tender = json_data.get('value', {}).get('amount', None)

# "Відкриті торги з особливостями"

# # "Звернення за роз’ясненнями"
# enquiryPeriod_endDate = json_data.get('enquiryPeriod', {}).get('endDate')
# if enquiryPeriod_endDate:
#     datetime_obj_enquiryPeriod_endDate = datetime.fromisoformat(enquiryPeriod_endDate)
#
#     date_enquiryPeriod_endDate = datetime_obj_enquiryPeriod_endDate - timedelta(days=1)
#     date_enquiryPeriod_endDate = date_enquiryPeriod_endDate.strftime("%d.%m.%Y")
#
#     datetime_obj_minus_one_minute = datetime_obj_enquiryPeriod_endDate - timedelta(minutes=1)
#     time_enquiryPeriod_endDate = datetime_obj_minus_one_minute.strftime("%H:%M")
# else:
#     date_enquiryPeriod_endDate = time_enquiryPeriod_endDate = None
#
# # "Кінцевий строк подання тендерних пропозицій"
# auctionPeriod_auctionPeriod = lots[0].get('auctionPeriod', {}).get('shouldStartAfter')
# if auctionPeriod_auctionPeriod:
#     datetime_obj_auctionPeriod_auctionPeriod = datetime.fromisoformat(auctionPeriod_auctionPeriod)
#
#     date_auctionPeriod_auctionPeriod = datetime_obj_auctionPeriod_auctionPeriod - timedelta(days=1)
#     date_auctionPeriod_auctionPeriod = date_auctionPeriod_auctionPeriod.strftime("%d.%m.%Y")
#     datetime_obj_minus_one_minute = datetime_obj_auctionPeriod_auctionPeriod - timedelta(minutes=1)
#     time_auctionPeriod_auctionPeriod = datetime_obj_minus_one_minute.strftime("%H:%M")
# else:
#     date_auctionPeriod_auctionPeriod = time_auctionPeriod_auctionPeriod = None

# "Початок аукціону"
# lots = json_data.get('lots', [{}])
# auctionPeriod = lots[0].get('auctionPeriod', {})
# # "Кінцевий строк подання тендерних пропозицій"
# auctionPeriod_auctionPeriod = lots[0].get('auctionPeriod', {}).get('startDate')
# if auctionPeriod_auctionPeriod:
#     datetime_obj_auctionPeriod = datetime.fromisoformat(auctionPeriod_auctionPeriod)
#
#     date_auctionPeriod = datetime_obj_auctionPeriod.strftime("%d.%m.%Y")
#     time_auctionPeriod = datetime_obj_auctionPeriod.strftime("%H:%M")
# else:
#     date_auctionPeriod_auctionPeriod = time_auctionPeriod_auctionPeriod = None
# # "Звернення за роз’ясненнями"
# enquiryPeriod_endDate = json_data.get('enquiryPeriod', {}).get('endDate')
# if enquiryPeriod_endDate:
#     datetime_obj_enquiryPeriod_endDate = datetime.fromisoformat(enquiryPeriod_endDate)
#
#     date_enquiryPeriod_endDate = datetime_obj_enquiryPeriod_endDate - timedelta(days=1)
#     date_enquiryPeriod_endDate = date_enquiryPeriod_endDate.strftime("%d.%m.%Y")
#
#     datetime_obj_minus_one_minute = datetime_obj_enquiryPeriod_endDate - timedelta(minutes=1)
#     time_enquiryPeriod_endDate = datetime_obj_minus_one_minute.strftime("%H:%M")
# else:
#     date_enquiryPeriod_endDate = time_enquiryPeriod_endDate = None
#
# # "Кінцевий строк подання тендерних пропозицій"
# auctionPeriod_auctionPeriod = lots[0].get('auctionPeriod', {}).get('shouldStartAfter')
# if auctionPeriod_auctionPeriod:
#     datetime_obj_auctionPeriod_auctionPeriod = datetime.fromisoformat(auctionPeriod_auctionPeriod)
#
#     date_auctionPeriod_auctionPeriod = datetime_obj_auctionPeriod_auctionPeriod - timedelta(days=1)
#     date_auctionPeriod_auctionPeriod = date_auctionPeriod_auctionPeriod.strftime("%d.%m.%Y")
#     datetime_obj_minus_one_minute = datetime_obj_auctionPeriod_auctionPeriod - timedelta(minutes=1)
#     time_auctionPeriod_auctionPeriod = datetime_obj_minus_one_minute.strftime("%H:%M")
# else:
#     date_auctionPeriod_auctionPeriod = time_auctionPeriod_auctionPeriod = None
# # "Початок аукціону"
# lots = json_data.get('lots', [{}])
# auctionPeriod = lots[0].get('auctionPeriod', {})
# # "Кінцевий строк подання тендерних пропозицій"
# auctionPeriod_auctionPeriod = lots[0].get('auctionPeriod', {}).get('startDate')
# if auctionPeriod_auctionPeriod:
#     datetime_obj_auctionPeriod = datetime.fromisoformat(auctionPeriod_auctionPeriod)
#
#     date_auctionPeriod = datetime_obj_auctionPeriod.strftime("%d.%m.%Y")
#     time_auctionPeriod = datetime_obj_auctionPeriod.strftime("%H:%M")
# else:
#     date_auctionPeriod_auctionPeriod = time_auctionPeriod_auctionPeriod = None
# # "Звернення за роз’ясненнями"
# enquiryPeriod_endDate = json_data.get('enquiryPeriod', {}).get('endDate')
# if enquiryPeriod_endDate:
#     datetime_obj_enquiryPeriod_endDate = datetime.fromisoformat(enquiryPeriod_endDate)
#
#     date_enquiryPeriod_endDate = datetime_obj_enquiryPeriod_endDate - timedelta(days=1)
#     date_enquiryPeriod_endDate = date_enquiryPeriod_endDate.strftime("%d.%m.%Y")
#
#     datetime_obj_minus_one_minute = datetime_obj_enquiryPeriod_endDate - timedelta(minutes=1)
#     time_enquiryPeriod_endDate = datetime_obj_minus_one_minute.strftime("%H:%M")
# else:
#     date_enquiryPeriod_endDate = time_enquiryPeriod_endDate = None
#
# # "Кінцевий строк подання тендерних пропозицій"
# auctionPeriod_auctionPeriod = lots[0].get('auctionPeriod', {}).get('shouldStartAfter')
# if auctionPeriod_auctionPeriod:
#     datetime_obj_auctionPeriod_auctionPeriod = datetime.fromisoformat(auctionPeriod_auctionPeriod)
#
#     date_auctionPeriod_auctionPeriod = datetime_obj_auctionPeriod_auctionPeriod - timedelta(days=1)
#     date_auctionPeriod_auctionPeriod = date_auctionPeriod_auctionPeriod.strftime("%d.%m.%Y")
#     datetime_obj_minus_one_minute = datetime_obj_auctionPeriod_auctionPeriod - timedelta(minutes=1)
#     time_auctionPeriod_auctionPeriod = datetime_obj_minus_one_minute.strftime("%H:%M")
# else:
#     date_auctionPeriod_auctionPeriod = time_auctionPeriod_auctionPeriod = None
# """Победитель """
# award_name_customer = json_data.get('awards', [{}])[0].get('suppliers', [{}])[0].get('name', None)
# """Ставка которая победила"""
# award_value_customer = json_data.get('awards', [{}])[0].get('value', [{}]).get('amount', None)
# dara_pending = json_data['awards'][0]['date']
# datetime_obj_pending = datetime.fromisoformat(dara_pending)
# """Дата и время победившей ставки"""
# date_pending = datetime_obj_pending.strftime("%d.%m.%Y")
# time_pending = datetime_obj_pending.strftime("%H:%M")
# """Победитель ЕДРПО"""
# edrpo_customer = json_data.get('awards', [{}])[0].get('suppliers', [{}])[0].get('identifier').get('id',
#                                                                                                   None)
# award_status = json_data.get('awards', [{}])[0].get('status', None)
# if edrpo_customer in dict_comany_edrpo.values():
#     if award_status == 'pending':
#         award_status = None
#     if award_status == 'active':
#         award_status = 'Победа'
#     if award_status == 'unsuccessful':
#         award_status = None
# else:
#     award_status = None
# """Победитель """
# award_name_customer = json_data.get('awards', [{}])[0].get('suppliers', [{}])[0].get('name', None)
# """Победитель ЕДРПО"""
# edrpo_customer = json_data.get('awards', [{}])[0].get('suppliers', [{}])[0].get('identifier').get('id',
#                                                                                                   None)
# # edrpo_customer = json_data['awards'][0]['suppliers'][0]['identifier']['id']

# """Ставка которая победила"""
# award_value_customer = json_data.get('awards', [{}])[0].get('value', [{}]).get('amount', None)
# dara_pending = json_data['awards'][0]['date']
# datetime_obj_pending = datetime.fromisoformat(dara_pending)
# """Дата и время победившей ставки"""
# date_pending = datetime_obj_pending.strftime("%d.%m.%Y")
# time_pending = datetime_obj_pending.strftime("%H:%M")
# # award_status = json_data.get('awards', [{}])[0].get('status', None)
# if edrpo_customer in dict_comany_edrpo.values():
#     if award_status == 'pending':
#         award_status = None
#     if award_status == 'active':
#         award_status = 'Победа'
#     if award_status == 'unsuccessful':
#         award_status = None
# else:
#     award_status = None