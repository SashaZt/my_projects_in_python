import asyncio
import json
import os
import subprocess
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

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


@app.post("/", response_class=HTMLResponse)
async def update_config(
    request: Request,
    proxy: str = Form(...),
    max_workers: int = Form(...),
    url_sitemap: str = Form(...),
    timeout: int = Form(...),
    delay_min: float = Form(...),
    delay_max: float = Form(...),
    retry_attempts: int = Form(...),
    retry_delay: float = Form(...),
    parser_interval_minutes: int = Form(...),
    translator_api_key: str = Form(...),
    eur_to_uah: float = Form(...),
    pln_to_uah: float = Form(...),
    cost_per_kg_uah: int = Form(...),
    default_weight_kg: float = Form(...),
):
    """Обновляет конфигурацию на основе данных формы"""

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
        # Делаем скрипт исполняемым
        os.chmod(START_SCRIPT, 0o755)

        # Запускаем скрипт в фоновом режиме
        parser_status["running"] = True
        parser_status["last_run"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        parser_status["output"] = "Запуск парсера..."

        # Запускаем процесс асинхронно
        process = await asyncio.create_subprocess_exec(
            "bash",
            START_SCRIPT,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd="/app",
        )

        # Не ждем завершения процесса, возвращаем ответ сразу
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
        return JSONResponse(
            status_code=500, content={"error": f"Ошибка запуска парсера: {str(e)}"}
        )


async def monitor_parser_process(process):
    """Мониторит процесс парсера"""
    try:
        stdout, _ = await process.communicate()
        parser_status["output"] = stdout.decode("utf-8", errors="ignore")
        parser_status["running"] = False
        print(f"Parser finished with return code: {process.returncode}")
    except Exception as e:
        parser_status["output"] = f"Ошибка выполнения: {str(e)}"
        parser_status["running"] = False
        print(f"Parser monitoring error: {e}")


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
