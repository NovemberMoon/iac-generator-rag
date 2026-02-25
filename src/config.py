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

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "llama-3.3-70b-versatile")

CUSTOM_LLM_URL = os.getenv("CUSTOM_LLM_URL")

if LLM_PROVIDER == "custom" and not CUSTOM_LLM_URL:
    logger.warning("Выбран CUSTOM провайдер, но CUSTOM_LLM_URL не задан в .env")

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "docs"
DB_DIR = BASE_DIR / "vector_db"
OUTPUT_DIR = BASE_DIR / "output"

for directory in (DOCS_DIR, DB_DIR, OUTPUT_DIR):
    directory.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Директория проверена/создана: {directory}")