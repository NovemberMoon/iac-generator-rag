"""
Модуль генерации конфигурационных файлов.

Связывает извлеченный контекст из документации с пользовательским запросом,
формирует системный промпт и обращается к API LLM для генерации IaC-кода.
"""

import logging
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import GROQ_API_KEY
from retriever import get_relevant_context

logger = logging.getLogger(__name__)

def generate_iac_script(user_query: str) -> str:
    """
    Генерирует сценарий развертывания (IaC) на основе запроса и базы знаний RAG.
    
    Args:
        user_query (str): Описание требуемой инфраструктуры от пользователя.
        
    Returns:
        str: Сгенерированный конфигурационный файл.
    """
    logger.info("Инициализация процесса генерации IaC-сценария...")
    
    context = get_relevant_context(user_query, k=2)
    
    llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model_name="llama-3.3-70b-versatile",
        temperature=0
    )
    
    system_prompt = """Ты опытный DevOps-инженер. 
                    Твоя задача — писать конфигурационные файлы инфраструктуры как кода (IaC), например Docker Compose или Ansible.

                    Используй СТРОГО следующую техническую документацию для написания кода:
                    {context}

                    Правила:
                    1. Выдавай ТОЛЬКО код. Никаких приветствий, пояснений и текста "Вот ваш код:".
                    2. Не используй разметку markdown (тройные кавычки), выдавай чистый текст файла.
                    3. Если в документации нет ответа, опирайся на свои базовые знания DevOps.
                    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{query}")
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    logger.info("Отправка промпта в LLM-провайдер...")
    try:
        response = chain.invoke({
            "context": context,
            "query": user_query
        })
        logger.info("Генерация успешно завершена.")
        return response
        
    except Exception as e:
        logger.error(f"Ошибка при обращении к LLM: {str(e)}")
        raise RuntimeError(f"Сбой компонента Generator: {str(e)}")

if __name__ == "__main__":
    test_query = "Напиши docker-compose для базы данных PostgreSQL и веб-сервера Nginx"
    result = generate_iac_script(test_query)
    print(f"\nСГЕНЕРИРОВАННЫЙ КОД:\n\n{result}")