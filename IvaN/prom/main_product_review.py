import concurrent.futures
import json
import random
import time
from datetime import datetime
from pathlib import Path

import requests
from config.logger import logger
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

current_directory = Path.cwd()
json_review_directory = current_directory / "json_review"
config_directory = current_directory / "config"
json_review_directory.mkdir(parents=True, exist_ok=True)
proxy_file = config_directory / "proxy.json"
companies_file = config_directory / "result.json"
proxy_list = []


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


def parse_review_date(review_data):
    """Extract the year from the review date."""
    try:
        date_created = review_data.get("dateCreated")
        if date_created:
            return datetime.fromisoformat(date_created).year
        return None
    except (ValueError, TypeError):
        return None


def get_min_review_year(response_json):
    """Find the earliest review year in the response."""
    try:
        opinions = (
            response_json.get("data", {}).get("opinionListing", {}).get("opinions", [])
        )
        if not opinions:
            return None

        years = []
        for opinion in opinions:
            year = parse_review_date(opinion)
            if year:
                years.append(year)

        return min(years) if years else None
    except Exception as e:
        logger.error(f"Error parsing response: {e}")
        return None


@retry(
    retry=retry_if_exception_type(
        (requests.exceptions.RequestException, json.JSONDecodeError)
    ),
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
)
def fetch_reviews_page(company_id, page, headers, json_data_template):
    """Fetch a single page of reviews for a company."""
    json_data = json_data_template.copy()
    json_data["variables"]["companyId"] = company_id
    json_data["variables"]["page"] = page

    # Получаем случайный прокси
    proxies = get_random_proxy()

    response = requests.post(
        "https://prom.ua/graphql",
        headers=headers,
        json=json_data,
        proxies=proxies,  # Добавляем прокси
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def process_company_reviews(
    company_id, headers, json_data_template, json_review_directory
):
    """Process all relevant review pages for a company until reaching 2022."""
    logger.info(f"Processing company ID: {company_id}")
    page = 1

    while True:
        file_path = json_review_directory / f"company_review_{company_id}_{page}.json"

        # Skip if already processed
        if file_path.exists():
            logger.info(f"Пропуск существующего файла: {file_path}")
            page += 1
            continue

        try:
            # Add some randomized delay to avoid being detected as a bot
            time.sleep(random.uniform(0.2, 1.0))

            # Fetch the current page
            response_json = fetch_reviews_page(
                company_id, page, headers, json_data_template
            )

            # Check if we have reviews on this page
            opinions = (
                response_json.get("data", {})
                .get("opinionListing", {})
                .get("opinions", [])
            )
            if not opinions:
                logger.error(f"Больше нет отзывов о компании {company_id}")
                break

            # Get the minimum year from the current page
            min_year = get_min_review_year(response_json)

            # If we have reviews from 2023-2025, save the JSON
            if min_year and min_year >= 2023:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(response_json, f, ensure_ascii=False, indent=4)
                logger.info(
                    f"Сохраненные отзывы о компании {company_id}, страница {page} (минимальный год: {min_year})"
                )

            # Check if we've reached 2022 or earlier
            if min_year and min_year <= 2022:
                logger.info(f"Достигнут 2022 год для компании {company_id}, остановка")
                break

            # Check if there's a next page
            has_next_page = (
                response_json.get("data", {})
                .get("opinionListing", {})
                .get("hasNextPage", False)
            )
            if not has_next_page:
                logger.info(f"Больше нет страниц для компании{company_id}")
                break

            page += 1

        except Exception as e:
            logger.info(f"Ошибка обработки компании {company_id}, page {page}: {e}")
            break

    return company_id


def process_companies(company_list, max_workers=5):
    """Process multiple companies in parallel."""

    # Load your existing headers and query template from your code
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
        "x-apollo-operation-name": "CompanyListingQuery",
        "x-forwarded-proto": "https",
        "x-language": "ru",
        "x-requested-with": "XMLHttpRequest",
    }

    json_data_template = {
        "operationName": "OpinionsListQuery",
        "variables": {
            "filterByRating": None,
            "hasTextContent": None,
            "companyId": None,
            "perPage": 10,
            "sortType": "by_date",
            "sortOrder": "",
        },
        "query": "query OpinionsListQuery($companyId: Int!, $page: Int!, $perPage: Int!, $sortType: String, $sortOrder: String, $filterByRating: String = null, $hasTextContent: Boolean = null) {\n  context {\n    domain\n    __typename\n  }\n  company(id: $companyId) {\n    id\n    name\n    opinionStats {\n      id\n      opinionPositivePercent\n      opinionTotal\n      __typename\n    }\n    slug\n    __typename\n  }\n  opinionListing(\n    companyId: $companyId\n    page: $page\n    perPage: $perPage\n    sortType: $sortType\n    sortOrder: $sortOrder\n    filterByRating: $filterByRating\n    hasTextContent: $hasTextContent\n  ) {\n    id\n    hasNextPage\n    opinions {\n      ...CompanyOpinionQueryFragment\n      __typename\n    }\n    __typename\n  }\n  url {\n    createOpinionCommentUrlPost\n    editOpinionCommentUrlPost\n    deleteOpinionCommentUrlPost\n    __typename\n  }\n}\n\nfragment CompanyOpinionQueryFragment on Opinion {\n  id\n  authorName\n  author_user_id\n  orderedProducts {\n    id\n    nameForCatalog\n    urlForProductCatalog\n    product {\n      id\n      isAdult\n      __typename\n    }\n    __typename\n  }\n  tags {\n    id\n    title\n    __typename\n  }\n  images {\n    id\n    url(width: 1024, height: 1024)\n    __typename\n  }\n  video {\n    id\n    videoUrl\n    thumbnailImageUrl\n    __typename\n  }\n  commentWork\n  rating\n  publishedWithoutRating\n  company_id\n  linkedOrder {\n    id\n    userCabinetOrderUrl\n    __typename\n  }\n  isRemovedByModerator\n  isInApprovalPendingStatuses\n  deleteUrl\n  comments {\n    id\n    message\n    dateCreated\n    authorIsCompany\n    authorName\n    author_user_id\n    replies {\n      id\n      dateCreated\n      message\n      authorIsCompany\n      authorName\n      author_user_id\n      __typename\n    }\n    __typename\n  }\n  companyResponse {\n    id\n    message\n    __typename\n  }\n  dateCreated\n  isCommentingProhibited\n  isRemovedStatus\n  canBeModified\n  ...LikesRatingFragment\n  __typename\n}\n\nfragment LikesRatingFragment on Opinion {\n  userRatings {\n    likes\n    dislikes\n    currentUserRatingState\n    __typename\n  }\n  __typename\n}",
    }

    results = []

    # Process companies in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                process_company_reviews,
                company["companyId"],
                headers,
                json_data_template,
                json_review_directory,
            )
            for company in company_list
        ]

        for future in concurrent.futures.as_completed(futures):
            try:
                company_id = future.result()
                results.append(company_id)
            except Exception as e:
                logger.error(f"Error in thread: {e}")

    return results


def load_companies(file_path):
    """Load the list of companies from a JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading companies file: {e}")
        return []


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
