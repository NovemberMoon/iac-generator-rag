"""Модуль семантического поиска и извлечения контекста.

Реализует функционал поиска релевантных фрагментов документации
с использованием векторной базы данных Chroma и ручного алгоритма Query Expansion.
"""

import logging

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from src.config import DB_DIR

logger = logging.getLogger(__name__)


def get_relevant_context(query: str, llm=None, k: int = 3) -> str:
    """Извлекает релевантный контекст из векторной базы данных.

    Args:
        query (str): Исходный запрос пользователя.
        llm: Экземпляр языковой модели для генерации подзапросов (опционально).
        k (int): Количество извлекаемых фрагментов на каждый запрос.

    Returns:
        str: Объединенный текст извлеченных фрагментов документации.
             Возвращает пустую строку в случае критической ошибки.
    """
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )
        vector_db = Chroma(
            persist_directory=str(DB_DIR),
            embedding_function=embeddings
        )

        if llm is None:
            docs = vector_db.similarity_search(query, k=k)
        else:
            logger.info("Запуск алгоритма расширения запроса (Query Expansion)...")
            expansion_prompt = """Сгенерируй 4 альтернативных поисковых запроса для базы знаний корпоративных стандартов.
                                Исходный запрос пользователя: {query}

                                ПРАВИЛА ГЕНЕРАЦИИ ЗАПРОСОВ:
                                1. Первый запрос должен фокусироваться на политиках информационной безопасности и ограничениях для запрошенных компонентов.
                                2. Второй запрос должен искать административные и корпоративные стандарты.
                                3. Третий запрос должен быть направлен на технические требования и архитектурную связность.
                                4. Четвертый запрос должен искать правила оптимизации затрат и выбора тарифных планов для указанных компонентов.

                                Выведи строго 4 запроса. Каждый запрос с новой строки. Без нумерации, дефисов и дополнительных слов.
                                """

            try:
                response = llm.invoke(expansion_prompt)
                content = response.content if hasattr(response, 'content') else str(response)
                queries = content.strip().split('\n')
            except Exception as e:
                logger.warning(f"Ошибка генерации подзапросов: {str(e)}")
                queries = []

            queries.append(query)

            all_docs = []
            seen_contents = set()

            for q in queries:
                if not q.strip():
                    continue
                found_docs = vector_db.similarity_search(q.strip(), k=k)
                for d in found_docs:
                    if d.page_content not in seen_contents:
                        seen_contents.add(d.page_content)
                        all_docs.append(d)

            docs = all_docs
            logger.info(f"Успех! Извлечено {len(docs)} уникальных фрагментов базы знаний.")

        context = "\n\n---\n\n".join([doc.page_content for doc in docs])
        return context

    except Exception as e:
        logger.error(f"Ошибка при извлечении контекста: {str(e)}")
        raise RuntimeError(f"Сбой компонента Retriever: {str(e)}")