import re
import json

class UniversalNuxtExtractor:
    """Универсальный экстрактор для любых товаров Hotline"""
    
    def __init__(self):
        self.variable_mapping = {}
    
    def extract_product_data(self, html_content):
        """Извлекает данные о любом товаре"""
        
        # Исправляем HTML если нужно
        if 'script>window.__NUXT__' in html_content and not '<script>' in html_content:
            html_content = html_content.replace('script>', '<script>')
        
        # Находим NUXT script
        script_content = self._find_nuxt_script(html_content)
        if not script_content:
            return None
        
        # Извлекаем переменные из конца функции
        variables = self._extract_variables(script_content)
        
        # Ищем данные через универсальные паттерны
        product_data = self._extract_universal_data(script_content, variables)
        
        return product_data
    
    def _find_nuxt_script(self, html_content):
        """Находит NUXT script"""
        patterns = [
            r'<script[^>]*>(.*?window\.__NUXT__.*?)</script>',
            r'window\.__NUXT__\s*=\s*\([^;]+\);?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html_content, re.DOTALL)
            if match:
                return match.group(0)
        return None
    
    def _extract_variables(self, script_content):
        """Извлекает переменные из конца функции"""
        # Ищем паттерн }(null,false,true,"",0,"текст",...))
        pattern = r'\}\s*\(([^)]+)\)\s*[;)]'
        match = re.search(pattern, script_content)
        
        if not match:
            return {}
        
        params_str = match.group(1)
        params = self._parse_function_params(params_str)
        
        # Создаем маппинг переменных
        variables = {}
        alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_$'
        
        for i, param in enumerate(params):
            if i < len(alphabet):
                var_name = alphabet[i]
            else:
                # Для aa, ab, ac, ...
                first_idx = (i - len(alphabet)) // len(alphabet)
                second_idx = (i - len(alphabet)) % len(alphabet)
                var_name = alphabet[first_idx] + alphabet[second_idx]
            
            variables[var_name] = param
        
        return variables
    
    def _parse_function_params(self, params_str):
        """Парсит параметры функции"""
        params = []
        current = ""
        depth = 0
        in_string = False
        quote_char = None
        
        i = 0
        while i < len(params_str):
            char = params_str[i]
            
            if not in_string:
                if char in ['"', "'"]:
                    in_string = True
                    quote_char = char
                elif char in ['[', '(', '{']:
                    depth += 1
                elif char in [']', ')', '}']:
                    depth -= 1
                elif char == ',' and depth == 0:
                    params.append(current.strip())
                    current = ""
                    i += 1
                    continue
            else:
                if char == quote_char and (i == 0 or params_str[i-1] != '\\'):
                    in_string = False
                    quote_char = None
            
            current += char
            i += 1
        
        if current.strip():
            params.append(current.strip())
        
        return params
    
    def _extract_universal_data(self, script_content, variables):
        """Извлекает данные через универсальные паттерны"""
        result = {}
        
        # 1. Ищем основные поля через стандартные паттерны
        basic_patterns = {
            'title': [
                r'"title":"([^"]+)"',
                r'title:"([^"]+)"'
            ],
            'vendor_title': [
                r'"vendor":\s*\{[^}]*"title":"([^"]+)"',
                r'vendor:\s*\{[^}]*title:"([^"]+)"'
            ],
            'min_price': [
                r'"minPrice":(\d+(?:\.\d+)?)',
                r'minPrice:(\d+(?:\.\d+)?)'
            ],
            'max_price': [
                r'"maxPrice":(\d+(?:\.\d+)?)',
                r'maxPrice:(\d+(?:\.\d+)?)'
            ],
            'offer_count': [
                r'"offerCount":(\d+)',
                r'offerCount:(\d+)',
                r'"totalCount":(\d+)'
            ],
            'product_id': [
                r'"_id":"?(\d+)"?',
                r'_id:"?(\d+)"?'
            ]
        }
        
        for field, patterns in basic_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, script_content)
                if match:
                    value = match.group(1)
                    # Конвертируем числа
                    if field in ['min_price', 'max_price', 'offer_count', 'product_id']:
                        try:
                            result[field] = int(float(value))
                        except ValueError:
                            result[field] = value
                    else:
                        result[field] = value
                    break
        
        # 2. Ищем изображения
        image_patterns = [
            r'"imageLinks":\s*\[([^\]]+)\]',
            r'imageLinks:\s*\[([^\]]+)\]'
        ]
        
        for pattern in image_patterns:
            match = re.search(pattern, script_content)
            if match:
                result['images'] = self._extract_image_urls(match.group(1))
                break
        
        # 3. Ищем характеристики
        specs_patterns = [
            r'"techShortSpecificationsList":\s*\[([^\]]+)\]',
            r'techShortSpecificationsList:\s*\[([^\]]+)\]'
        ]
        
        for pattern in specs_patterns:
            match = re.search(pattern, script_content)
            if match:
                result['specifications'] = self._extract_specifications(match.group(1))
                break
        
        # 4. Пытаемся декодировать переменные для недостающих данных
        if variables:
            result['decoded_variables'] = self._decode_important_variables(variables)
        
        # 5. Извлекаем URL и категорию
        url_patterns = [
            r'"url":"([^"]+)"',
            r'url:"([^"]+)"'
        ]
        
        for pattern in url_patterns:
            match = re.search(pattern, script_content)
            if match:
                result['url'] = match.group(1)
                # Извлекаем категорию из URL
                if '/bt/' in match.group(1):
                    category_match = re.search(r'/bt/([^/]+)/', match.group(1))
                    if category_match:
                        result['category'] = category_match.group(1)
                break
        
        return result if result else None
    
    def _extract_image_urls(self, images_str):
        """Извлекает URL изображений"""
        image_urls = []
        
        # Ищем все URL изображений
        url_patterns = [
            r'"(https?://[^"]+\.jpg)"',
            r'"(/img/[^"]+\.jpg)"',
            r'"thumb":"([^"]+)"',
            r'"basic":"([^"]+)"',
            r'"small":"([^"]+)"',
            r'"big":"([^"]+)"'
        ]
        
        for pattern in url_patterns:
            matches = re.findall(pattern, images_str)
            for match in matches:
                if match not in image_urls:
                    image_urls.append(match)
        
        return image_urls
    
    def _extract_specifications(self, specs_str):
        """Извлекает технические характеристики"""
        specs = []
        
        # Ищем пары ключ-значение
        key_value_patterns = [
            r'"key":"([^"]+)"[^}]*"value":"([^"]+)"',
            r'key:"([^"]+)"[^}]*value:"([^"]+)"'
        ]
        
        for pattern in key_value_patterns:
            matches = re.findall(pattern, specs_str)
            for key, value in matches:
                specs.append({'key': key, 'value': value})
        
        return specs
    
    def _decode_important_variables(self, variables):
        """Пытается декодировать важные переменные"""
        decoded = {}
        
        for var_name, value in variables.items():
            # Убираем кавычки если есть
            clean_value = value.strip('"\'')
            
            # Ищем осмысленные значения
            if self._looks_like_title(clean_value):
                decoded[f'{var_name}_title'] = clean_value
            elif self._looks_like_price(clean_value):
                decoded[f'{var_name}_price'] = clean_value
            elif self._looks_like_url(clean_value):
                decoded[f'{var_name}_url'] = clean_value
            elif self._looks_like_category(clean_value):
                decoded[f'{var_name}_category'] = clean_value
        
        return decoded
    
    def _looks_like_title(self, value):
        """Проверяет, похоже ли значение на название товара"""
        if not isinstance(value, str) or len(value) < 10:
            return False
        
        # Содержит буквы и цифры, но не только цифры
        has_letters = bool(re.search(r'[a-zA-Zа-яА-Я]', value))
        has_numbers = bool(re.search(r'\d', value))
        not_only_numbers = not value.replace(' ', '').replace('-', '').isdigit()
        
        return has_letters and not_only_numbers
    
    def _looks_like_price(self, value):
        """Проверяет, похоже ли значение на цену"""
        try:
            price = float(value)
            return 100 <= price <= 1000000  # Разумный диапазон цен
        except:
            return False
    
    def _looks_like_url(self, value):
        """Проверяет, похоже ли значение на URL"""
        return isinstance(value, str) and ('/' in value or '.html' in value or 'http' in value)
    
    def _looks_like_category(self, value):
        """Проверяет, похоже ли значение на категорию"""
        return (isinstance(value, str) and 
                len(value) > 3 and 
                '-' in value and 
                not value.startswith('http'))

# Простая функция для использования
def extract_product_info(html_content):
    """Простая функция для извлечения данных о товаре"""
    extractor = UniversalNuxtExtractor()
    return extractor.extract_product_data(html_content)

