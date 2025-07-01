# config/paths.py - обновленная версия
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from .config import Config


@dataclass
class ProjectPaths:
    """Управление путями проекта"""

    temp: Path  # ./temp/
    data: Path  # ./temp/data/
    json: Path  # ./temp/json/

    @classmethod
    def from_config(cls, config: "Config", base_dir: Path = None) -> "ProjectPaths":
        """Создает пути из конфигурации"""
        if base_dir is None:
            base_dir = Path.cwd()
        # Сначала создаем базовую temp директорию
        temp_base = base_dir / config.client.directories.temp

        # Создаем пути из конфигурации - все внутри temp
        paths = cls(
            temp=temp_base,
            data=temp_base / config.client.directories.data,
            json=temp_base / config.client.directories.json,
        )

        # Создаем все директории
        paths.create_directories()

        return paths

    def create_directories(self) -> None:
        """Создает все директории"""
        for field_name in self.__dataclass_fields__:
            path = getattr(self, field_name)
            if isinstance(path, Path):
                path.mkdir(parents=True, exist_ok=True)

    def get_file_path(self, directory: str, filename: str) -> Path:
        """Получает полный путь к файлу"""
        if not hasattr(self, directory):
            raise ValueError(f"Директория '{directory}' не найдена")

        dir_path = getattr(self, directory)
        return dir_path / filename

    def to_dict(self) -> Dict[str, Path]:
        """Возвращает словарь всех путей"""
        return {
            field_name: getattr(self, field_name)
            for field_name in self.__dataclass_fields__
        }

    def __str__(self) -> str:
        paths_info = []
        for name, path in self.to_dict().items():
            status = "✓" if path.exists() else "✗"
            # Показываем относительный путь от текущей директории
            try:
                relative_path = path.relative_to(Path.cwd())
            except ValueError:
                relative_path = path
            paths_info.append(f"  {name}: {relative_path} {status}")

        return "Project Paths:\n" + "\n".join(paths_info)
