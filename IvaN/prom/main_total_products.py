import concurrent.futures
import csv
import json
import os
import random
import time
from datetime import datetime
from pathlib import Path
from threading import Lock

import requests
from config.logger import logger
from requests.exceptions import HTTPError, RequestException
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

# Настройка директорий
current_directory = Path.cwd()
json_products_directory = current_directory / "json_products"
config_directory = current_directory / "config"
config_directory.mkdir(parents=True, exist_ok=True)
json_products_directory.mkdir(parents=True, exist_ok=True)
proxy_file = config_directory / "proxy.json"
companies_file = config_directory / "result.json"
proxy_list = []

headers = {
    "accept": "*/*",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "cache-control": "no-cache",
    "content-type": "application/json",
    "dnt": "1",
    "origin": "https://prom.ua",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://prom.ua/c2718447-magazin-tovarov-evropy.html",
    "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "x-apollo-operation-name": "CompanyFiltersQuery",
    "x-forwarded-proto": "https",
    "x-language": "ru",
    "x-requested-with": "XMLHttpRequest",
}


def load_companies(file_path):
    """Load the list of companies from a JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading companies file: {e}")
        return []


def load_proxies():
    """
    Загружает список прокси-серверов из config.json
    """
    global proxy_list
    try:
        if proxy_file.exists():
            with open(proxy_file, "r") as f:
                config = json.load(f)

                # Проверяем формат данных в config.json
                if "proxy_server" in config and isinstance(
                    config["proxy_server"], list
                ):
                    proxy_list = config["proxy_server"]
                    logger.info(
                        f"Загружено {len(proxy_list)} прокси-серверов из config.json"
                    )
                else:
                    logger.warning("В config.json отсутствует список прокси-серверов")
        else:
            logger.warning("Файл config.json не найден")
    except Exception as e:
        logger.error(f"Ошибка при загрузке конфигурации прокси: {str(e)}")


def get_random_proxy():
    """
    Возвращает случайный прокси из списка
    """
    if not proxy_list:
        return None

    proxy_url = random.choice(proxy_list)
    # Удаляем лишние пробелы в URL прокси (если они есть)
    proxy_url = proxy_url.strip()

    return {"http": proxy_url, "https": proxy_url}


@retry(
    retry=retry_if_exception_type((RequestException, json.JSONDecodeError)),
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
)
def process_company(company):
    """Обработка одной компании с применением случайного прокси"""
    company_id = company["companyId"]
    company_slug = company["companySlug"]

    logger.info(f"Обработка компании: {company_id} ({company_slug})")

    try:
        # Получаем случайный прокси для этого запроса
        proxies = get_random_proxy()

        # Вызываем функцию get_json с прокси
        get_json_with_proxy(company_id, company_slug, proxies)

        return company_id
    except Exception as e:
        logger.error(f"Ошибка при обработке компании {company_id}: {e}")
        raise


def parse_review_date(review_data):
    """Extract the year from the review date."""
    try:
        date_created = review_data.get("dateCreated")
        if date_created:
            return datetime.fromisoformat(date_created).year
        return None
    except (ValueError, TypeError):
        return None


def get_json_with_proxy(company_id, company_slug, proxies):
    """Получение JSON с использованием прокси"""
    json_data = {
        "operationName": "TagListingQuery",
        "variables": {
            "regionId": None,
            "includePremiumAdvBlock": False,
            "params": {
                "page": "1",
                "binary_filters": [],
            },
            "alias": company_slug,
            "limit": 29,
            "offset": 29,
        },
        "query": "query TagListingQuery($alias: String!, $offset: Int, $limit: Int, $params: Any, $sort: String, $regionId: Int = null, $includePremiumAdvBlock: Boolean = false, $subdomain: String = null, $regionDelivery: String = null) {\n  context {\n    ...ContextFragment\n    promOplataEnabled\n    __typename\n  }\n  listing: tagListing(\n    alias: $alias\n    offset: $offset\n    limit: $limit\n    params: $params\n    sort: $sort\n    region: {id: $regionId, subdomain: $subdomain}\n  ) {\n    page {\n      mainWordMatch\n      mainEntityMatch\n      attributesMatch\n      categoryIds\n      ...ProductsListFragment\n      __typename\n    }\n    tag {\n      id\n      name\n      alias\n      indexedRegions {\n        id\n        name\n        nameF2\n        subdomain\n        __typename\n      }\n      metaTitle\n      metaDescription\n      metaCanonicalUrl\n      redirectUrl\n      __typename\n    }\n    tagRequested {\n      id\n      name\n      __typename\n    }\n    substitutedCategory {\n      id\n      alias\n      __typename\n    }\n    substitutedManufacturer {\n      id\n      alias\n      __typename\n    }\n    category {\n      id\n      caption\n      isRoot\n      alias\n      path {\n        id\n        isRoot\n        caption\n        alias\n        __typename\n      }\n      isService\n      url\n      __typename\n    }\n    productType\n    breadCrumbs {\n      items {\n        type\n        params\n        url\n        caption\n        __typename\n      }\n      lastItemClickable\n      __typename\n    }\n    topCategories {\n      id\n      name: caption\n      isWholesaleEnabled\n      url\n      alias\n      minPriceLocal\n      maxPriceLocal\n      __typename\n    }\n    pageLinks {\n      ...SeoLinkFragment\n      __typename\n    }\n    isCpaOnly\n    advSource\n    searchTermData {\n      isAdult\n      mainWord\n      mainEntity\n      attributes\n      categoryId\n      possibleCatSource\n      categoryProba\n      __typename\n    }\n    motors {\n      ...MotorsListingContextFragment\n      __typename\n    }\n    motorsAvailable\n    motorsGarageAvailable\n    __typename\n  }\n  region(region: {id: $regionId, subdomain: $subdomain}) {\n    id\n    name\n    nameF2\n    isCity\n    subdomain\n    __typename\n  }\n  regionDelivery: region(region: {subdomain: $regionDelivery}) {\n    id\n    name\n    nameF2\n    isCity\n    subdomain\n    __typename\n  }\n  country {\n    code\n    name\n    nameF2\n    domain\n    __typename\n  }\n  categoryByAlias: category(alias: $alias) {\n    id\n    alias\n    __typename\n  }\n  premiumAdvBlock(\n    tag: $alias\n    params: $params\n    offset: 0\n    limit: 10\n    is_listing: true\n  ) @include(if: $includePremiumAdvBlock) {\n    products {\n      ...SmallProductTileFragment\n      __typename\n    }\n    total\n    __typename\n  }\n}\n\nfragment ProductsListFragment on ListingPage {\n  total\n  isPaidListing\n  esQueryHash\n  isCpaOnlySearch\n  regionReset\n  article\n  lang\n  mainWordMatch\n  mainEntityMatch\n  notEnoughProducts\n  attributesMatch\n  ltrModelName\n  topHitsCategory {\n    id\n    path {\n      id\n      caption\n      __typename\n    }\n    __typename\n  }\n  seoTags {\n    ...SeoLinkFragment\n    __typename\n  }\n  seoManufacturers {\n    ...SeoLinkFragment\n    __typename\n  }\n  seoCategories {\n    ...SeoLinkFragment\n    __typename\n  }\n  seoPromotions {\n    ...SeoLinkFragment\n    __typename\n  }\n  seoTopTags {\n    ...SeoLinkFragment\n    __typename\n  }\n  seoTopLatestTags {\n    ...SeoLinkFragment\n    __typename\n  }\n  seoMotorsCategories {\n    ...SeoLinkFragment\n    __typename\n  }\n  products {\n    ...ProductsItemFragment\n    __typename\n  }\n  productsBadMatch {\n    ...ProductsItemFragment\n    __typename\n  }\n  companyIds\n  quickFilters {\n    name\n    title\n    measureUnit\n    values {\n      value\n      title\n      imageUrl(width: 200, height: 200)\n      __typename\n    }\n    __typename\n  }\n  quickPromoFilter {\n    name\n    values {\n      value\n      selected\n      icon\n      darkIcon\n      title\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment ProductsItemFragment on ProductItem {\n  product_item_id\n  algSource\n  ...ProductTileProductItemFragment\n  product {\n    id\n    labels {\n      isEvoPayEnabled\n      __typename\n    }\n    company {\n      id\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment ProductTileProductItemFragment on ProductItem {\n  product {\n    id\n    is14Plus\n    isService\n    ordersCount\n    presence {\n      presence\n      __typename\n    }\n    groupId\n    productTypeKey\n    priceOriginal\n    priceUSD\n    categoryId\n    categoryIds\n    company_id\n    discountedPrice\n    newModelId\n    productOpinionCounters {\n      rating\n      count\n      __typename\n    }\n    company {\n      id\n      segment\n      deliveryStats {\n        deliverySpeed\n        __typename\n      }\n      ...ProductTileCompanyDetailsFragment\n      __typename\n    }\n    category {\n      id\n      areModelsEnabled\n      forceProductContent\n      __typename\n    }\n    model {\n      id\n      name\n      urlText\n      images(width: 200, height: 200)\n      images400x400: images(width: 400, height: 400)\n      category {\n        id\n        isAdult\n        is14Plus\n        __typename\n      }\n      counters {\n        count\n        rating\n        __typename\n      }\n      __typename\n    }\n    payPartsPrice\n    payPartsButtonText\n    priceCurrencyLocalized\n    ...SchemaOrgProductFragment\n    ...ProductTilePromoLabelFragment\n    ...ProductTileImageFragment\n    ...ProductPresenceFragment\n    ...ProductPriceFragment\n    ...ConversionBlockProductFragment\n    ...FavoriteButtonFragment\n    __typename\n  }\n  shouldShowAsModel\n  ltrLog\n  score\n  advertWeight\n  productClickToken\n  isDisabled\n  keywordsStrict\n  productModel {\n    model_id\n    min_price\n    product_count\n    company_count\n    max_price\n    model_product_ids\n    __typename\n  }\n  algSource\n  advert {\n    token\n    price\n    campaignId\n    categoryId\n    source\n    clickUrl\n    ctr\n    otr\n    commission_rate_kind\n    advert_weight_adv\n    hash\n    commission_type\n    ...AdvDebugFragment\n    __typename\n  }\n  __typename\n}\n\nfragment SchemaOrgProductFragment on Product {\n  id\n  name: nameForCatalog\n  sku\n  imageForProductSchema: image(width: 200, height: 200)\n  urlForProductCatalog\n  categoryIds\n  priceCurrency\n  price\n  discountDays\n  discountedPrice\n  hasDiscount\n  isAdult\n  buyButtonDisplayType\n  measureUnitCommonCode\n  productOpinionCounters {\n    rating\n    count\n    __typename\n  }\n  wholesalePrices {\n    id\n    measureUnitCommonCode\n    minimumOrderQuantity\n    price\n    __typename\n  }\n  presence {\n    presence\n    __typename\n  }\n  company {\n    id\n    name\n    returnPolicy {\n      id\n      returnTerms\n      notRefundable\n      __typename\n    }\n    opinionStats {\n      id\n      opinionPositivePercent\n      opinionTotal\n      __typename\n    }\n    __typename\n  }\n  manufacturerInfo {\n    id\n    name\n    __typename\n  }\n  __typename\n}\n\nfragment ProductTilePromoLabelFragment on Product {\n  promoLabelBanner {\n    id\n    imageUrl(width: 640, height: 640)\n    imageDarkUrl(width: 640, height: 640)\n    imageWidth\n    imageHeight\n    text\n    __typename\n  }\n  __typename\n}\n\nfragment ProductTileImageFragment on Product {\n  id\n  image(width: 200, height: 200)\n  image400x400: image(width: 400, height: 400)\n  imageAlt: image(width: 640, height: 640)\n  is14Plus\n  isAdult\n  name: nameForCatalog\n  __typename\n}\n\nfragment ProductPresenceFragment on Product {\n  presence {\n    presence\n    isAvailable\n    isEnding\n    isOrderable\n    isUnknown\n    isWait\n    isPresenceSure\n    __typename\n  }\n  catalogPresence {\n    value\n    title\n    titleExt\n    titleUnavailable\n    availabilityDate\n    __typename\n  }\n  __typename\n}\n\nfragment ProductPriceFragment on Product {\n  id\n  price\n  priceCurrencyLocalized\n  hasDiscount\n  discountedPrice\n  noPriceText\n  measureUnit\n  priceFrom\n  discountDaysLabel\n  canShowPrice\n  wholesalePrices {\n    id\n    price\n    __typename\n  }\n  sellingType\n  __typename\n}\n\nfragment ConversionBlockProductFragment on Product {\n  id\n  company_id\n  discountedPrice\n  price\n  priceCurrencyLocalized\n  image(width: 200, height: 200)\n  name: nameForCatalog\n  signed_id\n  buyButtonDisplayType\n  report_start_chat_url\n  groupId\n  company {\n    id\n    isChatVisible\n    __typename\n  }\n  __typename\n}\n\nfragment FavoriteButtonFragment on Product {\n  id\n  isFavorite\n  newModelId\n  category {\n    id\n    areModelsEnabled\n    forceProductContent\n    __typename\n  }\n  __typename\n}\n\nfragment ProductTileCompanyDetailsFragment on Company {\n  id\n  name\n  slug\n  regionName\n  countryName\n  ...CompanyRatingFragment\n  __typename\n}\n\nfragment CompanyRatingFragment on Company {\n  id\n  inTopSegment\n  opinionStats {\n    id\n    opinionPositivePercent\n    opinionTotal\n    __typename\n  }\n  deliveryStats {\n    id\n    deliverySpeed\n    __typename\n  }\n  __typename\n}\n\nfragment AdvDebugFragment on Prosale {\n  campaignId\n  price\n  ctr\n  otr\n  commission_rate_kind\n  advert_weight_adv\n  advert_weight_els\n  score\n  __typename\n}\n\nfragment SeoLinkFragment on SeoLink {\n  id\n  name\n  alias\n  type\n  params\n  tagId\n  titleAttr\n  __typename\n}\n\nfragment ContextFragment on Context {\n  context_meta\n  countryCode\n  domain\n  currentOrigin\n  defaultCurrencyCode\n  countryCurrency\n  currentUserPersonal {\n    ...CurrentUserPersonalFragment\n    __typename\n  }\n  currentRegionId\n  __typename\n}\n\nfragment CurrentUserPersonalFragment on ContextUser {\n  id\n  phone\n  email\n  policyConsent\n  hasValidRidToken\n  hasVerifiedPhone\n  vidhukOpinionConsent\n  __typename\n}\n\nfragment SmallProductTileFragment on ProductItem {\n  product {\n    id\n    name\n    categoryId\n    groupId\n    categoryIds\n    productTypeKey\n    priceOriginal\n    image(width: 200, height: 200)\n    priceCurrency\n    urlForProductCatalog\n    company_id\n    canShowPrice\n    priceUSD\n    isAdult\n    is14Plus\n    labels {\n      isEvoPayEnabled\n      __typename\n    }\n    productOpinionCounters {\n      rating\n      count\n      __typename\n    }\n    company {\n      id\n      name\n      segment\n      opinionStats {\n        id\n        opinionPositivePercent\n        __typename\n      }\n      deliveryStats {\n        id\n        deliverySpeed\n        __typename\n      }\n      __typename\n    }\n    payPartsButtonText\n    newModelId\n    model {\n      id\n      urlText\n      name\n      images(width: 200, height: 200)\n      category {\n        id\n        isAdult\n        is14Plus\n        __typename\n      }\n      __typename\n    }\n    ...ProductPresenceFragment\n    ...ProductPriceFragment\n    ...FavoriteButtonFragment\n    ...SpaConversionButtonProductFragment\n    __typename\n  }\n  algSource\n  advert {\n    ...ProductItemAdvertFragment\n    __typename\n  }\n  productClickToken\n  shouldShowAsModel\n  __typename\n}\n\nfragment ProductItemAdvertFragment on Prosale {\n  clickUrl\n  categoryId\n  token\n  campaignId\n  source\n  price\n  ctr\n  otr\n  commission_rate_kind\n  advert_weight_adv\n  hash\n  commission_type\n  __typename\n}\n\nfragment SpaConversionButtonProductFragment on Product {\n  id\n  category {\n    id\n    areModelsEnabled\n    forceProductContent\n    __typename\n  }\n  newModelId\n  __typename\n}\n\nfragment MotorsListingContextFragment on MotorsListingContext {\n  userHasVehicles\n  userVehicleCount\n  needToSyncFromSessionToDb\n  selectedUserVehicle {\n    id\n    vehicleId\n    name\n    liters\n    fuelTypeText\n    dateFrom\n    dateTo\n    __typename\n  }\n  __typename\n}",
    }

    file_path = json_products_directory / f"products_{company_id}_{company_slug}.json"

    if file_path.exists():
        logger.info(f"Пропуск существующего файла: {file_path}")
        return

    # Добавляем задержку для избежания блокировки
    time.sleep(random.uniform(1, 3))

    # Используем прокси для запроса
    response = requests.post(
        "https://prom.ua/graphql",
        headers=headers,
        json=json_data,
        proxies=proxies,  # Используем переданный прокси
        timeout=30,
    )

    response.raise_for_status()

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(response.json(), f, ensure_ascii=False, indent=4)

    logger.info(f"Сохранены данные для компании {company_id} ({company_slug})")


def process_companies(companies, max_workers=10):
    """Многопоточная обработка компаний"""
    results = []

    logger.info(f"Запуск обработки {len(companies)} компаний в {max_workers} потоков")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Запускаем задачи на выполнение
        futures = [executor.submit(process_company, company) for company in companies]

        # Обрабатываем результаты по мере их завершения
        for future in concurrent.futures.as_completed(futures):
            try:
                company_id = future.result()
                results.append(company_id)
                logger.info(f"Завершена обработка компании {company_id}")
            except Exception as e:
                logger.error(f"Ошибка в потоке: {e}")

    return results


def main():
    # Define paths

    # Загружаем прокси
    load_proxies()

    # Если нет прокси, выходим
    if not proxy_list:
        logger.error("Нет доступных прокси, выход из программы")
        return

    # Load companies
    companies = load_companies(companies_file)
    if not companies:
        logger.error(
            "Компании не найдены или произошла ошибка при загрузке файла компаний"
        )
        return

    logger.info(f"Начинаем обрабатывать {len(companies)} компаний")
    processed = process_companies(companies, max_workers=10)
    logger.info(f"Завершено {len(processed)} компаний")


if __name__ == "__main__":
    main()