# Главная функция
def main():
    # Ваш HTML контент (исправляем тег)
    html_content = """
    <script>window.__NUXT__=(function(a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w,x,y,z,A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z,_,$,aa,ab,ac,ad,ae,af,ag,ah,ai,aj,ak,al,am,an,ao,ap,aq,ar,as,at,au,av,aw,ax,ay,az,aA,aB,aC,aD,aE,aF,aG,aH,aI,aJ,aK,aL,aM,aN,aO,aP,aQ,aR,aS,aT,aU,aV,aW,aX,aY,aZ,a_,a$,ba,bb,bc,bd,be,bf,bg,bh,bi,bj,bk,bl,bm,bn,bo,bp,bq,br,bs,bt,bu,bv,bw,bx,by,bz,bA,bB,bC,bD,bE,bF,bG,bH,bI,bJ,bK,bL,bM,bN,bO,bP,bQ,bR,bS,bT,bU,bV,bW,bX,bY){aK[0]="bt-vytyazhki";aK[1]=aL;return {layout:"default",data:[{pathSegments:aK,pageType:aM,pageState:aN}],fetch:{},error:a,state:{detectLanguage:"uk",pathSegments:aK,uniqId:"037cb9ad7e8bb84979c2dd6f3dc537c2",unlocalizedPath:aj,initiallyLoaded:b,isMobile:b,isPhone:b,isUserBot:b,isUserBotChecked:b,breadcrumbs:{crumbs:[{url:"\u002Fbt\u002F",id:548,dropList:[],title:"Побутова техніка",type:"mainSection",isLastItem:b,trackingIdObject:{"track-id":"global-8",trackingType:ak},trackingIdObjectDropList:d},{url:"\u002Fbt\u002Fkrupnaya-bytovaya-tehnika\u002F",id:aO,dropList:[{weight_new:B,path:aP,menu:H,title:"Пральні та сушильні машини",id:577,hl_tid:461,url:"\u002Fbt\u002Fstiralnye-i-sushilnye-mashiny\u002F",hl_path:aP,groupId:a,isActive:b},{weight_new:T,path:aQ,menu:H,title:"Холодильники",id:563,hl_tid:486,url:"\u002Fbt\u002Fholodilniki\u002F",hl_path:aQ,groupId:a,isActive:b},{weight_new:U,path:d,menu:H,title:"Морозильні камери",id:3545,hl_tid:e,url:"\u002Fbt\u002Fholodilniki\u002F618\u002F",hl_path:d,groupId:a,isActive:b},{weight_new:C,path:aR,menu:H,title:"Посудомийні машини",id:554,hl_tid:478,url:"\u002Fbt\u002Fposudomoechnye-mashiny\u002F",hl_path:aR,groupId:a,isActive:b},{weight_new:aS,path:aT,menu:H,title:"Кухонні плити",id:570,hl_tid:474,url:"\u002Fbt\u002Fkuhonnye-plity-i-poverhnosti\u002F",hl_path:aT,groupId:a,isActive:b},{weight_new:aU,path:"varochnye-poverhnosti",menu:H,title:"Варильні поверхні",id:3500,hl_tid:i,url:"\u002Fbt\u002Fvarochnye-poverhnosti\u002F",hl_path:"varochnye-poverhnosti_3500",groupId:a,isActive:b},{weight_new:aV,path:aW,menu:H,title:al,id:av,hl_tid:456,url:aw,hl_path:aW,groupId:a,isActive:b},{weight_new:45,path:aX,menu:H,title:"Духовки",id:576,hl_tid:511,url:"\u002Fbt\u002Fduhovki\u002F",hl_path:aX,groupId:a,isActive:b},{weight_new:50,path:"vinnye-shkafy",menu:H,title:"Холодильники-вітрини",id:720,hl_tid:971,url:"\u002Fbt\u002Fvinnye-shkafy\u002F",hl_path:"holodilniki-vinnye-shkafy",groupId:a,isActive:b},{weight_new:aY,path:aZ,menu:H,title:"Аксесуари для пральних машин",id:648,hl_tid:546,url:"\u002Fbt\u002Faksessuary-dlya-stiralnyh-mashin\u002F",hl_path:aZ,groupId:a,isActive:b},{weight_new:65,path:a_,menu:H,title:a$,id:3189,hl_tid:i,url:ba,hl_path:a_,groupId:a,isActive:b}],title:"Велика побутова техніка",type:"underSections",isLastItem:b,trackingIdObject:d,trackingIdObjectDropList:{"track-id":"global-9",trackingType:ak},isDropList:c},{url:aw,id:av,dropList:[],title:al,type:"section",isLastItem:b,trackingIdObject:{"track-id":"global-11",trackingType:ak},trackingIdObjectDropList:d},{url:"\u002Fbt\u002Fvytyazhki\u002F298811\u002F",id:I,dropList:[],type:ax,title:D,isLastItem:b,trackingIdObject:{"track-id":"global-12",trackingType:ak},trackingIdObjectDropList:d},{url:aj,id:d,type:"card",dropList:[],title:ay,isLastItem:c,trackingIdObject:d,trackingIdObjectDropList:d}]},compare:{listsTitles:{},lists:[],cards:{},listsCardsReferens:{},isLock:c},location:{city:{_id:187,name:"Киев",nameTranslate:az,latitude:50.4501,longitude:30.5234,region:{name:az,nameTranslate:az,__typename:"Region"}},region:{_id:i},regionMode:i,defaultLocation:b},menuMain:{menuItems:{},menuState:{},isShowMenu:b,isShowMenuAlways:b,isReadyData:b,isShowPreloader:b},metaData:{title:bb,keywords:"Minola HBI 6473 BL GLASS 800 LED LINE, купити Minola HBI 6473 BL GLASS 800 LED LINE, ціна Minola HBI 6473 BL GLASS 800 LED LINE",description:bc,url:bd,image:"https:\u002F\u002Fhotline.ua\u002Fimg\u002Ftx\u002F510\u002F5107419105.jpg",canonical:bd,robots:d,alternateLinkUa:d,alternateLinkRu:d},modal:{name:d},myLists:{custom:[],bookmark:{}},pageType:{state:aN,token:"f4cd65ef-925b-46c6-a2e3-a7d39caf3019",type:aM,pathForDuplicateCatalog:a},popup:{open:b,data:{}},productsInOneShop:{products:[],productsIds:[],loading:b},productWishList:{productWishList:[],productIds:[]},user:{token:a,_id:a,GA_clientId:a,pic:a,afterLoginPath:a},zoomGallery:{isGalleryIn:a,itemActiveNum:a,items:a},vendors:{vendor:a,vendorMessage:a,catalogsWithReviews:[],catalogsWithQuestions:[],selectedCatalog:e,subscribedToReviews:b,subscribedToReplies:b},sr:{loading:b,query:d,countProducts:e,countShops:e,sections:[],vendors:[],vendorIds:[],paginationInfo:{},searchSelectValue:"allSite",activeFormat:"column",firmsSearch:[],productsSearch:[]},section:{popularProductPage:i,popularProductOrder:i,bannerAdvertising:{},guides:{howToChoice:[],guides:[]},menu:[],popularProduct:{products:[],count:e}},profile:{activeProductsViewFormat:E,sidebarMenuPrivate:E,sidebarMenuPublic:E,sidebarMenuGuest:E,personalData:E,ukMonths:["січня","лютого","березня","квітня","травня","червня","липня","серпня","вересня","жовтня","листопада","грудня"],ruMonths:["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"],pageTitle:E,compareListsLoading:c},product:{_id:be,isPaymentHidden:b,isFiltersCollapsed:b,bannerAdvertising:{},chart:{id:a,priceUAH:[],priceUSD:[],popularity:[],quantity:[]},crossSellingProducts:[],map:{loading:b,listLoading:b,visiblePoints:["available","delivery"],sortParams:{sort:"distance"},offersWithPoints:[],selectedOffer:a,showStoresOfferId:a,selectedStore:a,directionsPopup:{visible:b,position:a,data:a}},offers:{edges:[{node:{_id:"13682756336",condition:j,conditionId:e,conversionUrl:"\u002Fgo\u002Fprice\u002F13682756336\u002F",descriptionFull:am,descriptionShort:"Minola Витяжка Minola HBI 6473 BL GLASS 800 LED Line (5905538402003)",firmId:1531,firmLogo:"\u002Fimg\u002Fyp\u002F1531_.jpg?v=5",firmTitle:"ELMIR.UA",firmExtraInfo:{reviewsCount:bf,reviewsCountShortPeriod:bf,rating:an,isFirmNew:b,clicksAmount:859,isFavorite:b,isOfficial:b,officialFirmLink:a,officialFirmImage:a,vendorHint:a,firmDateStatusNew:a,website:"elmir.ua"},guaranteeTerm:z,guaranteeTermName:s,guaranteeType:a,hasBid:c,historyId:488924386,payment:{"pay-card":{type:v,attributes:{discount:[w]},enabled:c},"non-vat":{type:F,attributes:[],enabled:c},"card-in-shop":{type:G,attributes:[],enabled:c},"cash-on-delivery":{type:t,attributes:[],enabled:c}},price:q,reviewsNegativeNumber:56,reviewsPositiveNumber:194,bid:a,shipping:"3-6 днів",delivery:{deliveryMethods:[{id:22441,code:o,name:p,cost:f,pickupPoints:[]},{id:65691,code:aA,name:aB,cost:f,pickupPoints:[]}],hasFreeDelivery:b,isSameCity:b,name:bg,countryCodeFirm:k,__typename:l},sortPlace:{price_desc:Y,price_asc:V,shops_desc:ac,guarantee_desc:ad,payments_desc:ae},__typename:m,visible:c},__typename:n},{node:{_id:"13687738811",condition:j,conditionId:e,conversionUrl:"\u002Fgo\u002Fprice\u002F13687738811\u002F",descriptionFull:A,descriptionShort:"Minola HBI 6473 BL GLASS 800 LED Line (HBI6473BLGLASS800LEDLine)",firmId:20464,firmLogo:"\u002Fimg\u002Fyp\u002F20464_.jpg?v=1",firmTitle:"ЭЛМАГ",firmExtraInfo:{reviewsCount:M,reviewsCountShortPeriod:M,rating:bh,isFirmNew:b,clicksAmount:3023,isFavorite:b,isOfficial:b,officialFirmLink:a,officialFirmImage:a,vendorHint:a,firmDateStatusNew:a,website:"elmag.com.ua"},guaranteeTerm:a,guaranteeTermName:a,guaranteeType:a,hasBid:c,historyId:489557760,payment:{"card-card":{type:aC,attributes:{fee:[w]},enabled:c},"non-vat":{type:F,attributes:[],enabled:c},"card-in-shop":{type:G,attributes:[],enabled:c},"cash-on-delivery":{type:t,attributes:[],enabled:c}},price:q,reviewsNegativeNumber:B,reviewsPositiveNumber:W,bid:a,shipping:a,delivery:{deliveryMethods:[{id:35625,code:a,name:x,cost:d,pickupPoints:[bi]},{id:35623,code:y,name:"кур'єром ЭЛМАГ",cost:bj,pickupPoints:[]},{id:35624,code:o,name:p,cost:bk,pickupPoints:[]}],hasFreeDelivery:b,isSameCity:c,name:r,countryCodeFirm:k,__typename:l},sortPlace:{price_desc:ac,price_asc:ae,shops_desc:X,guarantee_desc:Q,payments_desc:Z},__typename:m,visible:c},__typename:n},{node:{_id:"13689808546",condition:j,conditionId:e,conversionUrl:"\u002Fgo\u002Fprice\u002F13689808546\u002F",descriptionFull:am,descriptionShort:bl,firmId:20807,firmLogo:"\u002Fimg\u002Fyp\u002F20807_.jpg?v=5",firmTitle:"Техномастер",firmExtraInfo:{reviewsCount:R,reviewsCountShortPeriod:B,rating:a,isFirmNew:b,clicksAmount:675,isFavorite:b,isOfficial:b,officialFirmLink:a,officialFirmImage:a,vendorHint:a,firmDateStatusNew:a,website:"tehnomaster.com"},guaranteeTerm:z,guaranteeTermName:s,guaranteeType:a,hasBid:b,historyId:489740049,payment:{"pay-card":{type:v,attributes:{discount:[w]},enabled:c},vat:{type:J,attributes:[],enabled:c},"card-in-shop":{type:G,attributes:[],enabled:c},"cash-on-delivery":{type:t,attributes:[],enabled:c}},price:q,reviewsNegativeNumber:i,reviewsPositiveNumber:N,bid:a,shipping:a,delivery:{deliveryMethods:[{id:39181,code:y,name:"кур'єром Техномастер",cost:ao,pickupPoints:[]},{id:39183,code:a,name:x,cost:d,pickupPoints:[bi]},{id:39182,code:o,name:p,cost:bk,pickupPoints:[]}],hasFreeDelivery:c,isSameCity:c,name:r,countryCodeFirm:k,__typename:l},sortPlace:{price_desc:M,price_asc:ad,shops_desc:M,guarantee_desc:M,payments_desc:_},__typename:m,visible:c},__typename:n},{node:{_id:"13694595033",condition:j,conditionId:e,conversionUrl:"\u002Fgo\u002Fprice\u002F13694595033\u002F",descriptionFull:aD,descriptionShort:A,firmId:1111,firmLogo:"\u002Fimg\u002Fyp\u002F1111_.jpg?v=1",firmTitle:"F.ua „ТОЙ САМИЙ“ магазин",firmExtraInfo:{reviewsCount:bm,reviewsCountShortPeriod:bm,rating:aE,isFirmNew:b,clicksAmount:1145,isFavorite:b,isOfficial:b,officialFirmLink:a,officialFirmImage:a,vendorHint:a,firmDateStatusNew:a,website:"f.ua"},guaranteeTerm:C,guaranteeTermName:s,guaranteeType:u,hasBid:b,historyId:489380654,payment:{"pay-card":{type:v,attributes:[],enabled:c},vat:{type:J,attributes:[],enabled:c},"card-in-shop":{type:G,attributes:[],enabled:c}},price:ap,reviewsNegativeNumber:aE,reviewsPositiveNumber:V,bid:a,shipping:af,delivery:{deliveryMethods:[{id:17545,code:o,name:p,cost:f,pickupPoints:[]},{id:17542,code:a,name:x,cost:d,pickupPoints:["Київ, вул. Машинобудівна, 44 (Магазин в районі м. Берестейська)","Київ, вул. Анни Ахматової 30, (м.Позняки) (Позняки)","Київ, вул. Героїв полку Азов, 12 (f.ua)"]},{id:17543,code:y,name:"кур'єром F.ua „ТОЙ САМИЙ“ магазин",cost:"95 грн",pickupPoints:[]}],hasFreeDelivery:b,isSameCity:c,name:r,countryCodeFirm:k,__typename:l},sortPlace:{price_desc:i,price_asc:ag,shops_desc:S,guarantee_desc:R,payments_desc:ah},__typename:m,visible:c},__typename:n},{node:{_id:"13697919501",condition:j,conditionId:e,conversionUrl:"\u002Fgo\u002Fprice\u002F13697919501\u002F",descriptionFull:"Кухонная вытяжка Minola HBI 6473 BL GLASS 800 LED Line",descriptionShort:"Minola Кухонная вытяжка Minola HBI 6473 BL GLASS 800 LED Line",firmId:10933,firmLogo:"\u002Fimg\u002Fyp\u002F10933_.jpg",firmTitle:"Элдом",firmExtraInfo:{reviewsCount:S,reviewsCountShortPeriod:S,rating:aV,isFirmNew:b,clicksAmount:436,isFavorite:b,isOfficial:b,officialFirmLink:a,officialFirmImage:a,vendorHint:a,firmDateStatusNew:a,website:"eldom.com.ua"},guaranteeTerm:a,guaranteeTermName:a,guaranteeType:a,hasBid:b,historyId:490905570,payment:{"pay-card":{type:v,attributes:[],enabled:c},"non-vat":{type:F,attributes:[],enabled:c},"cash-on-delivery":{type:t,attributes:[],enabled:c}},price:q,reviewsNegativeNumber:i,reviewsPositiveNumber:Z,bid:a,shipping:a,delivery:{deliveryMethods:[{id:11883,code:y,name:"кур'єром Элдом",cost:f,pickupPoints:[]},{id:11882,code:o,name:p,cost:f,pickupPoints:[]}],hasFreeDelivery:b,isSameCity:b,name:"з Дніпра",countryCodeFirm:k,__typename:l},sortPlace:{price_desc:Q,price_asc:ai,shops_desc:Q,guarantee_desc:K,payments_desc:T},__typename:m,visible:c},__typename:n},{node:{_id:"13703473747",condition:j,conditionId:e,conversionUrl:"\u002Fgo\u002Fprice\u002F13703473747\u002F",descriptionFull:aD,descriptionShort:A,firmId:14930,firmLogo:"\u002Fimg\u002Fyp\u002F14930_v2_150.png?v=1",firmTitle:"COMFY.UA",firmExtraInfo:{reviewsCount:bn,reviewsCountShortPeriod:115,rating:bo,isFirmNew:b,clicksAmount:5022,isFavorite:b,isOfficial:b,officialFirmLink:a,officialFirmImage:a,vendorHint:a,firmDateStatusNew:a,website:"comfy.ua"},guaranteeTerm:a,guaranteeTermName:a,guaranteeType:u,hasBid:b,historyId:489425960,payment:{"pay-card":{type:v,attributes:{discount:[w]},enabled:c},"card-in-shop":{type:G,attributes:[],enabled:c}},price:q,reviewsNegativeNumber:72,reviewsPositiveNumber:aU,bid:a,shipping:"сьогодні (при замовленні до 19:00)",delivery:{deliveryMethods:[{id:65305,code:o,name:p,cost:f,pickupPoints:[]}],hasFreeDelivery:b,isSameCity:c,name:r,countryCodeFirm:k,__typename:l},sortPlace:{price_desc:ah,price_asc:z,shops_desc:Y,guarantee_desc:$,payments_desc:V},__typename:m,visible:c},__typename:n},{node:{_id:"13736320781",condition:j,conditionId:e,conversionUrl:"\u002Fgo\u002Fprice\u002F13736320781\u002F",descriptionFull:"Витяжка повновбудовувана MINOLA HBI 6473 BL GLASS 800 LED Line",descriptionShort:"MINOLA Витяжка повновбудовувана MINOLA HBI 6473 BL GLASS 800 LED Line",firmId:24079,firmLogo:"\u002Fimg\u002Fyp\u002F24079_.jpg?v=6",firmTitle:"ТЕХНОточка",firmExtraInfo:{reviewsCount:aa,reviewsCountShortPeriod:aa,rating:aF,isFirmNew:b,clicksAmount:4302,isFavorite:b,isOfficial:b,officialFirmLink:a,officialFirmImage:a,vendorHint:a,firmDateStatusNew:a,website:"tt.ua"},guaranteeTerm:z,guaranteeTermName:s,guaranteeType:u,hasBid:b,historyId:489504560,payment:{"pay-card":{type:v,attributes:{discount:[w]},enabled:c},vat:{type:J,attributes:[],enabled:c},"card-in-shop":{type:G,attributes:[],enabled:c},"cash-on-delivery":{type:t,attributes:[],enabled:c}},price:q,reviewsNegativeNumber:R,reviewsPositiveNumber:M,bid:a,shipping:af,delivery:{deliveryMethods:[{id:66530,code:a,name:x,cost:f,pickupPoints:[bp]},{id:66918,code:a,name:x,cost:f,pickupPoints:[bp]},{id:66532,code:aA,name:aB,cost:"125 грн",pickupPoints:[]},{id:66531,code:y,name:"кур'єром ТЕХНОточка",cost:bj,pickupPoints:[]},{id:66528,code:o,name:p,cost:"250 грн",pickupPoints:[]}],hasFreeDelivery:b,isSameCity:c,name:r,countryCodeFirm:k,__typename:l},sortPlace:{price_desc:_,price_asc:ah,shops_desc:z,guarantee_desc:V,payments_desc:Y},__typename:m,visible:c},__typename:n},{node:{_id:"13741107118",condition:j,conditionId:e,conversionUrl:"\u002Fgo\u002Fprice\u002F13741107118\u002F",descriptionFull:am,descriptionShort:"Minola Витяжка Minola HBI 6473 BL GLASS 800 LED Line (AKУТ000004537)",firmId:2476,firmLogo:"\u002Fimg\u002Fyp\u002F2476_v2_150.png?v=1",firmTitle:"Rozetka.ua",firmExtraInfo:{reviewsCount:bq,reviewsCountShortPeriod:bq,rating:aY,isFirmNew:b,clicksAmount:5077,isFavorite:b,isOfficial:b,officialFirmLink:a,officialFirmImage:a,vendorHint:a,firmDateStatusNew:a,website:"rozetka.com.ua"},guaranteeTerm:C,guaranteeTermName:s,guaranteeType:u,hasBid:c,historyId:489368639,payment:{"pay-card":{type:v,attributes:{discount:[w]},enabled:c},vat:{type:J,attributes:[],enabled:c},"cash-on-delivery":{type:t,attributes:[],enabled:c}},price:q,reviewsNegativeNumber:165,reviewsPositiveNumber:an,bid:a,shipping:a,delivery:{deliveryMethods:[],hasFreeDelivery:b,isSameCity:c,name:r,countryCodeFirm:k,__typename:l},sortPlace:{price_desc:V,price_asc:ac,shops_desc:ae,guarantee_desc:O,payments_desc:X},__typename:m,visible:c},__typename:n},{node:{_id:"13741890640",condition:j,conditionId:e,conversionUrl:"\u002Fgo\u002Fprice\u002F13741890640\u002F",descriptionFull:br,descriptionShort:bs,firmId:23876,firmLogo:"\u002Fimg\u002Fyp\u002F23876_v2_150.png?v=16",firmTitle:"АйТіФрі",firmExtraInfo:{reviewsCount:bt,reviewsCountShortPeriod:217,rating:83,isFirmNew:b,clicksAmount:1172,isFavorite:b,isOfficial:b,officialFirmLink:a,officialFirmImage:a,vendorHint:a,firmDateStatusNew:a,website:"itfree.com.ua"},guaranteeTerm:z,guaranteeTermName:s,guaranteeType:u,hasBid:b,historyId:496732306,payment:{"card-card":{type:aC,attributes:{fee:[w]},enabled:c},"non-vat":{type:F,attributes:[],enabled:c},"cash-on-delivery":{type:t,attributes:[],enabled:c}},price:6698.5,reviewsNegativeNumber:aa,reviewsPositiveNumber:186,bid:a,shipping:"сьогодні",delivery:{deliveryMethods:[{id:18589,code:o,name:p,cost:f,pickupPoints:[]},{id:27299,code:aq,name:ar,cost:f,pickupPoints:[]},{id:27301,code:aA,name:aB,cost:f,pickupPoints:[]},{id:27414,code:a,name:x,cost:d,pickupPoints:["Київ, вул. Здолбунівська 6 (ITFREE)"]},{id:18588,code:y,name:"кур'єром АйТіФрі",cost:"199 грн",pickupPoints:[]}],hasFreeDelivery:b,isSameCity:c,name:r,countryCodeFirm:k,__typename:l},sortPlace:{price_desc:U,price_asc:S,shops_desc:Z,guarantee_desc:ah,payments_desc:M},__typename:m,visible:c},__typename:n},{node:{_id:"13744839820",condition:j,conditionId:e,conversionUrl:"\u002Fgo\u002Fprice\u002F13744839820\u002F",descriptionFull:A,descriptionShort:A,firmId:1396,firmLogo:"\u002Fimg\u002Fyp\u002F1396_.jpg?v=2",firmTitle:"TEHNOHATA.UA",firmExtraInfo:{reviewsCount:i,reviewsCountShortPeriod:i,rating:a,isFirmNew:b,clicksAmount:310,isFavorite:b,isOfficial:b,officialFirmLink:a,officialFirmImage:a,vendorHint:a,firmDateStatusNew:a,website:"tehnohata.ua"},guaranteeTerm:z,guaranteeTermName:s,guaranteeType:u,hasBid:b,historyId:488614238,payment:{"pay-card":{type:v,attributes:{discount:[w]},enabled:c},vat:{type:J,attributes:[],enabled:c},"card-in-shop":{type:G,attributes:[],enabled:c},"cash-on-delivery":{type:t,attributes:[],enabled:c}},price:q,reviewsNegativeNumber:e,reviewsPositiveNumber:i,bid:a,shipping:a,delivery:{deliveryMethods:[{id:53512,code:o,name:p,cost:f,pickupPoints:[]},{id:10495,code:a,name:x,cost:d,pickupPoints:["Київ, просп. Відрадний 95 (Крапка 1)"]},{id:10492,code:y,name:"кур'єром TEHNOHATA.UA",cost:"350 грн",pickupPoints:[]}],hasFreeDelivery:b,isSameCity:c,name:r,countryCodeFirm:k,__typename:l},sortPlace:{price_desc:C,price_asc:Q,shops_desc:C,guarantee_desc:T,payments_desc:$},__typename:m,visible:c},__typename:n},{node:{_id:"13753304913",condition:j,conditionId:e,conversionUrl:"\u002Fgo\u002Fprice\u002F13753304913\u002F",descriptionFull:am,descriptionShort:bl,firmId:32556,firmLogo:"\u002Fimg\u002Fyp\u002F32556_v2_150.png?v=4",firmTitle:"Кухня",firmExtraInfo:{reviewsCount:L,reviewsCountShortPeriod:L,rating:a,isFirmNew:b,clicksAmount:1556,isFavorite:b,isOfficial:b,officialFirmLink:a,officialFirmImage:a,vendorHint:a,firmDateStatusNew:a,website:"kuhnya.net"},guaranteeTerm:a,guaranteeTermName:a,guaranteeType:a,hasBid:c,historyId:496650819,payment:{"pay-card":{type:v,attributes:{discount:[w]},enabled:c},"non-vat":{type:F,attributes:[],enabled:c},"cash-on-delivery":{type:t,attributes:[],enabled:c}},price:q,reviewsNegativeNumber:i,reviewsPositiveNumber:i,bid:a,shipping:a,delivery:{deliveryMethods:[{id:39803,code:y,name:"кур'єром Кухня",cost:f,pickupPoints:[]},{id:39804,code:o,name:p,cost:f,pickupPoints:[]}],hasFreeDelivery:b,isSameCity:c,name:r,countryCodeFirm:k,__typename:l},sortPlace:{price_desc:z,price_asc:Y,shops_desc:V,guarantee_desc:C,payments_desc:ac},__typename:m,visible:c},__typename:n},{node:{_id:"13764432967",condition:j,conditionId:e,conversionUrl:"\u002Fgo\u002Fprice\u002F13764432967\u002F",descriptionFull:"Витяжка вбудована Minola HBI 6473 BL GLASS 800 LED LINE",descriptionShort:"Minola Витяжка вбудована Minola HBI 6473 BL GLASS 800 LED LINE",firmId:33937,firmLogo:"\u002Fimg\u002Fyp\u002F33937_.jpg?v=1",firmTitle:"TehnoAge",firmExtraInfo:{reviewsCount:bu,reviewsCountShortPeriod:bu,rating:bv,isFirmNew:b,clicksAmount:1006,isFavorite:b,isOfficial:b,officialFirmLink:a,officialFirmImage:a,vendorHint:a,firmDateStatusNew:a,website:"tehnoage.com.ua"},guaranteeTerm:a,guaranteeTermName:a,guaranteeType:a,hasBid:b,historyId:491978793,payment:[],price:bw,reviewsNegativeNumber:T,reviewsPositiveNumber:33,bid:a,shipping:a,delivery:{deliveryMethods:[{id:44045,code:y,name:"кур'єром TehnoAge",cost:f,pickupPoints:[]},{id:44046,code:o,name:p,cost:f,pickupPoints:[]}],hasFreeDelivery:b,isSameCity:c,name:r,countryCodeFirm:k,__typename:l},sortPlace:{price_desc:K,price_asc:i,shops_desc:U,guarantee_desc:ag,payments_desc:ag},__typename:m,visible:c},__typename:n},{node:{_id:"13782151715",condition:j,conditionId:e,conversionUrl:"\u002Fgo\u002Fprice\u002F13782151715\u002F",descriptionFull:A,descriptionShort:A,firmId:28401,firmLogo:"\u002Fimg\u002Fyp\u002F28401_v2_150.png?v=2",firmTitle:"AGD482",firmExtraInfo:{reviewsCount:i,reviewsCountShortPeriod:i,rating:a,isFirmNew:b,clicksAmount:221,isFavorite:b,isOfficial:b,officialFirmLink:a,officialFirmImage:a,vendorHint:a,firmDateStatusNew:a,website:"agd482.com.ua"},guaranteeTerm:z,guaranteeTermName:s,guaranteeType:u,hasBid:c,historyId:502528209,payment:{"pay-card":{type:v,attributes:{discount:[w]},enabled:c},"non-vat":{type:F,attributes:[],enabled:c},"card-in-shop":{type:G,attributes:[],enabled:c},"cash-on-delivery":{type:t,attributes:[],enabled:c}},price:q,reviewsNegativeNumber:e,reviewsPositiveNumber:i,bid:a,shipping:"сьогодні (при замовленні до 15:00)",delivery:{deliveryMethods:[{id:28580,code:o,name:p,cost:f,pickupPoints:[]}],hasFreeDelivery:b,isSameCity:b,name:"з Львова",countryCodeFirm:k,__typename:l},sortPlace:{price_desc:B,price_asc:N,shops_desc:O,guarantee_desc:ac,payments_desc:O},__typename:m,visible:c},__typename:n},{node:{_id:"13782622915",condition:j,conditionId:e,conversionUrl:"\u002Fgo\u002Fprice\u002F13782622915\u002F",descriptionFull:A,descriptionShort:A,firmId:23495,firmLogo:"\u002Fimg\u002Fyp\u002F23495_v2_150.png?v=15",firmTitle:"ВЕНКОН",firmExtraInfo:{reviewsCount:260,reviewsCountShortPeriod:259,rating:93,isFirmNew:b,clicksAmount:9703,isFavorite:b,isOfficial:b,officialFirmLink:a,officialFirmImage:a,vendorHint:a,firmDateStatusNew:a,website:"vencon.ua"},guaranteeTerm:Q,guaranteeTermName:s,guaranteeType:u,hasBid:c,historyId:491483337,payment:{"pay-card":{type:v,attributes:{discount:[w]},enabled:c},vat:{type:J,attributes:[],enabled:c},"card-in-shop":{type:G,attributes:[],enabled:c},"cash-on-delivery":{type:t,attributes:[],enabled:c}},price:q,reviewsNegativeNumber:L,reviewsPositiveNumber:251,bid:a,shipping:a,delivery:{deliveryMethods:[{id:19488,code:y,name:"кур'єром ВЕНКОН",cost:f,pickupPoints:[]},{id:53477,code:o,name:p,cost:f,pickupPoints:[]},{id:30816,code:a,name:x,cost:d,pickupPoints:["Київ, вул. Всеволода Змієнка  21 (Магазин #1 (біля ТРЦ Retroville))","Київ, вул. Микільсько-Слобідська 4В, оф. 167 (Магазин #2 (метро Лівобережна))"]}],hasFreeDelivery:c,isSameCity:c,name:r,countryCodeFirm:k,__typename:l},sortPlace:{price_desc:O,price_asc:L,shops_desc:i,guarantee_desc:X,payments_desc:i},__typename:m,visible:c},__typename:n},{node:{_id:"13786684137",condition:j,conditionId:e,conversionUrl:"\u002Fgo\u002Fprice\u002F13786684137\u002F",descriptionFull:"Витяжка вбудована Minola HBI 6473 BL Glass 800 LED Line",descriptionShort:"Minola Витяжка вбудована Minola HBI 6473 BL Glass 800 LED Line",firmId:20451,firmLogo:"\u002Fimg\u002Fyp\u002F20451_v2_150.png?v=5",firmTitle:"DENIKA.UA",firmExtraInfo:{reviewsCount:175,reviewsCountShortPeriod:174,rating:90,isFirmNew:b,clicksAmount:3277,isFavorite:b,isOfficial:b,officialFirmLink:a,officialFirmImage:a,vendorHint:a,firmDateStatusNew:a,website:"denika.ua"},guaranteeTerm:R,guaranteeTermName:s,guaranteeType:a,hasBid:b,historyId:503285287,payment:{"non-vat":{type:F,attributes:[],enabled:c},"cash-on-delivery":{type:t,attributes:[],enabled:c}},price:q,reviewsNegativeNumber:X,reviewsPositiveNumber:154,bid:a,shipping:a,delivery:{deliveryMethods:[{id:62528,code:o,name:p,cost:f,pickupPoints:[]}],hasFreeDelivery:b,isSameCity:b,name:bg,countryCodeFirm:k,__typename:l},sortPlace:{price_desc:$,price_asc:T,shops_desc:_,guarantee_desc:ai,payments_desc:U},__typename:m,visible:c},__typename:n},{node:{_id:"13792997146",condition:j,conditionId:e,conversionUrl:"\u002Fgo\u002Fprice\u002F13792997146\u002F",descriptionFull:A,descriptionShort:"Minola HBI 6473 BL GLASS 800 LED Line (5905538402003)",firmId:41071,firmLogo:"\u002Fimg\u002Fyp\u002F41071_v2_150.png?v=5",firmTitle:D,firmExtraInfo:{reviewsCount:i,reviewsCountShortPeriod:i,rating:a,isFirmNew:b,clicksAmount:1454,isFavorite:b,isOfficial:b,officialFirmLink:a,officialFirmImage:a,vendorHint:a,firmDateStatusNew:a,website:"minola.ua"},guaranteeTerm:C,guaranteeTermName:s,guaranteeType:u,hasBid:b,historyId:488407215,payment:{"pay-card":{type:v,attributes:{discount:[w]},enabled:c},"non-vat":{type:F,attributes:[],enabled:c},"cash-on-delivery":{type:t,attributes:{fee:[w]},enabled:c}},price:q,reviewsNegativeNumber:i,reviewsPositiveNumber:e,bid:a,shipping:a,delivery:{deliveryMethods:[{id:66099,code:o,name:p,cost:f,pickupPoints:[]}],hasFreeDelivery:c,isSameCity:c,name:r,countryCodeFirm:k,__typename:l},sortPlace:{price_desc:S,price_asc:Z,shops_desc:W,guarantee_desc:B,payments_desc:z},__typename:m,visible:c},__typename:n},{node:{_id:"13793935752",condition:j,conditionId:e,conversionUrl:"\u002Fgo\u002Fprice\u002F13793935752\u002F",descriptionFull:as,descriptionShort:as,firmId:24339,firmLogo:"\u002Fimg\u002Fyp\u002F24339_.jpg",firmTitle:"DiDi",firmExtraInfo:{reviewsCount:aa,reviewsCountShortPeriod:aa,rating:70,isFirmNew:b,clicksAmount:805,isFavorite:b,isOfficial:b,officialFirmLink:a,officialFirmImage:a,vendorHint:a,firmDateStatusNew:a,website:"didi.ua"},guaranteeTerm:z,guaranteeTermName:s,guaranteeType:u,hasBid:b,historyId:491917689,payment:[],price:q,reviewsNegativeNumber:X,reviewsPositiveNumber:S,bid:a,shipping:a,delivery:{deliveryMethods:[{id:57000,code:y,name:x,cost:d,pickupPoints:["Київ, вул. Антоновича 3а (Магазин на Льва Толстого)"]},{id:57001,code:o,name:p,cost:"50 грн",pickupPoints:[]},{id:56999,code:y,name:"кур'єром DiDi",cost:"200 грн",pickupPoints:[]}],hasFreeDelivery:b,isSameCity:c,name:r,countryCodeFirm:k,__typename:l},sortPlace:{price_desc:ad,price_asc:U,shops_desc:ad,guarantee_desc:_,payments_desc:K},__typename:m,visible:c},__typename:n},{node:{_id:"13807089789",condition:j,conditionId:e,conversionUrl:"\u002Fgo\u002Fprice\u002F13807089789\u002F",descriptionFull:br,descriptionShort:bs,firmId:42765,firmLogo:"\u002Fimg\u002Fyp\u002F42765_v2_150.png?v=1",firmTitle:"StellarShop ",firmExtraInfo:{reviewsCount:e,reviewsCountShortPeriod:e,rating:a,isFirmNew:b,clicksAmount:e,isFavorite:b,isOfficial:b,officialFirmLink:a,officialFirmImage:a,vendorHint:a,firmDateStatusNew:a,website:"stellarshop.com.ua"},guaranteeTerm:Q,guaranteeTermName:s,guaranteeType:u,hasBid:c,historyId:505587266,payment:{"pay-card":{type:v,attributes:{discount:[w]},enabled:c},"non-vat":{type:F,attributes:[],enabled:c},"card-in-shop":{type:G,attributes:[],enabled:c},"cash-on-delivery":{type:t,attributes:[],enabled:c}},price:q,reviewsNegativeNumber:e,reviewsPositiveNumber:e,bid:a,shipping:a,delivery:{deliveryMethods:[{id:67374,code:y,name:"кур'єром StellarShop ",cost:ao,pickupPoints:[]},{id:67375,code:o,name:p,cost:f,pickupPoints:[]},{id:67373,code:a,name:x,cost:f,pickupPoints:["Київ, вул. Рональда Рейгана, 1А (Склад)"]}],hasFreeDelivery:c,isSameCity:c,name:r,countryCodeFirm:k,__typename:l},sortPlace:{price_desc:N,price_asc:O,shops_desc:L,guarantee_desc:ae,payments_desc:L},__typename:m,visible:c},__typename:n},{node:{_id:"13808679576",condition:j,conditionId:e,conversionUrl:"\u002Fgo\u002Fprice\u002F13808679576\u002F",descriptionFull:A,descriptionShort:A,firmId:363,firmLogo:"\u002Fimg\u002Fyp\u002F363_v2_150.png?v=1",firmTitle:"Цифра",firmExtraInfo:{reviewsCount:bx,reviewsCountShortPeriod:bx,rating:bh,isFirmNew:b,clicksAmount:2225,isFavorite:b,isOfficial:b,officialFirmLink:a,officialFirmImage:a,vendorHint:a,firmDateStatusNew:a,website:"Y.ua"},guaranteeTerm:z,guaranteeTermName:s,guaranteeType:u,hasBid:b,historyId:489737799,payment:{"non-vat":{type:F,attributes:[],enabled:c},"cash-on-delivery":{type:t,attributes:[],enabled:c}},price:q,reviewsNegativeNumber:69,reviewsPositiveNumber:193,bid:a,shipping:af,delivery:{deliveryMethods:[{id:42415,code:o,name:p,cost:f,pickupPoints:[]}],hasFreeDelivery:b,isSameCity:c,name:r,countryCodeFirm:k,__typename:l},sortPlace:{price_desc:Z,price_asc:W,shops_desc:$,guarantee_desc:z,payments_desc:ad},__typename:m,visible:c},__typename:n},{node:{_id:"13810227568",condition:j,conditionId:e,conversionUrl:"\u002Fgo\u002Fprice\u002F13810227568\u002F",descriptionFull:aD,descriptionShort:A,firmId:650,firmLogo:"\u002Fimg\u002Fyp\u002F650_v2_150.png?v=2",firmTitle:"ТЕХНОСТАР",firmExtraInfo:{reviewsCount:N,reviewsCountShortPeriod:N,rating:a,isFirmNew:b,clicksAmount:472,isFavorite:b,isOfficial:b,officialFirmLink:a,officialFirmImage:a,vendorHint:a,firmDateStatusNew:a,website:"tehnostar.com.ua"},guaranteeTerm:a,guaranteeTermName:a,guaranteeType:u,hasBid:b,historyId:506102868,payment:{"card-card":{type:aC,attributes:{fee:["0.5"]},enabled:c},vat:{type:J,attributes:[],enabled:c},"cash-on-delivery":{type:t,attributes:[],enabled:c}},price:q,reviewsNegativeNumber:O,reviewsPositiveNumber:i,bid:a,shipping:a,delivery:{deliveryMethods:[{id:18831,code:y,name:"кур'єром ТЕХНОСТАР",cost:f,pickupPoints:[]},{id:18832,code:o,name:p,cost:f,pickupPoints:[]},{id:18834,code:a,name:x,cost:d,pickupPoints:["Київ, вул. Вікентія Хвойки 21 (Крапка 1)"]}],hasFreeDelivery:b,isSameCity:c,name:r,countryCodeFirm:k,__typename:l},sortPlace:{price_desc:ai,price_asc:M,shops_desc:ai,guarantee_desc:W,payments_desc:ai},__typename:m,visible:c},__typename:n},{node:{_id:"13812087496",condition:j,conditionId:e,conversionUrl:"\u002Fgo\u002Fprice\u002F13812087496\u002F",descriptionFull:"Витяжка вбудована Minola HBI 6473 BL GLASS 800 LED Line",descriptionShort:"Minola Витяжка вбудована Minola HBI 6473 BL GLASS 800 LED Line",firmId:18300,firmLogo:"\u002Fimg\u002Fyp\u002F18300_v2_150.png",firmTitle:"TopOne",firmExtraInfo:{reviewsCount:e,reviewsCountShortPeriod:e,rating:a,isFirmNew:b,clicksAmount:125,isFavorite:b,isOfficial:b,officialFirmLink:a,officialFirmImage:a,vendorHint:a,firmDateStatusNew:a,website:"topone.com.ua"},guaranteeTerm:a,guaranteeTermName:a,guaranteeType:u,hasBid:b,historyId:498494916,payment:{"pay-card":{type:v,attributes:[],enabled:c},vat:{type:J,attributes:[],enabled:c},"cash-on-delivery":{type:t,attributes:[],enabled:c}},price:q,reviewsNegativeNumber:e,reviewsPositiveNumber:e,bid:a,shipping:a,delivery:{deliveryMethods:[{id:52919,code:aq,name:ar,cost:f,pickupPoints:[]},{id:52920,code:o,name:p,cost:f,pickupPoints:[]}],hasFreeDelivery:b,isSameCity:c,name:r,countryCodeFirm:k,__typename:l},sortPlace:{price_desc:ag,price_asc:C,shops_desc:ag,guarantee_desc:Z,payments_desc:W},__typename:m,visible:c},__typename:n},{node:{_id:"13813633496",condition:j,conditionId:e,conversionUrl:"\u002Fgo\u002Fprice\u002F13813633496\u002F",descriptionFull:by,descriptionShort:bz,firmId:3300,firmLogo:"\u002Fimg\u002Fyp\u002F3300_.jpg?v=1",firmTitle:"ITbox.ua",firmExtraInfo:{reviewsCount:306,reviewsCountShortPeriod:305,rating:aF,isFirmNew:b,clicksAmount:3102,isFavorite:b,isOfficial:b,officialFirmLink:a,officialFirmImage:a,vendorHint:a,firmDateStatusNew:a,website:"itbox.ua"},guaranteeTerm:C,guaranteeTermName:s,guaranteeType:u,hasBid:c,historyId:500067033,payment:{"pay-card":{type:v,attributes:{discount:[w]},enabled:c},vat:{type:J,attributes:[],enabled:c},"card-in-shop":{type:G,attributes:[],enabled:c}},price:q,reviewsNegativeNumber:80,reviewsPositiveNumber:216,bid:a,shipping:a,delivery:{deliveryMethods:[{id:31586,code:o,name:p,cost:ao,pickupPoints:[]},{id:31123,code:a,name:x,cost:d,pickupPoints:["Київ, просп. Соборності 2\u002F1а (Пункт видачі ITbox - Київ (просп. Соборності 2\u002F1а))","Київ, просп. Берестейський 67, корпус G (Киев (просп. Перемоги 6, корпус G). Шоу-рум Дитячих товарів)","Київ, вул. Вербицкого 1 (Пункт видачі ITbox - Київ (вул. Вербицкого, 1))","Київ, пр. Науки 17\u002F15 (Пункт видачі ITbox - Київ (пр. Науки, 17\u002F15))","Київ, вул. Вадима Гетьмана 13 (Пункт видачі ITbox - Київ, (вул. Вадима Гетьмана, 13))","Київ, вул. Дмитрівська 56 (Пункт видачі ITbox - Київ (вул. Дмитрівська, 56))","Київ, вул. Васильківська 37А (Пункт видачі ITbox - Київ (вул. Васильківська, 37А))","Київ, вул. Рейгана 8 (Драйзера 8) (Пункт видачі ITbox - Київ (вул. Рейгана, 8))","Київ, просп. Оболонський 47\u002F42 (Пункт видачі ITbox - Київ (просп. Оболонський, 47\u002F42))","Київ, просп. Степана Бандери 23 (Пункт видачі ITbox (Магазин BRAIN))"]}],hasFreeDelivery:c,isSameCity:c,name:r,countryCodeFirm:k,__typename:l},sortPlace:{price_desc:R,price_asc:B,shops_desc:N,guarantee_desc:i,payments_desc:N},__typename:m,visible:c},__typename:n},{node:{_id:"13813765807",condition:j,conditionId:e,conversionUrl:"\u002Fgo\u002Fprice\u002F13813765807\u002F",descriptionFull:by,descriptionShort:bz,firmId:26140,firmLogo:"\u002Fimg\u002Fyp\u002F26140_.jpg?v=2",firmTitle:"Brain.Комп'ютери\u002Fгаджети",firmExtraInfo:{reviewsCount:265,reviewsCountShortPeriod:263,rating:84,isFirmNew:b,clicksAmount:2265,isFavorite:b,isOfficial:b,officialFirmLink:a,officialFirmImage:a,vendorHint:a,firmDateStatusNew:a,website:"Brain.com.ua"},guaranteeTerm:C,guaranteeTermName:s,guaranteeType:u,hasBid:c,historyId:498857429,payment:{"pay-card":{type:v,attributes:{discount:[w]},enabled:c},vat:{type:J,attributes:[],enabled:c},"card-in-shop":{type:G,attributes:[],enabled:c}},price:q,reviewsNegativeNumber:42,reviewsPositiveNumber:bt,bid:a,shipping:a,delivery:{deliveryMethods:[{id:35899,code:o,name:p,cost:ao,pickupPoints:[]},{id:35896,code:a,name:x,cost:d,pickupPoints:["Київ, вул. Рейгана 8 (Драйзера 8) (Комп'ютери та гаджети в Києві)","Київ, вул. Дмитрівська 56 (Комп'ютери та гаджети на Лук'янівці)","Київ, вул. Вадима Гетьмана 13 (Комп'ютери та гаджети в Києві)","Київ, вул. Васильківська 37А (Комп'ютери та гаджети на Васильківській)","Київ, пр. Берестейський 67, корпус G (Склад-магазин Brain)","Київ, вул. Архітектора Вербицького 1 (Комп'ютери та гаджети в ТРЦ New Way)","Київ, просп. Науки, 17\u002F15 (Комп'ютери та гаджети в Києві)","Київ, пр. Степана Бандери 23 (Комп'ютери та гаджети в ТЦ Городок)","Київ, пр. Соборності 2\u002F1А (Комп'ютери та гаджети в ТЦ Дарниця)","Київ, просп. Оболонський 47\u002F42 (Комп'ютери та гаджети в ТЦ Оазис)","Київ, пр. Правди 47 (Комп'ютери та гаджети в ТРЦ Retrovill)"]}],hasFreeDelivery:c,isSameCity:c,name:r,countryCodeFirm:k,__typename:l},sortPlace:{price_desc:ae,price_asc:X,shops_desc:R,guarantee_desc:L,payments_desc:R},__typename:m,visible:c},__typename:n},{node:{_id:"13816559192",condition:j,conditionId:e,conversionUrl:"\u002Fgo\u002Fprice\u002F13816559192\u002F",descriptionFull:A,descriptionShort:A,firmId:287,firmLogo:"\u002Fimg\u002Fyp\u002F287_v2_150.png?v=2",firmTitle:"STYLUS",firmExtraInfo:{reviewsCount:539,reviewsCountShortPeriod:538,rating:aF,isFirmNew:b,clicksAmount:4217,isFavorite:b,isOfficial:b,officialFirmLink:a,officialFirmImage:a,vendorHint:a,firmDateStatusNew:a,website:"stls.store"},guaranteeTerm:z,guaranteeTermName:s,guaranteeType:u,hasBid:b,historyId:489741040,payment:{"non-vat":{type:F,attributes:[],enabled:c},"cash-on-delivery":{type:t,attributes:[],enabled:c}},price:q,reviewsNegativeNumber:120,reviewsPositiveNumber:396,bid:a,shipping:af,delivery:{deliveryMethods:[{id:10128,code:y,name:"кур'єром STYLUS",cost:f,pickupPoints:[]},{id:10129,code:o,name:p,cost:f,pickupPoints:[]},{id:19107,code:a,name:x,cost:d,pickupPoints:["Київ, проспект Миколи Бажана, 30 (STYLUS на Бажана)","Київ, пр. Степана Бандери, 21 (Stylus на пр. Степана Бандери)"]}],hasFreeDelivery:b,isSameCity:c,name:r,countryCodeFirm:k,__typename:l},sortPlace:{price_desc:T,price_asc:_,shops_desc:ah,guarantee_desc:Y,payments_desc:S},__typename:m,visible:c},__typename:n},{node:{_id:"13823553923",condition:j,conditionId:e,conversionUrl:"\u002Fgo\u002Fprice\u002F13823553923\u002F",descriptionFull:as,descriptionShort:as,firmId:24345,firmLogo:"\u002Fimg\u002Fyp\u002F24345_v2_150.png",firmTitle:"ТВ МИР",firmExtraInfo:{reviewsCount:K,reviewsCountShortPeriod:C,rating:61,isFirmNew:b,clicksAmount:bn,isFavorite:b,isOfficial:b,officialFirmLink:a,officialFirmImage:a,vendorHint:a,firmDateStatusNew:a,website:"tv-mir.com.ua"},guaranteeTerm:z,guaranteeTermName:s,guaranteeType:"от магазина",hasBid:b,historyId:507805487,payment:{"non-vat":{type:F,attributes:[],enabled:c},"cash-on-delivery":{type:t,attributes:[],enabled:c}},price:ap,reviewsNegativeNumber:V,reviewsPositiveNumber:_,bid:a,shipping:af,delivery:{deliveryMethods:[{id:20413,code:y,name:"кур'єром ТВ МИР",cost:f,pickupPoints:[]},{id:20416,code:o,name:p,cost:f,pickupPoints:[]},{id:38901,code:a,name:x,cost:d,pickupPoints:["Київ, вул. Івана Виговського 13 (ТБ СВІТ Київ)"]}],hasFreeDelivery:b,isSameCity:c,name:r,countryCodeFirm:k,__typename:l},sortPlace:{price_desc:L,price_asc:K,shops_desc:K,guarantee_desc:S,payments_desc:Q},__typename:m,visible:c},__typename:n},{node:{_id:"13829933190",condition:j,conditionId:e,conversionUrl:"\u002Fgo\u002Fprice\u002F13829933190\u002F",descriptionFull:"Кухонна витяжка Minola HBI 6473 BL GLASS 800 LED Line",descriptionShort:"Minola Кухонна витяжка Minola HBI 6473 BL GLASS 800 LED Line",firmId:862,firmLogo:"\u002Fimg\u002Fyp\u002F862_v2_150.png?v=2",firmTitle:"ALLO.ua",firmExtraInfo:{reviewsCount:333,reviewsCountShortPeriod:331,rating:bv,isFirmNew:b,clicksAmount:13852,isFavorite:b,isOfficial:b,officialFirmLink:a,officialFirmImage:a,vendorHint:a,firmDateStatusNew:a,website:"allo.ua"},guaranteeTerm:Q,guaranteeTermName:s,guaranteeType:a,hasBid:c,historyId:490413873,payment:{"pay-card":{type:v,attributes:[],enabled:c},"cash-on-delivery":{type:t,attributes:{fee:[w]},enabled:c}},price:q,reviewsNegativeNumber:136,reviewsPositiveNumber:183,bid:a,shipping:a,delivery:{deliveryMethods:[{id:10361,code:y,name:"кур'єром ALLO.ua",cost:f,pickupPoints:[]},{id:10360,code:o,name:p,cost:f,pickupPoints:[]},{id:66718,code:aq,name:ar,cost:f,pickupPoints:[]},{id:10363,code:a,name:x,cost:d,pickupPoints:["Київ, просп. Відрадний, 16\u002F50, маг. Kyivstar (АЛЛО)","Київ, просп. Бажана, 3-В (АЛЛО)","Київ, вул. Велика Васильківська, 72 (АЛЛО, ТЦ «Олімпійський», 1-ий поверх)","Київ, просп. Степана Бандери (кол. Московський), 23, маг. Mi Store (АЛЛО, ТЦ «Городок», 1-ий поверх)","Київ, вул. Лаврухіна Миколи, 4 (АЛЛО MAX, ТРЦ «Район», 1-ий поверх)","Київ, вул. Антоновича, 176 (АЛЛО MAX, ТРЦ «OCEAN PLAZA», -1-ий поверх)","Київ, просп. Повітрофлотський, 50\u002F2 (АЛЛО)","Київ, просп. Соборності, 2\u002F1-А (АЛЛО, ТЦ «Дарниця», 1-ий поверх)","Київ, вул. Миколайчука Івана (Серафимовича), 11 (АЛЛО)","Київ, вул. Гната Хоткевича, 1-В (АЛЛО MAX, ТЦ «Проспект», 2-ий поверх)","Київ, вул. Будівельників, 40 (АЛЛО, ТЦ «DOMA center», 1-ий поверх)","Київ, просп. Маяковського (Троєщина), 43\u002F2 (АЛЛО)","Київ, вул. Малишка Андрія, 3-Д (АЛЛО)","Київ, просп. Правди, 58А (АЛЛО, ТЦ «Орнамент», 1-ий поверх)","Київ, вул. Вербицького Архітектора, 1 (АЛЛО, ТЦ «Нью Вей», мінус 1-ий поверх)","Київ, просп. Степана Бандери (кол. Московський), 23 (АЛЛО MAX, ТЦ «Городок», 1-ий поверх)","Київ, вул. Хрещатик, 21 (АЛЛО)","Київ, вул. Берковецька, 6Д (АЛЛО MAX, ТРК «Лавина», 1-ий поверх, сектор 6013)","Київ, майдан Незалежності, ПТП №1, , маг. Mi Store (АЛЛО, ТЦ «Globus», 1-ий поверх)","Київ, вул. Здолбунівська, 17, маг. Mi Store (АЛЛО, , ТРЦ «Ашан»)","Київ, просп. Перемоги (Проспект), 24 (АЛЛО MAX, ТРЦ «Smart Plaza», 2-ий поверх)","Київ, вул. Іллєнка Юрія (Мельникова), 1-Ц (АЛЛО)","Київ, вул. Героїв Полку Азов (Малиновського Маршала), 12 А (АЛЛО)","Київ, вул. Лугова, 12 (АЛЛО, ТРЦ «Караван», 1-ий поверх)","Київ, вул. Мішуги Олександра, 4 А (АЛЛО MAX, ТЦ «Піраміда», 1-ий поверх)","Київ, вул. Я. Гніздовського (кол. Магнітогорська), 1 А (АЛЛО, ТРЦ «Даринок», 1-ий поверх)","Київ, вул. Лаврухіна Миколи, 4, маг. Mi Store\t (АЛЛО, ТРЦ «Район», 1-ий поверх)","Київ, вул. Гната Хоткевича, 1-В, маг. Mi Store (АЛЛО, ТРК «Проспект», 1-ий поверх)","Київ, вул. Антоновича (Горького), 176, маг. Mi Store (АЛЛО, ТРЦ «OCEAN PLAZA», -1-ий поверх)","Київ, вул. Мішуги Олександра, 4, маг. Mi Store (АЛЛО, ТЦ «ПІРАМІDА», 1-ий поверх)","Київ, вул. Берковецька, 6Д, маг. Mi Store (АЛЛО, ТРЦ «Lavina», 1-ий поверх)","Київ, просп. Правди, 47 (АЛЛО MAX, ТРЦ «Retroville»)","Київ, просп. Правди, 47, маг. Mi Store (АЛЛО, , ТЦ «Retroville»)","Київ, просп. Перемоги (Проспект), 134\u002F1, секція №130 (АЛЛО, ТЦ Хіт Mall)","Київ, дорога Кільцева, 1 (АЛЛО MAX, RESPUBLIKA PARK)","Київ, вул. Велика Кільцева, 4-Ф (АЛЛО, ТЦ «Promenada Park», 1-ий поверх)","Київ, просп. Глушкова Академіка, 13-Б (АЛЛО Express)"]}],hasFreeDelivery:b,isSameCity:c,name:r,countryCodeFirm:k,__typename:l},sortPlace:{price_desc:X,price_asc:R,shops_desc:B,guarantee_desc:U,payments_desc:B},__typename:m,visible:c},__typename:n},{node:{_id:"13832234382",condition:j,conditionId:e,conversionUrl:"\u002Fgo\u002Fprice\u002F13832234382\u002F",descriptionFull:"Витяжка Minola Hbi 6473 Bl Glass 800 Led Line",descriptionShort:"Minola Витяжка Minola Hbi 6473 Bl Glass 800 Led Line (5905538402003)",firmId:26823,firmLogo:"\u002Fimg\u002Fyp\u002F26823_v2_150.png?v=7",firmTitle:"Епіцентр",firmExtraInfo:{reviewsCount:an,reviewsCountShortPeriod:an,rating:bo,isFirmNew:b,clicksAmount:2587,isFavorite:b,isOfficial:b,officialFirmLink:a,officialFirmImage:a,vendorHint:a,firmDateStatusNew:a,website:"epicentrk.ua"},guaranteeTerm:C,guaranteeTermName:s,guaranteeType:u,hasBid:b,historyId:493552035,payment:[],price:q,reviewsNegativeNumber:aE,reviewsPositiveNumber:M,bid:a,shipping:a,delivery:{deliveryMethods:[{id:49373,code:o,name:p,cost:f,pickupPoints:[]},{id:49374,code:aq,name:ar,cost:f,pickupPoints:[]},{id:66581,code:a,name:x,cost:d,pickupPoints:["Київ, вул. Полярна 20-Д (ЕпіцентрК7)","Київ, вул. Берковецька 6-В (ЕпіцентрК6)","Київ, пр. С. Бандери 11-А (ЕпіцентрК8)","Київ, вул. Віскозна 4 (ЕпіцентрК)","Київ, пр. П. Григоренка 40 (ЕпіцентрК)","Київ, вул. Кільцева дорога 1-Б (Епіцентр)","Київ, вул. Братиславська 11 (Епіцентр)"]}],hasFreeDelivery:b,isSameCity:c,name:r,countryCodeFirm:k,__typename:l},sortPlace:{price_desc:W,price_asc:$,shops_desc:T,guarantee_desc:N,payments_desc:C},__typename:m,visible:c},__typename:n}],currentFilters:[],currentSort:d,offersToSkip:[],filterGroupsSet:b,checklistMain:{},checklistDelivery:{},checklistShipping:{},checklistPay:{},checklistGuarantee:{},checklistGuaranteeTerms:{},totalCount:K,__typename:"OfferConnection"},productAnalytics:{},productValues:{edges:[{node:{isHeader:b,url:"\u002Fbrands\u002Fminola\u002F",title:ax,value:D,help:a,h1Text:a,type:ax,__typename:g},__typename:h},{node:{isHeader:b,url:"\u002Fbt\u002Fvytyazhki\u002F121966\u002F",title:aG,value:at,help:d,h1Text:a,type:au,__typename:g},__typename:h},{node:{isHeader:b,url:a,title:bA,value:bB,help:d,h1Text:a,type:a,__typename:g},__typename:h},{node:{isHeader:c,url:a,title:"#Основні характеристики",value:a,help:d,h1Text:a,type:a,__typename:g},__typename:h},{node:{isHeader:b,url:"\u002Fbt\u002Fvytyazhki\u002F1949\u002F",title:"Ширина, мм",value:aH,help:d,h1Text:"Витяжки шириною 600 мм (60 см)",type:au,__typename:g},__typename:h},{node:{isHeader:b,url:a,title:"Висота, мм",value:"175",help:d,h1Text:a,type:a,__typename:g},__typename:h},{node:{isHeader:b,url:a,title:"Глибина, мм",value:"290",help:d,h1Text:a,type:a,__typename:g},__typename:h},{node:{isHeader:b,url:a,title:bC,value:bD,help:d,h1Text:a,type:a,__typename:g},__typename:h},{node:{isHeader:b,url:a,title:"Тип повітроочисника",value:bE,help:d,h1Text:a,type:a,__typename:g},__typename:h},{node:{isHeader:b,url:a,title:"Відведення\u002Fрециркуляція повітря",value:"є\u002Fє",help:d,h1Text:a,type:a,__typename:g},__typename:h},{node:{isHeader:b,url:a,title:"Mаксимальна потужність, м3 \u002F год",value:"800",help:d,h1Text:a,type:a,__typename:g},__typename:h},{node:{isHeader:b,url:a,title:"Рекомендована площа приміщення (при висоті 2,7 м), м2",value:"понад 28,5",help:d,h1Text:a,type:a,__typename:g},__typename:h},{node:{isHeader:b,url:a,title:"Матеріал корпусу",value:"фарбований метал, скло",help:d,h1Text:a,type:a,__typename:g},__typename:h},{node:{isHeader:b,url:a,title:"Колір",value:bF,help:d,h1Text:a,type:a,__typename:g},__typename:h},{node:{isHeader:b,url:a,title:"Рівень шуму, дБ",value:"49-54",help:d,h1Text:a,type:a,__typename:g},__typename:h},{node:{isHeader:b,url:a,title:"Споживана потужність, Вт",value:"немає даних",help:d,h1Text:a,type:a,__typename:g},__typename:h},{node:{isHeader:b,url:a,title:"Діаметр вихідного отвору, мм",value:"120",help:d,h1Text:a,type:a,__typename:g},__typename:h},{node:{isHeader:b,url:a,title:"Висота вбудовування, мм",value:"170",help:d,h1Text:a,type:a,__typename:g},__typename:h},{node:{isHeader:c,url:a,title:"#Фільтри",value:a,help:d,h1Text:a,type:a,__typename:g},__typename:h},{node:{isHeader:b,url:a,title:"Грубого очищення (жировий) - металевий",value:aI,help:d,h1Text:a,type:a,__typename:g},__typename:h},{node:{isHeader:b,url:a,title:"Грубого очищення (жировий) - з органічних волокон",value:ab,help:d,h1Text:a,type:a,__typename:g},__typename:h},{node:{isHeader:b,url:a,title:"Тонкого очищення (вугільний фільтр)",value:"опція",help:d,h1Text:a,type:a,__typename:g},__typename:h},{node:{isHeader:c,url:a,title:"#Оснащення",value:a,help:d,h1Text:a,type:a,__typename:g},__typename:h},{node:{isHeader:b,url:a,title:"Мотор (кількість х потужність, Вт)",value:"1х70",help:d,h1Text:a,type:a,__typename:g},__typename:h},{node:{isHeader:b,url:a,title:"Кількість швидкостей\u002Fінтенсивний режим",value:"3",help:d,h1Text:a,type:a,__typename:g},__typename:h},{node:{isHeader:b,url:a,title:"Освітлення (кількість ламп x потужність, Вт)",value:"LED 1х5",help:d,h1Text:a,type:a,__typename:g},__typename:h},{node:{isHeader:b,url:a,title:"Таймер",value:aI,help:d,h1Text:a,type:a,__typename:g},__typename:h},{node:{isHeader:b,url:a,title:"Індикатор заміни фільтра",value:ab,help:d,h1Text:a,type:a,__typename:g},__typename:h},{node:{isHeader:b,url:a,title:"Дисплей",value:ab,help:d,h1Text:a,type:a,__typename:g},__typename:h},{node:{isHeader:b,url:"\u002Fbt\u002Fvytyazhki\u002F20900494\u002F",title:"Зворотний клапан",value:aI,help:d,h1Text:"Витяжка із зворотним клапаном",type:au,__typename:g},__typename:h},{node:{isHeader:b,url:a,title:"Сенсор диму",value:ab,help:d,h1Text:a,type:a,__typename:g},__typename:h},{node:{isHeader:b,url:a,title:"Периметральне всмоктування",value:ab,help:d,h1Text:a,type:a,__typename:g},__typename:h},{node:{isHeader:b,url:a,title:"Покриття проти відбитків пальців",value:ab,help:d,h1Text:a,type:a,__typename:g},__typename:h},{node:{isHeader:b,url:"https:\u002F\u002Fminola.ua\u002Fminola-hbi-6473-bl-glass-800-led-line",title:"productOnVendorSite",value:"https:\u002F\u002Fminola.ua\u002Fminola-hbi-6473-bl-glass-800-...",help:a,h1Text:a,type:"siteVendor",__typename:g},__typename:h}],__typename:"ProductValuesConnection"},questions:[],sales:{sales:{"13744839820":{id:1840374989,holidayTitle:a,title:"Подарунок: Магазин приймає карти єВідновлення. Знижка -5% на весь товар на сайті!. Вигода: 10000,00 грн",salePriceUrl:"\u002Fgo\u002Fsales\u002F1840374989\u002F13744839820\u002F"},"13782151715":{id:2031994407,holidayTitle:a,title:"Подарунок: вартість доставки 50 грн в пункти видачі Rozetka. Вигода: 100,00 грн",salePriceUrl:"\u002Fgo\u002Fsales\u002F2031994407\u002F13782151715\u002F"},"13694595033":{id:2088958065,holidayTitle:a,title:bG,salePriceUrl:"\u002Fgo\u002Fsales\u002F2088958065\u002F13694595033\u002F"},"13807089789":{id:2128897056,holidayTitle:a,title:bG,salePriceUrl:"\u002Fgo\u002Fsales\u002F2128897056\u002F13807089789\u002F"},"13697919501":{id:2145175101,holidayTitle:a,title:"Подарунок: Знижка -7% при покупці з промокодом VESNA. Вигода: 1000,00 грн",salePriceUrl:"\u002Fgo\u002Fsales\u002F2145175101\u002F13697919501\u002F"},"13687738811":{id:2145182721,holidayTitle:a,title:"Знижка 2300 грн",salePriceUrl:"\u002Fgo\u002Fsales\u002F2145182721\u002F13687738811\u002F",oldPrice:ap},"13782622915":{id:2145192128,holidayTitle:a,title:"Подарунок: Безкоштовна доставка замовлень від 1000 грн по Україні. Вигода: 297,00 грн",salePriceUrl:"\u002Fgo\u002Fsales\u002F2145192128\u002F13782622915\u002F"},"13736320781":{id:2145196358,holidayTitle:a,title:"Подарунок: Кешбек. Вигода: 402,00 грн",salePriceUrl:"\u002Fgo\u002Fsales\u002F2145196358\u002F13736320781\u002F"}}},siteZone:{},userReviews:[],userRights:{},vendorCatalogs:[],videos:[],parentId:aO,date:"2024-11-28",title:ay,url:aj,section:{_id:P,title:al,path:aw,isAdult:b,__typename:"Section"},vendor:{_id:I,title:D,path:"minola",__typename:"Vendor"},hlSectionId:av,isDefaultTabOffers:c,isGuaranteeHidden:b,userSubscribed:b,userSubscribedNewSales:b,userSubscribedLowerPrice:b,targetUserSubscriptionLowerPrice:a,userReviewsSubscribed:b,imageLinks:[{thumb:"\u002Fimg\u002Ftx\u002F510\u002F5107419100.jpg",basic:bH,small:bI,big:bJ},{thumb:"\u002Fimg\u002Ftx\u002F510\u002F5107419120.jpg",basic:"\u002Fimg\u002Ftx\u002F510\u002F5107419121.jpg",small:"\u002Fimg\u002Ftx\u002F510\u002F510741912_s265.jpg",big:"\u002Fimg\u002Ftx\u002F510\u002F5107419125.jpg"},{thumb:"\u002Fimg\u002Ftx\u002F510\u002F5107419140.jpg",basic:"\u002Fimg\u002Ftx\u002F510\u002F5107419141.jpg",small:"\u002Fimg\u002Ftx\u002F510\u002F510741914_s265.jpg",big:"\u002Fimg\u002Ftx\u002F510\u002F5107419145.jpg"},{thumb:"\u002Fimg\u002Ftx\u002F510\u002F5107419160.jpg",basic:"\u002Fimg\u002Ftx\u002F510\u002F5107419161.jpg",small:"\u002Fimg\u002Ftx\u002F510\u002F510741916_s265.jpg",big:"\u002Fimg\u002Ftx\u002F510\u002F5107419165.jpg"},{thumb:"\u002Fimg\u002Ftx\u002F510\u002F5107419180.jpg",basic:"\u002Fimg\u002Ftx\u002F510\u002F5107419181.jpg",small:"\u002Fimg\u002Ftx\u002F510\u002F510741918_s265.jpg",big:"\u002Fimg\u002Ftx\u002F510\u002F5107419185.jpg"},{thumb:"\u002Fimg\u002Ftx\u002F510\u002F5107419200.jpg",basic:"\u002Fimg\u002Ftx\u002F510\u002F5107419201.jpg",small:"\u002Fimg\u002Ftx\u002F510\u002F510741920_s265.jpg",big:"\u002Fimg\u002Ftx\u002F510\u002F5107419205.jpg"},{thumb:"\u002Fimg\u002Ftx\u002F510\u002F5107419230.jpg",basic:"\u002Fimg\u002Ftx\u002F510\u002F5107419231.jpg",small:"\u002Fimg\u002Ftx\u002F510\u002F510741923_s265.jpg",big:"\u002Fimg\u002Ftx\u002F510\u002F5107419235.jpg"},{thumb:"\u002Fimg\u002Ftx\u002F510\u002F5107419270.jpg",basic:"\u002Fimg\u002Ftx\u002F510\u002F5107419271.jpg",small:"\u002Fimg\u002Ftx\u002F510\u002F510741927_s265.jpg",big:"\u002Fimg\u002Ftx\u002F510\u002F5107419275.jpg"},{thumb:"\u002Fimg\u002Ftx\u002F510\u002F5107419300.jpg",basic:"\u002Fimg\u002Ftx\u002F510\u002F5107419301.jpg",small:"\u002Fimg\u002Ftx\u002F510\u002F510741930_s265.jpg",big:"\u002Fimg\u002Ftx\u002F510\u002F5107419305.jpg"},{thumb:"\u002Fimg\u002Ftx\u002F510\u002F5107419320.jpg",basic:"\u002Fimg\u002Ftx\u002F510\u002F5107419321.jpg",small:"\u002Fimg\u002Ftx\u002F510\u002F510741932_s265.jpg",big:"\u002Fimg\u002Ftx\u002F510\u002F5107419325.jpg"}],type:at,isNew:e,isLine:b,lineName:d,linePathNew:a,techShortSpecifications:[at," ширина: 600 мм"," глибина: 290 мм"," тип повітроочисника: проточний\u002Fциркуляційний"," колір: чорний","продуктивність: 800 м³\u002Fгод","приміщення: понад 28,5 м²"],techShortSpecificationsList:[{value:at,isNoMargin:b},{key:"ширина",value:"600 мм",isNoMargin:b},{key:"глибина",value:"290 мм",isNoMargin:b},{key:"тип повітроочисника",value:bE,isNoMargin:b},{key:"колір",value:bF,isNoMargin:b},{key:"продуктивність",value:"800 м³\u002Fгод",isNoMargin:b},{key:"приміщення",value:"понад 28,5 м²",isNoMargin:b}],fullDescription:"Повновбудована кухонна витяжка Minola HBI 6473 BL GLASS 800 LED Line оснащена мотором потужністю 70 Вт і забезпечує максимальну продуктивність до 800 м³\u002Fгод, що дає змогу ефективно видаляти пару, запахи та кіптяву, які виникають у процесі приготування їжі. Ширина пристрою забезпечує легку інтеграцію в стандартні кухонні шафи. Корпус виконано з пофарбованого металу і загартованого скла, стійкого до високих температур і механічних пошкоджень. Управління здійснюється за допомогою сенсорної панелі з п'ятьма кнопками, розташованими на фронтальній частині, що забезпечує інтуїтивну взаємодію з пристроєм. Витяжка підтримує два режими роботи: відведення повітря і рециркуляція, що дає змогу адаптувати її під різні умови експлуатації. Для ефективного очищення повітря передбачено п'ятишаровий алюмінієвий жировий фільтр, розташований під захисною кришкою. Освітлення робочої зони забезпечується світлодіодною лампою потужністю 5 Вт, яка вирізняється енергоефективністю та довговічністю.  Завдяки своїм технічним характеристикам і функціональності, витяжка Minola HBI 6473 BL GLASS 800 BL GLASS LED Line є практичним рішенням для забезпечення чистоти і свіжості повітря на кухні.",rating:a,colorRating:a,minPrice:bw,maxPrice:ap,newProducts:[{id:26225504,title:"HPL 633 WH",path:"\u002Fbt-vytyazhki\u002Fminola-hpl-633-wh\u002F",image:"\u002Fimg\u002Ftx\u002F525\u002F5254894991.jpg",minPrice:aJ,quantity:B,vendor:D,vendorId:I,isNew:c},{id:26225493,title:"HPL 633 I",path:"\u002Fbt-vytyazhki\u002Fminola-hpl-633-i\u002F",image:"\u002Fimg\u002Ftx\u002F525\u002F5252092221.jpg",minPrice:294900,quantity:O,vendor:D,vendorId:I,isNew:c},{id:26225490,title:"HPL 633 IV",path:"\u002Fbt-vytyazhki\u002Fminola-hpl-633-iv\u002F",image:"\u002Fimg\u002Ftx\u002F525\u002F5254895001.jpg",minPrice:aJ,quantity:B,vendor:D,vendorId:I,isNew:c},{id:26225478,title:"HPL 633 BR",path:"\u002Fbt-vytyazhki\u002Fminola-hpl-633-br\u002F",image:"\u002Fimg\u002Ftx\u002F525\u002F5252090351.jpg",minPrice:288100,quantity:O,vendor:D,vendorId:I,isNew:c},{id:26225475,title:"HPL 633 BL",path:"\u002Fbt-vytyazhki\u002Fminola-hpl-633-bl\u002F",image:"\u002Fimg\u002Ftx\u002F525\u002F5254895011.jpg",minPrice:aJ,quantity:B,vendor:D,vendorId:I,isNew:c},{id:26178827,title:"HVS 6812 BL 1200 LED",path:"\u002Fbt-vytyazhki\u002Fminola-hvs-6812-bl-1200-led\u002F",image:"\u002Fimg\u002Ftx\u002F521\u002F5218128801.jpg",minPrice:593900,quantity:Y,vendor:D,vendorId:I,isNew:c},{id:26134501,title:"MTG 6242 BL LED",path:"\u002Fbt-vytyazhki\u002Fminola-mtg-6242-bl-led\u002F",image:"\u002Fimg\u002Ftx\u002F523\u002F5235849011.jpg",minPrice:467900,quantity:U,vendor:D,vendorId:I,isNew:c},{id:26048121,title:"MTG 6642 I LED",path:"\u002Fbt-vytyazhki\u002Fminola-mtg-6642-i-led\u002F",image:"\u002Fimg\u002Ftx\u002F521\u002F5218194431.jpg",minPrice:509900,quantity:$,vendor:D,vendorId:I,isNew:b}],similarProducts:{products:[{id:25888392,title:"NUOVA 6JWRB NERO",path:"\u002Fbt-vytyazhki\u002Fperfelli-nuova-6jwrb-nero\u002F",image:"\u002Fimg\u002Ftx\u002F521\u002F5218191581.jpg",minPrice:bK,quantity:aS,vendor:bL,vendorId:bM,sectionId:P,popularity:B,isNew:b},{id:bN,title:bO,path:bP,image:bQ,minPrice:629900,quantity:i,vendor:D,vendorId:I,sectionId:P,popularity:N,isNew:b},{id:25888393,title:"LUMINA WBG 65 BLACK",path:"\u002Fbt-vytyazhki\u002Fweilor-lumina-wbg-65-black\u002F",image:"\u002Fimg\u002Ftx\u002F510\u002F5109314541.jpg",minPrice:799850,quantity:K,vendor:bR,vendorId:bS,sectionId:P,popularity:L,isNew:b},{id:25888390,title:"NUOVA 6JWR BIANCO",path:"\u002Fbt-vytyazhki\u002Fperfelli-nuova-6jwr-bianco\u002F",image:"\u002Fimg\u002Ftx\u002F521\u002F5219091521.jpg",minPrice:bK,quantity:aa,vendor:bL,vendorId:bM,sectionId:P,popularity:i,isNew:b},{id:24824836,title:"CH-600B",path:"\u002Fbt-vytyazhki\u002Fcastle-ch-600b\u002F",image:"\u002Fimg\u002Ftx\u002F494\u002F4942796201.jpg",minPrice:552400,quantity:O,vendor:"Castle",vendorId:226347,sectionId:P,popularity:i,isNew:b},{id:25888394,title:"LUMINA WBG 65 WHITE",path:"\u002Fbt-vytyazhki\u002Fweilor-lumina-wbg-65-white\u002F",image:"\u002Fimg\u002Ftx\u002F510\u002F5109314441.jpg",minPrice:799900,quantity:L,vendor:bR,vendorId:bS,sectionId:P,popularity:e,isNew:b}],filters:[{filterValueId:121966,filterValueTitle:"вытяжка встраиваемая",filterValueTitleUk:"витяжка вбудована",filterTitle:aG,filterTitleUk:aG},{filterValueId:1949,filterValueTitle:aH,filterValueTitleUk:aH,filterTitle:bT,filterTitleUk:bT},{filterValueId:576160,filterValueTitle:bU,filterValueTitleUk:bU,filterTitle:"Mаксимальная производительность",filterTitleUk:"Максимальна продуктивність"},{filterValueId:1928,filterValueTitle:"встраиваемая (в шкаф)",filterValueTitleUk:bB,filterTitle:"Тип монтажа",filterTitleUk:bA},{filterValueId:1935,filterValueTitle:"28,5 и более",filterValueTitleUk:"28,5 і більше",filterTitle:"Рекомендованная площадь помещения",filterTitleUk:"Рекомендована площа приміщення"},{filterValueId:600437,filterValueTitle:"сенсорное",filterValueTitleUk:bD,filterTitle:"Управление",filterTitleUk:bC},{filterValueId:1955,filterValueTitle:"отвод воздуха",filterValueTitleUk:"відвід повітря",filterTitle:bV,filterTitleUk:bW},{filterValueId:1956,filterValueTitle:"рециркуляция воздуха",filterValueTitleUk:"рециркуляція повітря",filterTitle:bV,filterTitleUk:bW}],priceRange:{from:479815,to:901908}},promoRelinkList:[],crossSelling:[{title:"Кухонні мийки",image:"\u002Fimg\u002Ftx\u002F481\u002F4813217391.jpg",path:"\u002Fremont\u002Fkuhonnye-mojki\u002F"},{title:"Мікрохвильові печі",image:"\u002Fimg\u002Ftx\u002F524\u002F5245796201.jpg",path:"\u002Fbt\u002Fmikrovolnovye-pechi\u002F"},{title:"Засоби по догляду за побутовою технікою",image:"\u002Fimg\u002Ftx\u002F321\u002F3219056371.jpg",path:"\u002Fpobutova_himiia\u002Fsredstva-po-uhodu-za-bytovoj-tehnikoj\u002F"},{title:a$,image:"\u002Fimg\u002Ftx\u002F457\u002F4571639111.jpg",path:ba},{title:"Кухні",image:"\u002Fimg\u002Ftx\u002F518\u002F5187281221.jpg",path:"\u002Fdom\u002Fkuhni\u002F"}],colorsProduct:[{id:be,title:ay,imageId:510741910,productPath:aL,sectionId:P,colorId:i,alias:"black",colorName:"Чорний",sizeId:a,sizeName:a,sizeChart:a,pathImg:bH,pathImgSmall:bI,pathImgBig:bJ,path:aj},{id:bN,title:bO,imageId:510741934,productPath:"minola-hbi-6473-wh-glass-800-led-line",sectionId:P,colorId:B,alias:"whitebeige",colorName:"Білий",sizeId:a,sizeName:a,sizeChart:a,pathImg:bQ,pathImgSmall:"\u002Fimg\u002Ftx\u002F510\u002F510741934_s265.jpg",pathImgBig:"\u002Fimg\u002Ftx\u002F510\u002F5107419345.jpg",path:bP}],sizesProduct:[],sizeChart:a,videoInstagramHash:"B8q-pSvHjAP",guide:{title:al,url:"\u002Fguides\u002Fbt\u002Fvytyazhki\u002F"},quantity:K,barcode:"5905538402003",lastHistoryPrice:6850,lastHistoryDate:"2025-05-29",lastHistoryCurrency:"UAH",hasStores:c,recommendedReviewsCount:e,notRecommendedReviewsCount:e,reviewsSpecificationRatings:[],colorReviewsSpecificationRatings:[],seo:{titleProduct:bb,descriptionProduct:bc,__typename:"SectionSeo"},offerCount:K,madeInUkraine:b,hasSeries:b,hasCrossSellingProducts:b,offersWithStoresCount:W,isArchived:b,__typename:"Product"},guides:{rubricsConfig:{kak_vybrat:{color:"#6F9FEC",icon:"guides\u002Fkak_vybrat"},scho_podaruvaty:{color:"#FD6A7E",icon:"guides\u002Fscho_podaruvaty"},video:{alternativeColor:"#555",alternativeColorDark:"#d2d2d2",color:"#E57373",icon:"guides\u002Fvideo"},"top-10":{color:"#F4BD00",icon:"guides\u002Ftop-10"},materialy_podborki:{color:"#FF8080",icon:"guides\u002Fmaterialy_podborki"},materialy_sravneniya:{color:"#98BF31",icon:"guides\u002Fmaterialy_sravneniya"},materialy_podskazki:{color:"#AC80FF",icon:"guides\u002Fmaterialy_podskazki"},recepty:{color:"#FFA726",icon:"guides\u002Frecepty"}},guideId:E,catalogTitle:d,currentRubric:a,bannerAdvertising:{}},catalog:{_id:a,activeFormat:"row",advertItem:a,currentCrossSellingBrandFilterId:a,crossSellingBrandFilterId:a,crossSellingBrandProducts:[],crossSellingLoaded:c,similarCatalogProducts:[],filtersSelected:[],filtersCategoriesOpenState:{},filterTitleToSearch:d,loading:b,sort:"popularity",showFirst:a,filterReviews:E,page:i,pageReviews:i,searchPhrase:d,sectionUserProductFilters:[],selectedMinPrice:e,selectedMaxPrice:e,selectedUserFilterId:E,selectedUserFilterTitle:d,noProductsFound:b,filteredProductsCount:e,productsCount:e,keyForUpdate:e,keyForUpdateImmediate:e,faqType:au,isAdult:b,adultConfirmed:b,specialTypePage:E,showSimilarLinks:c,taggedCatalog:b,taggedCatalogId:E,taggedCatalogFiltersString:d,shouldSendFiltersBannerEvent:c,bannerAdvertising:{},feedback:{collection:[],stat:a},filters:[],guide:{},meta:{},popularQuery:[],popularQuestions:{},products:{collection:[],paginationInfo:{}},rating:{catalogData:a,ratingData:a,loading:b,date:a},seo:{},series:{_id:E,title:d,vendor:{title:d},loading:b,feedbackStatistic:{},serieTechSpecifications:[],serieTechSpecificationsList:[],popularProducts:{collection:[]},imageLinks:[]},siteZone:{},taggedSections:[],topFilters:{}},brands:{singleBrand:{reviews:[]}},home:{bannerAdvertising:{}},productQuestions:{allQuestions:{totalCount:e,collection:[]}},productReviews:{allReviews:{totalCount:e,collection:[]}},yp:{allReviews:{totalCount:e,collection:[]},bannerAdvertising:{},reviews:{totalCount:e,collection:[]},storeInfo:{storeInfo:{},mapPoints:[]}},i18n:{routeParams:{}}},serverRendered:c,routePath:"\u002Fua\u002Fbt-vytyazhki\u002Fminola-hbi-6473-bl-glass-800-led-line\u002F",config:{HOTLINE_HOST:"https:\u002F\u002Fhotline.ua",apolloEndpoint:"\u002F\u002Fhotline.ua\u002Fsvc\u002Ffrontend-api\u002Fgraphql",apolloSSREndpoint:"http:\u002F\u002Fgateway-api.gateway-api-12-production.svc.cluster.local\u002Ffrontend-api\u002Fgraphql",envConfig:{axios:{baseURL:bX,credentials:b,headers:{common:{"X-Requested-With":"XMLHttpRequest"}}},jsonRPCEndpoint:{tracking:"\u002Fsvc\u002Ftracking\u002Fjson-rpc",recaptcha:"\u002Fsvc\u002Frecaptcha",search:"\u002Fsvc\u002Fsearch\u002Fapi\u002Fjson-rpc"},graphEndpoint:{sales:"\u002Fsvc\u002Fsales\u002Fgraphql",salesSSR:"http:\u002F\u002Fsales.sales-29-production\u002Fgraphql",profile:"\u002Fsvc\u002Fprofile\u002Fgraphql",profileSSR:"http:\u002F\u002Fprofile.profile-39-production\u002Fgraphql"},GTM_containerId:"GTM-MLHSDC",turnstileSitekey:"0x4AAAAAAABLne3c1iZm7tRb",googleClientId:"450268490645-nrl7e3r98i9qk4mglmfee1i1blo32fi8.apps.googleusercontent.com",authFacebookId:"186640098032099",appleClientId:"com.ecommerce.hotline.auth",appleRedirectURI:"https:\u002F\u002Fhotline.ua\u002F"},searchSSREndpoint:"http:\u002F\u002Fsearch.search-19-production\u002Fapi\u002Fjson-rpc",_app:{basePath:bX,assetsPath:"\u002Ffrontend\u002F_nuxt\u002F",cdnURL:a}},colorMode:{preference:bY,value:bY,unknown:c,forced:b},apollo:{salesClient:Object.create(null),profileClient:Object.create(null),defaultClient:Object.create(null)}}}(null,false,true,"",0,"за тарифами перевізника","ProductValues","ProductValuesEdge",1,"новый","UA","OfferDelivery","Offer","OfferEdge","NP","Нова Пошта",6699,"з Києва","мес.","cash-on-delivery","от производителя","pay-card","0","Самовивіз в Києві","SLF",12,"Minola HBI 6473 BL GLASS 800 LED Line",5,25,"Minola",void 0,"non-vat","card-in-shop","y",66432,"vat",27,2,22,4,3,111,24,6,19,15,20,10,17,7,11,18,14,16,29,"немає",9,21,8,"1-2 дні",26,13,23,"\u002Fbt-vytyazhki\u002Fminola-hbi-6473-bl-glass-800-led-line\u002F","click","Витяжки","Витяжка Minola HBI 6473 BL GLASS 800 LED Line",81,"безкоштовно",8999,"ME","Meest ПОШТА","Minola HBI 6473 BL GLASS 800 LED LINE","Витяжка вбудована","catalog",598,"\u002Fbt\u002Fvytyazhki\u002F","vendor","HBI 6473 BL GLASS 800 LED LINE","Київ","UP","Укрпошта","card-card","HBI 6473 BL GLASS 800 LED Line",41,78,"Тип","600","є",329900,Array(2),"minola-hbi-6473-bl-glass-800-led-line","product-regular","normal",938,"stiralnye-i-sushilnye-mashiny","holodilniki","posudomoechnye-mashiny",30,"kuhonnye-plity-i-poverhnosti",35,40,"vytyazhki","duhovki",55,"aksessuary-dlya-stiralnyh-mashin","aksessuary-dlya-vytyazhek","Аксесуари для витяжок","\u002Fbt\u002Faksessuary-dlya-vytyazhek\u002F","Minola HBI 6473 BL GLASS 800 LED LINE купити в інтернет-магазині: ціни на витяжка вбудована HBI 6473 BL GLASS 800 LED LINE - відгуки та огляди, фото та характеристики. Порівняти пропозиції в Україні: Київ, Харків, Одеса, Дніпро на Hotline.ua","Minola Витяжка вбудована HBI 6473 BL GLASS 800 LED LINE ✓ПОРІВНЯЙ пропозиції всіх інтернет-магазинів і ОБЕРИ найвигідніше! ➤HOTLINE знає, де ДЕШЕВШЕ.","https:\u002F\u002Fhotline.ua\u002Fua\u002Fbt-vytyazhki\u002Fminola-hbi-6473-bl-glass-800-led-line\u002F",25888362,256,"з Харкова",76,"Київ, вул. Введенська 15 (Видача товару Київ Поділ)","150 грн","300 грн","Minola Витяжка Minola HBI 6473 BL GLASS 800 LED Line",53,116,54,"Київ, вул. Введенська 15 (ТЕХНОточка Київ)",315,"Витяжка повновбудована Minola HBI 6473 BL GLASS 800 LED Line","Minola Витяжка повновбудована Minola HBI 6473 BL GLASS 800 LED Line",219,48,68,6298,275,"Витяжка кухонна Minola HBI 6473 BL GLASS 800 LED Line","Minola Витяжка кухонна Minola HBI 6473 BL GLASS 800 LED Line","Тип монтажу","вбудована (в шафу)","Керування","сенсорне","проточний\u002Fциркуляційний","чорний","Безкоштовна доставка","\u002Fimg\u002Ftx\u002F510\u002F5107419101.jpg","\u002Fimg\u002Ftx\u002F510\u002F510741910_s265.jpg","\u002Fimg\u002Ftx\u002F510\u002F5107419105.jpg",739900,"Perfelli",61719,25888364,"HBI 6473 WH GLASS 800 LED LINE","\u002Fbt-vytyazhki\u002Fminola-hbi-6473-wh-glass-800-led-line\u002F","\u002Fimg\u002Ftx\u002F510\u002F5107419341.jpg","Weilor",179079,"Ширина","700 - 999","Режим воздухоочистки","Режим очищення повітря","\u002F","system"));</script>
    """
    
    print("🚀 Универсальное извлечение данных о товаре")
    print("=" * 50)
    
    # Извлекаем данные
    product_data = extract_product_info(html_content)
    
    if product_data:
        print("📦 НАЙДЕННЫЕ ДАННЫЕ:")
        
        # Основная информация
        if 'title' in product_data:
            print(f"📝 Название: {product_data['title']}")
        
        if 'vendor_title' in product_data:
            print(f"🏭 Бренд: {product_data['vendor_title']}")
        
        if 'product_id' in product_data:
            print(f"🆔 ID: {product_data['product_id']}")
        
        # Цены
        prices = []
        if 'min_price' in product_data:
            prices.append(f"min: {product_data['min_price']}")
        if 'max_price' in product_data:
            prices.append(f"max: {product_data['max_price']}")
        if prices:
            print(f"💰 Цены: {', '.join(prices)}")
        
        if 'offer_count' in product_data:
            print(f"🏪 Предложений: {product_data['offer_count']}")
        
        if 'category' in product_data:
            print(f"📂 Категория: {product_data['category']}")
        
        if 'url' in product_data:
            print(f"🔗 URL: {product_data['url']}")
        
        # Изображения
        if 'images' in product_data and product_data['images']:
            print(f"🖼️  Изображений: {len(product_data['images'])}")
            for i, img in enumerate(product_data['images'][:3], 1):
                print(f"   {i}. {img}")
        print(product_data['specifications'])
        # Характеристики
        if 'specifications' in product_data and product_data['specifications']:
            print(f"\n🔧 ХАРАКТЕРИСТИКИ ({len(product_data['specifications'])}):")
            for spec in product_data['specifications']:
                print(f"   • {spec['key']}: {spec['value']}")
        
        # Декодированные переменные (если есть интересные)
        if 'decoded_variables' in product_data and product_data['decoded_variables']:
            print(f"\n🔍 ДОПОЛНИТЕЛЬНО:")
            for key, value in list(product_data['decoded_variables'].items())[:3]:
                print(f"   • {key}: {value}")
        
    else:
        print("❌ Данные не найдены")
        print("Проверьте формат NUXT кода")

# Функция для работы с файлом
def extract_from_file(file_path):
    """Извлекает данные из файла"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Если это просто NUXT код без HTML тегов
        if content.strip().startswith('window.__NUXT__'):
            content = f"<script>{content}</script>"
        
        return extract_product_info(content)
        
    except FileNotFoundError:
        print(f"❌ Файл {file_path} не найден")
        return None
    except Exception as e:
        print(f"❌ Ошибка чтения файла: {e}")
        return None

if __name__ == "__main__":
    main()
    
    # # Пример работы с файлом
    # print("\n" + "=" * 50)
    # print("📁 Попытка чтения из файла paste.txt...")
    # file_data = extract_from_file('paste.txt')
    # if file_data:
    #     print("✅ Данные из файла извлечены!")
    #     if 'title' in file_data:
    #         print(f"Название: {file_data['title']}")