import asyncio
import json
import os
import subprocess
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Config Editor")
templates = Jinja2Templates(directory="templates")


# Умное определение пути к конфигу и скриптам
def get_config_path():
    """Определяет правильный путь к config.json"""
    possible_paths = [
        "/app/config.json",  # В Docker контейнере (монтированный)
        "../config.json",  # Относительно web папки
        "config.json",  # В текущей директории
        "/config.json",  # В корне файловой системы
    ]

    for path in possible_paths:
        if os.path.exists(path):
            print(f"Using config file: {path}")
            return path

    raise FileNotFoundError("config.json not found in any of the expected locations")


def get_start_script_path():
    """Определяет правильный путь к start.sh"""
    possible_paths = [
        "/app/start.sh",  # В Docker контейнере (монтированный)
        "../start.sh",  # Относительно web папки
        "start.sh",  # В текущей директории
        "/start.sh",  # В корне файловой системы
    ]

    for path in possible_paths:
        if os.path.exists(path):
            print(f"Using start script: {path}")
            return path

    raise FileNotFoundError("start.sh not found in any of the expected locations")


CONFIG_FILE = get_config_path()
START_SCRIPT = (
    get_start_script_path()
    if os.path.exists("/app/start.sh")
    or os.path.exists("../start.sh")
    or os.path.exists("start.sh")
    else None
)

# Глобальная переменная для отслеживания статуса парсера
parser_status = {"running": False, "last_run": None, "output": ""}


def load_config():
    """Загружает конфигурацию из файла"""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"Config file not found at {CONFIG_FILE}"
        )
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in config file")


