"""
Модуль генерации конфигурационных файлов.

Связывает извлеченный контекст из документации с пользовательским запросом,
формирует системный промпт и обращается к API LLM для генерации IaC-кода.
"""

import logging
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.config import GROQ_API_KEY
from src.retriever import get_relevant_context

logger = logging.getLogger(__name__)

def generate_iac_script(user_query: str, iac_tool: str = "terraform") -> str:
    """
    Генерирует сценарий (IaC) на основе запроса и базы знаний RAG.
    
    Args:
        user_query (str): Описание требуемой инфраструктуры.
        iac_tool (str): Инструмент IaC (по умолчанию 'terraform').
        
    Returns:
        str: Сгенерированный код конфигурации.
    """
    logger.info(f"Инициализация генерации для инструмента: {iac_tool.upper()}")
    
    context = get_relevant_context(user_query, k=3)
    
    llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model_name="llama-3.3-70b-versatile",
        temperature=0
    )
    
    system_prompt = """Ты опытный DevOps-инженер и системный архитектор. 
                    Твоя задача – писать конфигурационные файлы инфраструктуры как кода (IaC) для инструмента: {iac_tool}.

                    Используй СТРОГО следующую техническую документацию:
                    {context}

                    Правила:
                    1. Выдавай ТОЛЬКО валидный код для {iac_tool}. Никаких приветствий, пояснений и текста "Вот ваш код:".
                    2. Не используй разметку markdown (тройные кавычки), выдавай чистый текст файла.
                    3. Если это terraform, пиши HCL код. Если ansible - пиши YAML.
                    4. Если ответа нет в документации, используй свои знания best practices.
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
            "query": user_query,
            "iac_tool": iac_tool
        })
        logger.info("Генерация успешно завершена.")
        return response
        
    except Exception as e:
        logger.error(f"Ошибка при обращении к LLM: {str(e)}")
        raise RuntimeError(f"Сбой компонента Generator: {str(e)}")