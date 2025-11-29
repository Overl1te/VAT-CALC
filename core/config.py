# core/config.py
import json
from pathlib import Path
import re

# Пути по умолчанию
BASE_DIR = Path.home() / "Documents" / "vat"
PROJECTS_DIR = BASE_DIR / "projects"
CONFIG_FILE = BASE_DIR / "config.json"

# Значения по умолчанию
DEFAULT_CURRENT_VAT = 20.0
DEFAULT_FUTURE_VAT = 22.0

# Кеш конфигурации (будет заполнен при первом обращении)
_config_cache = None


def _load_config():
    """Внутренняя функция загрузки — вызывается один раз."""
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Приводим к float, на случай если кто-то записал строки
                if 'default_current_vat' in data:
                    data['default_current_vat'] = float(data['default_current_vat'])
                if 'default_future_vat' in data:
                    data['default_future_vat'] = float(data['default_future_vat'])
                _config_cache = data
                return data
    except Exception as e:
        # При любой ошибке — просто дефолты, но логируем в stderr (если нужно)
        print(f"[Config] Не удалось загрузить конфиг: {e}")

    _config_cache = {}
    return _config_cache


def get_projects_dir() -> Path:
    """Возвращает путь к папке проектов."""
    path_str = _load_config().get('projects_dir', str(PROJECTS_DIR))
    return Path(path_str)


def get_current_vat() -> float:
    return float(_load_config().get('default_current_vat', DEFAULT_CURRENT_VAT))


def get_future_vat() -> float:
    return float(_load_config().get('default_future_vat', DEFAULT_FUTURE_VAT))


# ========================
# Валидация имён проектов
# ========================

# Запрещённые символы в имени папки Windows
FORBIDDEN_CHARS = r'[<>:"/\\|?*\x00-\x1F]'
FORBIDDEN_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
}


def sanitize_project_name(name: str) -> str:
    """
    Очищает имя проекта от запрещённых символов и зарезервированных имён Windows.
    Возвращает безопасное имя для создания папки.
    """
    if not name:
        return "Новый_проект"

    # Убираем ведущие/конечные пробелы и точки
    name = name.strip(" .")

    # Заменяем запрещённые символы на подчёркивание
    name = re.sub(FORBIDDEN_CHARS, "_", name)

    # Убираем множественные подчёркивания
    name = re.sub(r'_+', '_', name)

    # Проверяем зарезервированные имена
    clean_upper = name.upper()
    if clean_upper in FORBIDDEN_NAMES or clean_upper.startswith("COM") or clean_upper.startswith("LPT"):
        name = "_" + name

    # Ограничиваем длину (Windows: 255 символов для пути, но папка — до 240 безопасно)
    if len(name) > 100:
        name = name[:97] + "..."

    return name.strip("_") or "Проект"