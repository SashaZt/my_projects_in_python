import json
import os
from pathlib import Path

# Пути к директориям
CURRENT_DIRECTORY = Path.cwd()
CONFIG_DIRECTORY = CURRENT_DIRECTORY / "config"
CONFIG_FILE = CONFIG_DIRECTORY / "config.json"

# Настройки Excel
DEFAULT_EXCEL_FILE = "thomann.xlsx"

# Настройки скрапинга
DEFAULT_HTML_DIR = "html_pages"
DEFAULT_JSON_DIR = "json_jobs"


# Настройки API
def get_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


# Загружаем конфигурацию
try:
    CONFIG = get_config()
    API_KEY = CONFIG["scraperapi"]["api_key"]

    # Загружаем настройки из конфига, если они есть
    settings_config = CONFIG.get("settings", {})

    # Настройки запросов
    REQUEST_TIMEOUT = settings_config.get("request_timeout", 30)
    RESULT_TIMEOUT = settings_config.get("result_timeout", 60)

    # Настройки повторных попыток
    MAX_JOB_CHECK_ATTEMPTS = settings_config.get("max_job_check_attempts", 10)
    JOB_CHECK_INTERVAL = settings_config.get("job_check_interval", 2)
    MAX_SUBMIT_RETRIES = settings_config.get("max_submit_retries", 3)
    CHECK_CYCLE_INTERVAL = settings_config.get("check_cycle_interval", 30)

    # Настройки параллельной обработки
    MAX_PARALLEL_CHECKS = settings_config.get("max_parallel_checks", 20)
    MAX_PARALLEL_SUBMITS = settings_config.get("max_parallel_submits", 10)
    CHECK_BATCH_SIZE = settings_config.get("check_batch_size", 50)

except Exception as e:
    print(f"Ошибка загрузки конфигурации: {str(e)}")
    # Используем значения по умолчанию
    API_KEY = os.environ.get("SCRAPER_API_KEY", None)

    # Настройки запросов
    REQUEST_TIMEOUT = 30
    RESULT_TIMEOUT = 60

    # Настройки повторных попыток
    MAX_JOB_CHECK_ATTEMPTS = 10
    JOB_CHECK_INTERVAL = 2
    MAX_SUBMIT_RETRIES = 3
    CHECK_CYCLE_INTERVAL = 30

    # Настройки параллельной обработки
    MAX_PARALLEL_CHECKS = 20
    MAX_PARALLEL_SUBMITS = 10
    CHECK_BATCH_SIZE = 50

# Убедитесь, что эти значения не меньше 1
MAX_PARALLEL_CHECKS = max(1, MAX_PARALLEL_CHECKS)
MAX_PARALLEL_SUBMITS = max(1, MAX_PARALLEL_SUBMITS)
CHECK_BATCH_SIZE = max(1, CHECK_BATCH_SIZE)
