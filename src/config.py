"""
Конфигурационный модуль проекта.

Отвечает за загрузку переменных окружения, определение базовых путей
файловой системы и настройку глобального логирования.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(module)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.error("Переменная окружения GROQ_API_KEY не найдена.")
    raise ValueError("Отсутствует GROQ_API_KEY в файле .env")

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "docs"
DB_DIR = BASE_DIR / "vector_db"
OUTPUT_DIR = BASE_DIR / "output"

for directory in (DOCS_DIR, DB_DIR, OUTPUT_DIR):
    directory.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Директория проверена/создана: {directory}")