def save_config(config_data):
    """Сохраняет конфигурацию в файл"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def get_xml_file_info():
    """Получает информацию о XML файле"""
    if os.path.exists(XML_EXPORT_PATH):
        stat = os.stat(XML_EXPORT_PATH)
        return {
            "exists": True,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "path": XML_EXPORT_PATH
        }
    else:
        return {
            "exists": False,
            "size": 0,
            "modified": None,
            "path": XML_EXPORT_PATH
        }


@app.get("/", response_class=HTMLResponse)
async def get_config_form(request: Request):
    """Отображает форму редактирования конфигурации"""
    config = load_config()
    client_config = config.get("client", {})

    return templates.TemplateResponse(
        "config_form.html",
        {
            "request": request,
            "config": client_config,
            "config_path": CONFIG_FILE,
            "start_script_available": START_SCRIPT is not None,
            "parser_status": parser_status,
        },
    )

@app.get("/download-xml")
async def download_xml():
    """Скачивание XML файла экспорта"""
    if not os.path.exists(XML_EXPORT_PATH):
        raise HTTPException(
            status_code=404, 
            detail=f"XML файл не найден по пути: {XML_EXPORT_PATH}"
        )
    
    return FileResponse(
        path=XML_EXPORT_PATH,
        filename="export_output.xml",
        media_type="application/xml",
        headers={"Content-Disposition": "attachment; filename=export_output.xml"}
    )


@app.get("/xml-info")
async def get_xml_info():
    """Возвращает информацию о XML файле в JSON формате"""
    return JSONResponse(content=get_xml_file_info())

@app.post("/", response_class=HTMLResponse)
async def update_config(request: Request):
    """Обновляет конфигурацию на основе данных формы"""
    
    # Получаем данные формы
    form_data = await request.form()
    
    # Извлекаем основные параметры
    proxy = form_data.get("proxy", "")
    max_workers = int(form_data.get("max_workers", 5))
    url_sitemap = form_data.get("url_sitemap", "")
    timeout = int(form_data.get("timeout", 30))
    delay_min = float(form_data.get("delay_min", 0.3))
    delay_max = float(form_data.get("delay_max", 1.0))
    retry_attempts = int(form_data.get("retry_attempts", 3))
    retry_delay = float(form_data.get("retry_delay", 2.0))
    parser_interval_minutes = int(form_data.get("parser_interval_minutes", 60))
    translator_api_key = form_data.get("translator_api_key", "")
    eur_to_uah = float(form_data.get("eur_to_uah", 47.8))
    pln_to_uah = float(form_data.get("pln_to_uah", 11.4))
    cost_per_kg_uah = int(form_data.get("cost_per_kg_uah", 5))
    default_weight_kg = float(form_data.get("default_weight_kg", 5.0))
    
    # Извлекаем дополнительные параметры
    excluded_categories = form_data.get("excluded_categories", "")
    stop_words = form_data.get("stop_words", "")
    ru_prefix_title = form_data.get("ru_prefix_title", "")
    ru_suffix_title = form_data.get("ru_suffix_title", "")
    ru_prefix_description = form_data.get("ru_prefix_description", "")
    ru_suffix_description = form_data.get("ru_suffix_description", "")
    ru_replacements = form_data.get("ru_replacements", "")
    ua_prefix_title = form_data.get("ua_prefix_title", "")
    ua_suffix_title = form_data.get("ua_suffix_title", "")
    ua_prefix_description = form_data.get("ua_prefix_description", "")
    ua_suffix_description = form_data.get("ua_suffix_description", "")
    ua_replacements = form_data.get("ua_replacements", "")
    rounding_precision = int(form_data.get("rounding_precision", 2))
    discounts = float(form_data.get("discounts", 0))

    # Загружаем текущую конфигурацию
    config = load_config()

    # Обновляем параметры client
    client_config = config.get("client", {})

    # Обновляем основные параметры
    client_config.update(
        {
            "proxy": proxy,
            "max_workers": max_workers,
            "url_sitemap": url_sitemap,
            "timeout": timeout,
            "delay_min": delay_min,
            "delay_max": delay_max,
            "retry_attempts": retry_attempts,
            "retry_delay": retry_delay,
            "parser_interval_minutes": parser_interval_minutes,
            "translator_api_key": translator_api_key,
        }
    )

    # Обновляем exchange_rates
    if "exchange_rates" not in client_config:
        client_config["exchange_rates"] = {}
    client_config["exchange_rates"].update(
        {"eur_to_uah": eur_to_uah, "pln_to_uah": pln_to_uah}
    )

    # Обновляем shipping
    if "shipping" not in client_config:
        client_config["shipping"] = {}
    client_config["shipping"].update(
        {"cost_per_kg_uah": cost_per_kg_uah, "default_weight_kg": default_weight_kg}
    )

    # Обновляем filters
    if "filters" not in client_config:
        client_config["filters"] = {}
    
    # Преобразуем строки в списки
    excluded_categories_list = [item.strip() for item in excluded_categories.split(",") if item.strip()] if excluded_categories else []
    stop_words_list = [item.strip() for item in stop_words.split(",") if item.strip()] if stop_words else []
    
    client_config["filters"].update({
        "excluded_categories": excluded_categories_list,
        "stop_words": stop_words_list
    })

    # Обновляем text_modifications
    if "text_modifications" not in client_config:
        client_config["text_modifications"] = {}
    
    # Русские модификации
    if "ru" not in client_config["text_modifications"]:
        client_config["text_modifications"]["ru"] = {}
    
    ru_prefix_title_list = [item.strip() for item in ru_prefix_title.split(",") if item.strip()] if ru_prefix_title else []
    ru_suffix_title_list = [item.strip() for item in ru_suffix_title.split(",") if item.strip()] if ru_suffix_title else []
    ru_prefix_description_list = [item.strip() for item in ru_prefix_description.split(",") if item.strip()] if ru_prefix_description else []
    ru_suffix_description_list = [item.strip() for item in ru_suffix_description.split(",") if item.strip()] if ru_suffix_description else []
    
    # Обрабатываем замены для русского
    ru_replacements_dict = {}
    if ru_replacements:
        for pair in ru_replacements.split(","):
            if "=" in pair:
                key, value = pair.split("=", 1)
                ru_replacements_dict[key.strip()] = value.strip()
    
    client_config["text_modifications"]["ru"].update({
        "prefix_title": ru_prefix_title_list,
        "suffix_title": ru_suffix_title_list,
        "prefix_description": ru_prefix_description_list,
        "suffix_description": ru_suffix_description_list,
        "replacements": ru_replacements_dict
    })

    # Украинские модификации
    if "ua" not in client_config["text_modifications"]:
        client_config["text_modifications"]["ua"] = {}
    
    ua_prefix_title_list = [item.strip() for item in ua_prefix_title.split(",") if item.strip()] if ua_prefix_title else []
    ua_suffix_title_list = [item.strip() for item in ua_suffix_title.split(",") if item.strip()] if ua_suffix_title else []
    ua_prefix_description_list = [item.strip() for item in ua_prefix_description.split(",") if item.strip()] if ua_prefix_description else []
    ua_suffix_description_list = [item.strip() for item in ua_suffix_description.split(",") if item.strip()] if ua_suffix_description else []
    
    # Обрабатываем замены для украинского
    ua_replacements_dict = {}
    if ua_replacements:
        for pair in ua_replacements.split(","):
            if "=" in pair:
                key, value = pair.split("=", 1)
                # Проверяем, является ли значение списком (если содержит дополнительные запятые)
                if "," in value and "=" not in value:
                    ua_replacements_dict[key.strip()] = [v.strip() for v in value.split(",")]
                else:
                    ua_replacements_dict[key.strip()] = value.strip()
    
    client_config["text_modifications"]["ua"].update({
        "prefix_title": ua_prefix_title_list,
        "suffix_title": ua_suffix_title_list,
        "prefix_description": ua_prefix_description_list,
        "suffix_description": ua_suffix_description_list,
        "replacements": ua_replacements_dict
    })

    # Обновляем price_rules
    if "price_rules" not in client_config:
        client_config["price_rules"] = {}
    
    # Обрабатываем markup_rules
    markup_rules = []
    rule_index = 0
    
    while f"rule_{rule_index}_min" in form_data:
        try:
            rule = {
                "min": int(form_data[f"rule_{rule_index}_min"]),
                "max": int(form_data[f"rule_{rule_index}_max"]),
                "retail": float(form_data[f"rule_{rule_index}_retail"]),
                "opt1": float(form_data[f"rule_{rule_index}_opt1"]),
                "opt2": float(form_data[f"rule_{rule_index}_opt2"]),
                "quantity1": int(form_data[f"rule_{rule_index}_quantity1"]),
                "quantity2": int(form_data[f"rule_{rule_index}_quantity2"])
            }
            markup_rules.append(rule)
        except (ValueError, KeyError) as e:
            print(f"Error processing rule {rule_index}: {e}")
        
        rule_index += 1
    
    client_config["price_rules"].update({
        "rounding_precision": rounding_precision,
        "discounts": discounts,
        "markup_rules": markup_rules
    })

    # Сохраняем обновленную конфигурацию
    config["client"] = client_config

    if save_config(config):
        success_message = "Конфигурация успешно сохранена!"
        return templates.TemplateResponse(
            "config_form.html",
            {
                "request": request,
                "config": client_config,
                "success_message": success_message,
                "config_path": CONFIG_FILE,
                "start_script_available": START_SCRIPT is not None,
                "parser_status": parser_status,
            },
        )
    else:
        error_message = "Ошибка при сохранении конфигурации!"
        return templates.TemplateResponse(
            "config_form.html",
            {
                "request": request,
                "config": client_config,
                "error_message": error_message,
                "config_path": CONFIG_FILE,
                "start_script_available": START_SCRIPT is not None,
                "parser_status": parser_status,
            },
        )
        
@app.get("/config/json")
async def get_config_json():
    """Возвращает текущую конфигурацию в формате JSON"""
    config = load_config()
    return config


@app.post("/start-parser")
async def start_parser():
    """Запускает парсер через start.sh скрипт"""
    if not START_SCRIPT:
        raise HTTPException(status_code=404, detail="Start script not found")

    if parser_status["running"]:
        return JSONResponse(status_code=400, content={"error": "Парсер уже запущен"})

    try:
        # Проверяем что файл существует
        if not os.path.exists(START_SCRIPT):
            raise Exception(f"Файл {START_SCRIPT} не найден")
            
        # Делаем скрипт исполняемым
        os.chmod(START_SCRIPT, 0o755)

        parser_status["running"] = True
        parser_status["last_run"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        parser_status["output"] = "Запуск парсера..."

        print(f"Starting script: {START_SCRIPT}")
        
        # Запускаем процесс асинхронно с отдельным stderr
        process = await asyncio.create_subprocess_exec(
            "bash",
            START_SCRIPT,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,  # Отдельно перехватываем ошибки
            cwd=os.path.dirname(START_SCRIPT) or "/app",  # Запускаем из директории скрипта
        )

        # Запускаем мониторинг
        asyncio.create_task(monitor_parser_process(process))

        return JSONResponse(
            content={
                "message": "Парсер успешно запущен",
                "status": "running", 
                "started_at": parser_status["last_run"],
            }
        )

    except Exception as e:
        parser_status["running"] = False
        parser_status["output"] = f"Ошибка запуска: {str(e)}"
        print(f"Error starting parser: {e}")
        return JSONResponse(
            status_code=500, content={"error": f"Ошибка запуска парсера: {str(e)}"}
        )


async def monitor_parser_process(process):
    """Мониторит процесс парсера"""
    try:
        stdout, stderr = await process.communicate()
        output = stdout.decode("utf-8", errors="ignore")
        if stderr:
            output += "\nSTDERR:\n" + stderr.decode("utf-8", errors="ignore")
        
        parser_status["output"] = output
        parser_status["running"] = False
        print(f"Parser finished with return code: {process.returncode}")
        print(f"Parser output: {output}")
        
        if process.returncode != 0:
            print(f"Parser failed with exit code: {process.returncode}")
            
    except Exception as e:
        parser_status["output"] = f"Ошибка выполнения: {str(e)}"
        parser_status["running"] = False
        print(f"Parser monitoring error: {e}")


def get_xml_export_path():
    """Определяет путь к XML файлу экспорта"""
    possible_paths = [
        "/app/client/export_output.xml",  # В Docker контейнере
        "../client/export_output.xml",  # Относительно web папки
        "client/export_output.xml",  # В текущей директории
        "/client/export_output.xml",  # В корне
        "./export_output.xml",  # В текущей директории веб-приложения
    ]

    for path in possible_paths:
        if os.path.exists(path):
            print(f"Found XML export file: {path}")
            return path

    # Возвращаем наиболее вероятный путь, даже если файл не существует
    return "/app/client/export_output.xml"


CONFIG_FILE = get_config_path()
START_SCRIPT = (
    get_start_script_path()
    if os.path.exists("/app/start.sh")
    or os.path.exists("../start.sh")
    or os.path.exists("start.sh")
    else None
)
XML_EXPORT_PATH = get_xml_export_path()

@app.get("/parser-status")
async def get_parser_status():
    """Возвращает текущий статус парсера"""
    return JSONResponse(content=parser_status)


@app.post("/stop-parser")
async def stop_parser():
    """Останавливает парсер (базовая реализация)"""
    # Простая реализация - сбрасываем статус
    # В продакшене здесь можно добавить более сложную логику остановки процесса
    parser_status["running"] = False
    parser_status["output"] += "\n[STOPPED] Парсер остановлен пользователем"

    return JSONResponse(
        content={"message": "Команда остановки отправлена", "status": "stopped"}
    )


@app.get("/health")
async def health_check():
    """Проверка здоровья приложения"""
    return {
        "status": "healthy",
        "config_file": CONFIG_FILE,
        "config_exists": os.path.exists(CONFIG_FILE),
        "start_script": START_SCRIPT,
        "start_script_exists": START_SCRIPT is not None
        and os.path.exists(START_SCRIPT),
        "parser_running": parser_status["running"],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
