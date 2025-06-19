# config/config.py
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv()


@dataclass
class DirectoriesConfig:
    """Конфигурация директорий"""

    temp: str
    data: str
    json: str
    html: str


@dataclass
class DiscountsConfig:
    """Конфигурация скидок"""

    retail_percent: int
    purchase_percent: int


@dataclass
class ExchangeRatesConfig:
    """Конфигурация валютных курсов"""

    eur_to_uah: float
    pln_to_uah: float


@dataclass
class FiltersConfig:
    """Конфигурация фильтров"""

    excluded_categories: List[str]
    stop_words: List[str]


@dataclass
class MarkupRule:
    """Правило наценки"""

    min: int
    max: int
    retail: float
    opt1: float
    opt2: float
    quantity1: int
    quantity2: int


@dataclass
class PriceRulesConfig:
    """Конфигурация ценовых правил"""

    rounding_precision: int
    markup_rules: List[MarkupRule]


@dataclass
class ShippingConfig:
    """Конфигурация доставки"""

    cost_per_kg_uah: int
    default_weight_kg: float


@dataclass
class TextReplacements:
    """Замены текста"""

    klarstein: str
    example_ru: str = ""
    example_ua: str = ""


@dataclass
class TextModificationLang:
    """Модификации текста для языка"""

    prefix_title: List[str]
    suffix_title: List[str]
    prefix_description: List[str]
    suffix_description: List[str]
    replacements: Dict[str, str]


@dataclass
class TextModificationsConfig:
    """Конфигурация текстовых модификаций"""

    ru: TextModificationLang
    ua: TextModificationLang


@dataclass
class ClientConfig:
    """Конфигурация для клиента"""

    proxy: str
    max_workers: int
    url_sitemap: str
    directories: DirectoriesConfig
    timeout: int
    delay_min: float
    delay_max: float
    retry_attempts: int
    retry_delay: float
    parser_interval_minutes: int
    translator_api_key: str
    discounts: DiscountsConfig
    exchange_rates: ExchangeRatesConfig
    filters: FiltersConfig
    price_rules: PriceRulesConfig
    shipping: ShippingConfig
    text_modifications: TextModificationsConfig
    user_agents: List[str] = None

    def __post_init__(self):
        """Инициализация user_agents после создания объекта"""
        if self.user_agents is None:
            self.user_agents = [
                # Google Chrome (Desktop)
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                # Mozilla Firefox (Desktop)
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:126.0) Gecko/20100101 Firefox/126.0",
                # Safari (Desktop)
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
                # Edge (Desktop)
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
            ]


@dataclass
class LogConfig:
    """Конфигурация логирования"""

    level: str
    rotation: str
    retention: str
    format_file: str
    format_console: str


@dataclass
class DbConfig:
    """Конфигурация базы данных"""

    user: str
    password: str
    name: str
    host: str
    port: int
    data_dir: str
    pgdata_path: str
    init_db: str
    max_connections: int
    shared_buffers: str
    effective_cache_size: str
    maintenance_work_mem: str
    checkpoint_completion_target: float
    wal_buffers: str
    default_statistics_target: int
    random_page_cost: float
    effective_io_concurrency: int
    work_mem: str
    min_wal_size: str
    max_wal_size: str
    max_parallel_workers_per_gather: int
    max_parallel_workers: int
    max_worker_processes: int


