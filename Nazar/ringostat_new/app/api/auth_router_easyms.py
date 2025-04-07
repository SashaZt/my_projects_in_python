import os
import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel


# Создаем модель данных для авторизации
class AuthRequest(BaseModel):
    username: str
    password: str
    organization_id: int


# Создаем роутер
auth_router = APIRouter(
    prefix="/easyms/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)


@auth_router.post("/", status_code=200)
async def authorize(auth_data: AuthRequest):
    """
    Авторизация пользователя и запуск скрипта обработки бронирований.

    Принимает имя пользователя, пароль и ID организации.
    Запускает main.py с переданными учетными данными.
    """
    try:
        logger.debug(
            f"Запрос авторизации для пользователя: {auth_data.username} и организации: {auth_data.organization_id}"
        )

        # Определяем базовую директорию проекта
        project_root = Path("/opt/ringostat")

        # Относительные пути
        main_script_path = project_root / "app/client/easyms/main.py"
        python_interpreter = project_root / "venv/bin/python3"
        # Используем ID организации в имени PID файла

        # Проверяем существование файлов
        if not main_script_path.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Файл main.py не найден по пути {main_script_path}",
            )

        if not python_interpreter.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Python интерпретатор не найден по пути {python_interpreter}",
            )

        # Создаем pid файл для отслеживания процесса
        pid_dir = project_root / "app/client/easyms/run"
        pid_dir.mkdir(parents=True, exist_ok=True)
        pid_file = pid_dir / f"easyms_process_{auth_data.organization_id}.pid"

        # Проверяем, не запущен ли уже процесс
        if pid_file.exists():
            try:
                with open(pid_file, "r") as f:
                    old_pid = int(f.read().strip())
                try:
                    # Проверяем, существует ли процесс с таким PID
                    os.kill(old_pid, 0)
                    # Если мы дошли сюда, процесс существует
                    logger.info(f"Процесс уже запущен с PID {old_pid}")
                    return {
                        "status": "success",
                        "message": f"Процесс уже запущен с PID {old_pid}",
                        "pid": old_pid,
                    }
                except OSError:
                    # Процесса с таким PID нет, можно продолжать
                    logger.info(
                        f"PID-файл существует, но процесса {old_pid} нет. Запускаем новый процесс."
                    )
            except Exception as e:
                logger.error(f"Ошибка при чтении PID файла: {e}")
                # Продолжаем запуск нового процесса

        # Запускаем скрипт main.py в отдельном процессе с переданными параметрами
        process = subprocess.Popen(
            [
                str(python_interpreter),
                str(main_script_path),
                "--username",
                auth_data.username,
                "--password",
                auth_data.password,
                "--organization_id",
                str(auth_data.organization_id),
            ],
            # Запускаем в фоновом режиме
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,  # Создаем новую сессию, чтобы процесс не завершился при закрытии API
        )

        # Записываем PID процесса в файл
        with open(pid_file, "w") as f:
            f.write(str(process.pid))

        logger.info(f"Запущен процесс с PID {process.pid} из {main_script_path}")

        # Проверяем, что процесс запустился успешно
        try:
            # Проверяем существование процесса
            os.kill(process.pid, 0)
            return {
                "status": "success",
                "message": "Авторизация успешна, обработка бронирований запущена в фоновом режиме",
                "pid": process.pid,
            }
        except OSError:
            # Процесс не запустился
            raise HTTPException(
                status_code=500,
                detail="Не удалось запустить процесс обработки бронирований",
            )

    except Exception as e:
        logger.error(f"Ошибка при авторизации и запуске обработки: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Ошибка при обработке запроса: {str(e)}"
        )
