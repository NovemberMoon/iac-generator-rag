"""
Модуль поиска (Retriever) для системы RAG.

Отвечает за подключение к существующей векторной базе данных Chroma,
векторизацию пользовательского запроса и поиск наиболее релевантных 
фрагментов документации на основе косинусного сходства векторов.
"""

import logging
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from config import DB_DIR

logger = logging.getLogger(__name__)

def get_relevant_context(query: str, k: int = 3) -> str:
    """
    Выполняет семантический поиск по векторной базе данных.
    
    Args:
        query (str): Запрос пользователя.
        k (int): Количество возвращаемых релевантных фрагментов.
        
    Returns:
        str: Объединенный текст найденных фрагментов.
    """
    logger.info(f"Выполнение поиска по базе для запроса: '{query}'")
    
    try:
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vector_db = Chroma(
            persist_directory=str(DB_DIR), 
            embedding_function=embeddings
        )
        
        docs = vector_db.similarity_search(query, k=k)
        
        if not docs:
            logger.warning("Поиск не дал результатов.")
            return ""
            
        logger.info(f"Найдено {len(docs)} релевантных фрагментов документации.")
        context = "\n\n".join([doc.page_content for doc in docs])
        
        return context
        
    except Exception as e:
        logger.error(f"Ошибка при поиске в векторной базе: {str(e)}")
        raise RuntimeError(f"Сбой компонента Retriever: {str(e)}")