@dataclass
class Config:
    """Общая конфигурация приложения"""

    project_name: str
    version: str
    environment: str
    timezone: str
    client: ClientConfig
    logging: LogConfig
    db: DbConfig = None

    @classmethod
    def load(cls) -> "Config":
        """Загружает конфигурацию из доступных источников"""
        config_path = Path(".env")
        if config_path.exists():
            return cls.from_env()
        else:
            raise RuntimeError("Файл конфигурации .env не найден")

    @classmethod
    def _parse_json_env_var(cls, var_name: str, default_value: Any = None) -> Any:
        """Парсит JSON из переменной окружения"""
        value = os.getenv(var_name)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                print(f"Ошибка парсинга JSON в переменной {var_name}: {value}")
                return default_value
        return default_value

    @classmethod
    def _parse_markup_rules(cls, json_data: List[Dict]) -> List[MarkupRule]:
        """Парсит правила наценки из JSON"""
        if not json_data:
            return []

        rules = []
        for rule_data in json_data:
            rule = MarkupRule(
                min=rule_data.get("min", 0),
                max=rule_data.get("max", 0),
                retail=rule_data.get("retail", 1.0),
                opt1=rule_data.get("opt1", 1.0),
                opt2=rule_data.get("opt2", 1.0),
                quantity1=rule_data.get("quantity1", 0),
                quantity2=rule_data.get("quantity2", 0),
            )
            rules.append(rule)
        return rules

    @classmethod
    def from_env(cls) -> "Config":
        """Загружает конфигурацию из переменных окружения"""

        # Парсим JSON данные из env переменных
        excluded_categories = cls._parse_json_env_var(
            "CLIENT_FILTERS_EXCLUDED_CATEGORIES", []
        )
        stop_words = cls._parse_json_env_var("CLIENT_FILTERS_STOP_WORDS", [])
        markup_rules_data = cls._parse_json_env_var(
            "CLIENT_PRICE_RULES_MARKUP_RULES", []
        )

        # Текстовые модификации для RU
        ru_prefix_title = cls._parse_json_env_var(
            "CLIENT_TEXT_MODIFICATIONS_RU_PREFIX_TITLE", []
        )
        ru_suffix_title = cls._parse_json_env_var(
            "CLIENT_TEXT_MODIFICATIONS_RU_SUFFIX_TITLE", []
        )
        ru_prefix_description = cls._parse_json_env_var(
            "CLIENT_TEXT_MODIFICATIONS_RU_PREFIX_DESCRIPTION", []
        )
        ru_suffix_description = cls._parse_json_env_var(
            "CLIENT_TEXT_MODIFICATIONS_RU_SUFFIX_DESCRIPTION", []
        )

        # Текстовые модификации для UA
        ua_prefix_title = cls._parse_json_env_var(
            "CLIENT_TEXT_MODIFICATIONS_UA_PREFIX_TITLE", []
        )
        ua_suffix_title = cls._parse_json_env_var(
            "CLIENT_TEXT_MODIFICATIONS_UA_SUFFIX_TITLE", []
        )
        ua_prefix_description = cls._parse_json_env_var(
            "CLIENT_TEXT_MODIFICATIONS_UA_PREFIX_DESCRIPTION", []
        )
        ua_suffix_description = cls._parse_json_env_var(
            "CLIENT_TEXT_MODIFICATIONS_UA_SUFFIX_DESCRIPTION", []
        )

        return cls(
            project_name=os.getenv("PROJECT_NAME", ""),
            version=os.getenv("PROJECT_VERSION", ""),
            environment=os.getenv("PROJECT_ENVIRONMENT", ""),
            timezone=os.getenv("PROJECT_TIMEZONE", ""),
            client=ClientConfig(
                proxy=os.getenv("CLIENT_PROXY", ""),
                max_workers=int(os.getenv("CLIENT_MAX_WORKERS", "10")),
                url_sitemap=os.getenv("CLIENT_URL_SITEMAP", ""),
                directories=DirectoriesConfig(
                    temp=os.getenv("CLIENT_DIRECTORIES_TEMP", "temp"),
                    data=os.getenv("CLIENT_DIRECTORIES_DATA", "data"),
                    json=os.getenv("CLIENT_DIRECTORIES_JSON", "json"),
                    html=os.getenv("CLIENT_DIRECTORIES_HTML", "html"),
                ),
                timeout=int(os.getenv("CLIENT_TIMEOUT", "30")),
                delay_min=float(os.getenv("CLIENT_DELAY_MIN", "0.5")),
                delay_max=float(os.getenv("CLIENT_DELAY_MAX", "2.0")),
                retry_attempts=int(os.getenv("CLIENT_RETRY_ATTEMPTS", "3")),
                retry_delay=float(os.getenv("CLIENT_RETRY_DELAY", "1.0")),
                parser_interval_minutes=int(
                    os.getenv("CLIENT_PARSER_INTERVAL_MINUTES", "60")
                ),
                translator_api_key=os.getenv("CLIENT_TRANSLATOR_API_KEY", ""),
                discounts=DiscountsConfig(
                    retail_percent=int(
                        os.getenv("CLIENT_DISCOUNTS_RETAIL_PERCENT", "10")
                    ),
                    purchase_percent=int(
                        os.getenv("CLIENT_DISCOUNTS_PURCHASE_PERCENT", "5")
                    ),
                ),
                exchange_rates=ExchangeRatesConfig(
                    eur_to_uah=float(
                        os.getenv("CLIENT_EXCHANGE_RATES_EUR_TO_UAH", "47.8")
                    ),
                    pln_to_uah=float(
                        os.getenv("CLIENT_EXCHANGE_RATES_PLN_TO_UAH", "11.4")
                    ),
                ),
                filters=FiltersConfig(
                    excluded_categories=excluded_categories, stop_words=stop_words
                ),
                price_rules=PriceRulesConfig(
                    rounding_precision=int(
                        os.getenv("CLIENT_PRICE_RULES_ROUNDING_PRECISION", "2")
                    ),
                    markup_rules=cls._parse_markup_rules(markup_rules_data),
                ),
                shipping=ShippingConfig(
                    cost_per_kg_uah=int(
                        os.getenv("CLIENT_SHIPPING_COST_PER_KG_UAH", "57")
                    ),
                    default_weight_kg=float(
                        os.getenv("CLIENT_SHIPPING_DEFAULT_WEIGHT_KG", "5.0")
                    ),
                ),
                text_modifications=TextModificationsConfig(
                    ru=TextModificationLang(
                        prefix_title=ru_prefix_title,
                        suffix_title=ru_suffix_title,
                        prefix_description=ru_prefix_description,
                        suffix_description=ru_suffix_description,
                        replacements={
                            "klarstein": os.getenv(
                                "CLIENT_TEXT_MODIFICATIONS_RU_REPLACEMENTS_KLARSTEIN",
                                "",
                            ),
                            "example_ru": os.getenv(
                                "CLIENT_TEXT_MODIFICATIONS_RU_REPLACEMENTS_EXAMPLE_RU",
                                "",
                            ),
                        },
                    ),
                    ua=TextModificationLang(
                        prefix_title=ua_prefix_title,
                        suffix_title=ua_suffix_title,
                        prefix_description=ua_prefix_description,
                        suffix_description=ua_suffix_description,
                        replacements={
                            "klarstein": os.getenv(
                                "CLIENT_TEXT_MODIFICATIONS_UA_REPLACEMENTS_KLARSTEIN",
                                "",
                            ),
                            "example_ua": os.getenv(
                                "CLIENT_TEXT_MODIFICATIONS_UA_REPLACEMENTS_EXAMPLE_UA",
                                "",
                            ),
                        },
                    ),
                ),
            ),
            logging=LogConfig(
                level=os.getenv("CLIENT_LOG_LEVEL", "INFO"),
                rotation=os.getenv("CLIENT_LOG_ROTATION", "10 MB"),
                retention=os.getenv("CLIENT_LOG_RETENTION", "7 days"),
                format_file=os.getenv("CLIENT_LOG_FORMAT_FILE", ""),
                format_console=os.getenv("CLIENT_LOG_FORMAT_CONSOLE", ""),
            ),
            # DB конфигурация (опциональная, если есть в .env)
            db=(
                DbConfig(
                    user=os.getenv("DB_USER", ""),
                    password=os.getenv("DB_PASSWORD", ""),
                    name=os.getenv("DB_NAME", ""),
                    host=os.getenv("DB_HOST", "localhost"),
                    port=int(os.getenv("DB_PORT", "5432")),
                    data_dir=os.getenv("DB_DATA_DIR", "./pgdata"),
                    pgdata_path=os.getenv(
                        "DB_PGDATA_PATH", "/var/lib/postgresql/data/pgdata"
                    ),
                    init_db=os.getenv("DB_INIT_DB", "/var/lib/postgresql/wal"),
                    max_connections=int(os.getenv("DB_MAX_CONNECTIONS", "200")),
                    shared_buffers=os.getenv("DB_SHARED_BUFFERS", "1024MB"),
                    effective_cache_size=os.getenv("DB_EFFECTIVE_CACHE_SIZE", "1536MB"),
                    maintenance_work_mem=os.getenv("DB_MAINTENANCE_WORK_MEM", "256MB"),
                    checkpoint_completion_target=float(
                        os.getenv("DB_CHECKPOINT_COMPLETION_TARGET", "0.9")
                    ),
                    wal_buffers=os.getenv("DB_WAL_BUFFERS", "16MB"),
                    default_statistics_target=int(
                        os.getenv("DB_DEFAULT_STATISTICS_TARGET", "100")
                    ),
                    random_page_cost=float(os.getenv("DB_RANDOM_PAGE_COST", "1.1")),
                    effective_io_concurrency=int(
                        os.getenv("DB_EFFECTIVE_IO_CONCURRENCY", "300")
                    ),
                    work_mem=os.getenv("DB_WORK_MEM", "32MB"),
                    min_wal_size=os.getenv("DB_MIN_WAL_SIZE", "1GB"),
                    max_wal_size=os.getenv("DB_MAX_WAL_SIZE", "4GB"),
                    max_parallel_workers_per_gather=int(
                        os.getenv("DB_MAX_PARALLEL_WORKERS_PER_GATHER", "4")
                    ),
                    max_parallel_workers=int(os.getenv("DB_MAX_PARALLEL_WORKERS", "8")),
                    max_worker_processes=int(
                        os.getenv("DB_MAX_WORKER_PROCESSES", "16")
                    ),
                )
                if os.getenv("DB_USER")
                else None
            ),
        )


# Пример использования
if __name__ == "__main__":
    try:
        config = Config.load()
        print(f"Проект: {config.project_name}")
        print(f"Версия: {config.version}")
        print(f"Окружение: {config.environment}")
        print(f"Часовой пояс: {config.timezone}")
        print(f"Макс. воркеров: {config.client.max_workers}")
        print(f"Директория данных: {config.client.directories.data}")
        print(f"Курс EUR->UAH: {config.client.exchange_rates.eur_to_uah}")
        print(f"Скидка розница: {config.client.discounts.retail_percent}%")
        print(f"Правил наценки: {len(config.client.price_rules.markup_rules)}")

        if config.db:
            print(f"БД: {config.db.name}@{config.db.host}:{config.db.port}")

    except Exception as e:
        print(f"Ошибка загрузки конфигурации: {e}")
