import os
import json
from lxml import etree

all_voevodstvo = []
seen_cities = set()

for filename in os.listdir('C:/scrap_tutorial-master/Temp/che/'):
    if filename.endswith('.osm'):
        name_csv = filename.replace(".osm", '').replace('-latest', '')
        print(name_csv)
        filepath = os.path.join('C:/scrap_tutorial-master/Temp/che/', filename)
        current_cities = set()

        # Используем iterparse из lxml
        context = etree.iterparse(filepath, events=("start",), tag="node", huge_tree=True)

        for event, elem in context:
            addr_tags = {}
            for tag in elem.findall('tag'):
                k = tag.get('k')
                v = tag.get('v')
                if k in ['addr:city', 'addr:province', 'addr:place', 'addr:suburb']:
                    addr_tags[k] = v.replace('/', ' ').replace('\\', ' ')

            if 'addr:city' in addr_tags:
                selected_value = addr_tags['addr:city']
            elif 'addr:province' in addr_tags:
                selected_value = addr_tags['addr:province']
            elif 'addr:place' in addr_tags:
                selected_value = addr_tags['addr:place']
            elif 'addr:suburb' in addr_tags:
                selected_value = addr_tags['addr:suburb']
            else:
                continue

            if selected_value not in seen_cities:
                seen_cities.add(selected_value)
                current_cities.add(selected_value)

            # освобождаем память
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]

        all_voevodstvo.append({
            'voevodstvo': name_csv.replace('-latest', ''),
            'cities': list(current_cities)
        })

        with open(f'{name_csv}.json', 'w', encoding='utf-8') as f:
            json.dump(all_voevodstvo, f, ensure_ascii=False, indent=4)
