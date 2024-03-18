from bs4 import BeautifulSoup
import csv
import os
import glob
import requests
import time
import json

"""Рабочи скрипт"""


def parsing():
    # urls = [
    #     'https://www.houzz.com/professionals/architect/probr0-bo~t_11784',
    #     'https://www.houzz.com/professionals/adu-contractors/probr0-bo~t_34256',
    #     'https://www.houzz.com/professionals/agents-and-brokers/probr0-bo~t_11822',
    #     'https://www.houzz.com/professionals/appliances/probr0-bo~t_11810',
    #     'https://www.houzz.com/professionals/artist-and-artisan/probr0-bo~t_11801',
    #     'https://www.houzz.com/professionals/backyard-courts/probr0-bo~t_11838',
    #     'https://www.houzz.com/professionals/basement-remodelers/probr0-bo~t_34261',
    #     'https://www.houzz.com/professionals/bedding-and-bath/probr0-bo~t_11806',
    #     'https://www.houzz.com/professionals/building-supplies/probr0-bo~t_11805',
    #     'https://www.houzz.com/professionals/cabinets/probr0-bo~t_11829',
    #     'https://www.houzz.com/professionals/carpenter/probr0-bo~t_11831',
    #     'https://www.houzz.com/professionals/carpet-and-flooring/probr0-bo~t_11799',
    #     'https://www.houzz.com/professionals/carpet-cleaners/probr0-bo~t_27201',
    #     'https://www.houzz.com/professionals/chimney-cleaners/probr0-bo~t_27200',
    #     'https://www.houzz.com/professionals/custom-closet-designers/probr0-bo~t_33907',
    #     'https://www.houzz.com/professionals/custom-countertops/probr0-bo~t_33909',
    #     'https://www.houzz.com/professionals/decks-and-patios/probr0-bo~t_11830',
    #     'https://www.houzz.com/professionals/design-build/probr0-bo~t_11793',
    #     'https://www.houzz.com/professionals/doors/probr0-bo~t_11827',
    #     'https://www.houzz.com/professionals/driveways-and-paving/probr0-bo~t_11832',
    #     'https://www.houzz.com/professionals/electrical-contractors/probr0-bo~t_11818',
    #     'https://www.houzz.com/professionals/environmental-services-and-restoration/probr0-bo~t_11813',
    #     'https://www.houzz.com/professionals/exterior-cleaners/probr0-bo~t_27202',
    #     'https://www.houzz.com/professionals/fencing-and-gates/probr0-bo~t_11833',
    #     'https://www.houzz.com/professionals/fireplace/probr0-bo~t_11800',
    #     'https://www.houzz.com/professionals/furniture-and-accessories/probr0-bo~t_11802',
    #     'https://www.houzz.com/professionals/furniture-refinishing-and-upholstery/probr0-bo~t_11840',
    #     'https://www.houzz.com/professionals/garage-doors/probr0-bo~t_11828',
    #     'https://www.houzz.com/professionals/garden-and-landscape-supplies/probr0-bo~t_11809',
    #     'https://www.houzz.com/professionals/general-contractor/probr0-bo~t_11786',
    #     'https://www.houzz.com/professionals/glass-and-shower-door-dealers/probr0-bo~t_27203',
    #     'https://www.houzz.com/professionals/handyman/probr0-bo~t_27204',
    #     'https://www.houzz.com/professionals/hardwood-flooring-dealers/probr0-bo~t_28349',
    #     'https://www.houzz.com/professionals/home-additions-and-extensions/probr0-bo~t_34259',
    #     'https://www.houzz.com/professionals/home-builders/probr0-bo~t_11823',
    #     'https://www.houzz.com/professionals/home-media/probr0-bo~t_11787',
    #     'https://www.houzz.com/professionals/home-remodeling/probr0-bo~t_34257',
    #     'https://www.houzz.com/professionals/home-staging/probr0-bo~t_11789',
    #     'https://www.houzz.com/professionals/hot-tub-and-spa-dealers/probr0-bo~t_28350',
    #     'https://www.houzz.com/professionals/house-cleaners/probr0-bo~t_27205',
    #     'https://www.houzz.com/professionals/hvac-contractors/probr0-bo~t_11814',
    #     'https://www.houzz.com/professionals/interior-designer/probr0-bo~t_11785',
    #     'https://www.houzz.com/professionals/ironwork/probr0-bo~t_11834',
    #     'https://www.houzz.com/professionals/kitchen-and-bath/probr0-bo~t_11790',
    #     'https://www.houzz.com/professionals/kitchen-and-bath-fixtures/probr0-bo~t_11804',
    #     'https://www.houzz.com/professionals/kitchen-and-bath-remodelers/probr0-bo~t_11825',
    #     'https://www.houzz.com/professionals/landscape-architect/probr0-bo~t_11788',
    #     'https://www.houzz.com/professionals/landscape-contractors/probr0-bo~t_11812',
    #     'https://www.houzz.com/professionals/lawn-and-sprinklers/probr0-bo~t_11835',
    #     'https://www.houzz.com/professionals/lighting/probr0-bo~t_11794',
    #     'https://www.houzz.com/professionals/movers/probr0-bo~t_27206',
    #     'https://www.houzz.com/professionals/outdoor-lighting-and-audio-visual-systems/probr0-bo~t_11836',
    #     'https://www.houzz.com/professionals/outdoor-play/probr0-bo~t_11837',
    #     'https://www.houzz.com/professionals/paint-and-wall-coverings/probr0-bo~t_11807',
    #     'https://www.houzz.com/professionals/painters/probr0-bo~t_27105',
    #     'https://www.houzz.com/professionals/pest-control/probr0-bo~t_27207',
    #     'https://www.houzz.com/professionals/photographer/probr0-bo~t_11792',
    #     'https://www.houzz.com/professionals/plumbing-contractors/probr0-bo~t_11817',
    #     'https://www.houzz.com/professionals/pools-and-spas/probr0-bo~t_11795',
    #     'https://www.houzz.com/professionals/professional-organizers/probr0-bo~t_33908',
    #     'https://www.houzz.com/professionals/roofing-and-gutter/probr0-bo~t_11819',
    #     'https://www.houzz.com/professionals/rubbish-removal/probr0-bo~t_11820',
    #     'https://www.houzz.com/professionals/septic-tanks-and-systems/probr0-bo~t_11815',
    #     'https://www.houzz.com/professionals/siding-and-exterior/probr0-bo~t_11826',
    #     'https://www.houzz.com/professionals/solar-energy-contractors/probr0-bo~t_11816',
    #     'https://www.houzz.com/professionals/spa-and-pool-maintenance/probr0-bo~t_28351',
    #     'https://www.houzz.com/professionals/specialty-contractors/probr0-bo~t_11811',
    #     'https://www.houzz.com/professionals/staircases/probr0-bo~t_11839',
    #     'https://www.houzz.com/professionals/stone-pavers-and-concrete/probr0-bo~t_11824',
    #     'https://www.houzz.com/professionals/tile-and-stone-contractors/probr0-bo~t_33910',
    #     'https://www.houzz.com/professionals/tree-service/probr0-bo~t_11821',
    #     'https://www.houzz.com/professionals/universal-design/probr0-bo~t_34260',
    #     'https://www.houzz.com/professionals/window-cleaners/probr0-bo~t_27209'
    #     'https://www.houzz.com/professionals/window-coverings/probr0-bo~t_11798',
    #     'https://www.houzz.com/professionals/windows/probr0-bo~t_11797',
    #     'https://www.houzz.com/professionals/wine-cellars/probr0-bo~t_11841',
    #
    # ]
    group = 'specialty-contractors'
    with open(f'{group}.csv', "w", errors='ignore', encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=";", lineterminator="\r")
        writer.writerow(
            ('name_company', 'telephone_company', 'www_company', 'costEstimate_company', 'address', 'street_address',
             'addressLocality', 'addressRegion', 'postalCode', 'addressCountry',
             'facebook_company', 'twitter_company', 'linkedin_company', 'blog_company', 'service_company',
             'category_company', 'catalog', 'ratingValue', 'reviewCount', 'proyectos_company'))
        # for url in urls[:1]:
        # group = url.split('/')[-2]
        folders_html = fr"c:\DATA\houzz_com\product\{group}\*.html"
        files_html = glob.glob(folders_html)
        for i in files_html:
            catalog = i.split('\\')[-2]
            datas = []
            with open(i, encoding="utf-8") as html_file:
                src = html_file.read()
            facebook_company = ""
            twitter_company = ""
            linkedin_company = ""
            blog_company = ""
            soup = BeautifulSoup(src, 'lxml')
            script_tag = soup.find('script', {'type': 'application/json'})
            try:
                json_data = json.loads(script_tag.string)
            except:
                # print(i)
                continue
            try:
                name_company = json_data['data']['stores']['data']['ProProfileStore']['data']['user'][
                    'displayName'].replace('- ', '').replace('* ', '').replace('· ', '')
            except:
                name_company = None
            try:
                telephone_company = \
                    json_data['data']['stores']['data']['ProProfileStore']['data']['user']['professional'][
                        'formattedPhone']
            except:
                telephone_company = None
            try:
                www_company = \
                    json_data['data']['stores']['data']['ProProfileStore']['data']['user']['professional'][
                        'rawDomain']
            except:
                www_company = None
            try:
                costEstimate_company = \
                    json_data['data']['stores']['data']['ProProfileStore']['data']['user']['professional'][
                        'costEstimate']
            except:
                costEstimate_company = None

            try:
                address_company = \
                    json_data['data']['stores']['data']['ProProfileStore']['data']['user']['professional'][
                        'formattedAddress']
            except:
                continue
            address = ''
            try:
                category_companys = \
                    json_data['data']['stores']['data']['ProProfileStore']['data']['user']['professional'][
                        'seoProType']
                soup_category = BeautifulSoup(category_companys, 'html.parser')
                category_company = soup_category.find('span').text.strip()

            except:
                category_company = None
            try:
                soup_add = BeautifulSoup(address_company, 'html.parser')

                address_elements = soup_add.find_all('span', itemprop='streetAddress')
                for element in address_elements:
                    address += element.text.strip() + ' '
            except:
                pass

            try:
                service_company = \
                    json_data['data']['stores']['data']['ProProfileStore']['data']['user']['professional'][
                        'servicesProvided'].replace('-', '').replace('* ', '').replace('· ', '').replace('\n',
                                                                                                         '')
            except:
                service_company = None
            try:
                postal_code_element = soup_add.find('span', itemprop='postalCode')
                if postal_code_element:
                    address += postal_code_element.text.strip() + ' '
            except:
                pass

            try:
                locality_element = soup_add.find('span', itemprop='addressLocality')
                if locality_element:
                    address += locality_element.text.strip() + ' '
            except:
                pass

            try:
                socialLinks_company = json_data['data']['stores']['data']['ProProfileStore']['data']['user'][
                    'socialLinks']

                for item_s in socialLinks_company:
                    if item_s['type'] == 'LINK_TYPE_FB':
                        facebook_company = item_s['trackedUrl']
                    elif item_s['type'] == 'LINK_TYPE_TWITTER':
                        twitter_company = item_s['trackedUrl']
                    elif item_s['type'] == 'LINK_TYPE_LINKEDIN':
                        linkedin_company = item_s['trackedUrl']
                    elif item_s['type'] == 'LINK_TYPE_BLOG':
                        blog_company = item_s['trackedUrl']
            except:
                continue

            street_address = ""
            addressLocality = ""
            addressRegion = ""
            postalCode = ""
            addressCountry = ""
            ratingValue = ''
            reviewCount = ''
            try:
                street_add = json_data['data']['stores']['data']['PageStore']['data']['pageDescriptionFooter']
                soup_s = BeautifulSoup(street_add, 'html.parser')
                script_tag = soup_s.find('runnable', type='application/ld+json')
                if script_tag:
                    json_data_script = script_tag.string.strip()
                    data = json.loads(json_data_script)
                    for item_add in data:
                        if 'address' in item_add:
                            street_address = item_add['address'].get('streetAddress')
                            addressLocality = item_add['address'].get('addressLocality')
                            addressRegion = item_add['address'].get('addressRegion')
                            postalCode = item_add['address'].get('postalCode')
                            addressCountry = item_add['address'].get('addressCountry')
                        if 'aggregateRating' in item_add:
                            ratingValue = item_add['aggregateRating'].get('ratingValue')
                            reviewCount = item_add['aggregateRating'].get('reviewCount')

            except:
                continue
            try:
                proyectos_company = soup.find('h2', attrs={'id': 'projects-label'}).text.strip().replace(
                    ' Proyectos', "").replace(' Proyecto', '')
            except:
                proyectos_company = None
            if not postalCode:
                postalCode = \
                    json_data['data']['stores']['data']['ProProfileStore']['data']['user']['professional'][
                        'zip']
            if not addressLocality:
                addressLocality = \
                    json_data['data']['stores']['data']['ProProfileStore']['data']['user']['professional'][
                        'city']

            if not addressCountry:
                addressCountry = \
                    json_data['data']['stores']['data']['FooterStore']['data']['footerInfo']['currentCcTld'][
                        'countryNativeName']
            datas.append(
                [name_company, telephone_company, www_company, costEstimate_company, address, street_address,
                 addressLocality, addressRegion, postalCode, addressCountry,
                 facebook_company, twitter_company, linkedin_company, blog_company, service_company,
                 category_company, catalog, ratingValue, reviewCount, proyectos_company])
            writer.writerows(datas)
    print(f'Записан {group}.csv')


if __name__ == '__main__':
    parsing()
