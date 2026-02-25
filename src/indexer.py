"""
Модуль векторизации технической документации.

Осуществляет чтение файлов документации из директории docs/,
разбиение текста на фрагменты (чанки), преобразование их в векторные 
представления (эмбеддинги) и сохранение в локальную базу данных Chroma.
"""

import os
import shutil
import logging
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from src.config import DOCS_DIR, DB_DIR

logger = logging.getLogger(__name__)

def create_vector_db() -> None:
    """
    Создает и сохраняет векторную базу данных на основе файлов из DOCS_DIR.
    
    Raises:
        RuntimeError: В случае ошибки при чтении файлов или создании БД.
    """
    logger.info("Запуск процесса индексации документации.")
    
    try:
        logger.info(f"Поиск Markdown-файлов в директории {DOCS_DIR}...")
        loader = DirectoryLoader(
            str(DOCS_DIR), 
            glob="**/*.md", 
            loader_cls=TextLoader,
            loader_kwargs={'autodetect_encoding': True}
        )
        documents = loader.load()

        if not documents:
            logger.warning("Директория с документацией пуста. Индексация прервана.")
            return

        logger.info(f"Успешно загружено документов: {len(documents)}")

        logger.info("Разбиение документов на текстовые фрагменты...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=300,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_documents(documents)
        logger.info(f"Сформировано текстовых фрагментов (чанков): {len(chunks)}")

        logger.info("Загрузка модели эмбеддингов (all-MiniLM-L6-v2)...")
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        if os.path.exists(DB_DIR):
            logger.info("Удаление предыдущей версии векторной базы данных...")
            shutil.rmtree(DB_DIR)

        logger.info("Построение индексов и сохранение в базу Chroma...")
        Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=str(DB_DIR)
        )
        logger.info("Векторная база данных успешно сформирована и сохранена.")

    except Exception as e:
        logger.error(f"Произошла ошибка в процессе индексации: {str(e)}")
        raise RuntimeError(f"Сбой индексации: {str(e)}")

if __name__ == "__main__":
    create_vector_db()