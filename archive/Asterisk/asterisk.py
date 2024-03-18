"""Внутринние номера"""
# data = {}
#
# with open('file.csv', newline='', encoding="utf-8") as csvfile:
#     reader = csv.reader(csvfile, delimiter=',')
#     next(reader)  # пропускаем первую строку
#     for row in reader:
#         vn = row[0]
#         p_i_p = row[1]
#         data[vn] = f'(aut)\ncallerid="{p_i_p}" <{vn}>\ncontext=outcoling_ice'
#
# for vn, value in data.items():
#     print(f'[{vn}]{value}')
import csv
# from openpyxl import Workbook
#
# wb = Workbook()
# ws = wb.active
#
# with open('file.csv', newline='', encoding="utf-8") as csvfile:
#     reader = csv.reader(csvfile, delimiter=',')
#     next(reader)  # пропускаем первую строку
#     for row in reader:
#         vn = row[0]
#         p_i_p = row[1]
#         cell_value = f"[{vn}](aut)\ncallerid=\"{p_i_p}\" <{vn}>\ncontext=outcoling_ice"
#         ws.append([cell_value])
#
# wb.save('output.xlsx')

"""MAC_Ver1.csv"""
with open('test_.csv', 'r') as file:
    reader = csv.reader(file, delimiter=';')
    for row in reader:
        vn = row[0]
        mac = row[1]
        output_string = f"{mac},{vn},1235,{vn},{vn},GXP1620-{vn}"
        print(output_string)