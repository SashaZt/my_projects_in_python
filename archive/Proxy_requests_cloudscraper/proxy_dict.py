import csv

proxies = []

with open('C:\\scrap_tutorial-master\\ucars.pro\\url_04.csv', newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        proxies.append(f"{row[0]}")
print(proxies)