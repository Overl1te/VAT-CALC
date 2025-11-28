import os
from pathlib import Path

# Базовые настройки
DEFAULT_CURRENT_VAT = 20.0
DEFAULT_FUTURE_VAT = 22.0
DEFAULT_YEARS_PROJECTION = 5
MAX_DISPLAY_ROWS = 1000
MAX_PROJECTION_YEARS = 10

# Пути для проектов
DOCUMENTS_DIR = Path.home() / "Documents"
PROJECTS_DIR = DOCUMENTS_DIR / "vat" / "projects"
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

# Поддерживаемые расширения
SUPPORTED_EXTENSIONS = ['.xlsx', '.xls', '.csv']