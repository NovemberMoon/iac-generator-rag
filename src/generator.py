"""
Модуль генерации конфигурационных файлов.

Связывает извлеченный контекст из документации с пользовательским запросом,
формирует системный промпт и обращается к API LLM для генерации IaC-кода.
"""

import os
import logging

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.chat_models import init_chat_model
from langchain_openai import ChatOpenAI

from src.config import LLM_PROVIDER, LLM_MODEL_NAME, CUSTOM_LLM_URL
from src.retriever import get_relevant_context

logger = logging.getLogger(__name__)

def clean_markdown(text: str) -> str:
    """Удаляет markdown-разметку из ответа нейросети."""
    lines = text.strip().split('\n')
    if lines and lines[0].strip().startswith("```"):
        lines.pop(0)
    if lines and lines[-1].strip().startswith("```"):
        lines.pop()
    return "\n".join(lines).strip()

def get_llm():
    """Универсальная фабрика для инициализации языковой модели."""
    if LLM_PROVIDER == "custom":
        return ChatOpenAI(
            base_url=CUSTOM_LLM_URL,
            api_key=os.getenv("CUSTOM_LLM_KEY", "not-needed"),
            model_name=LLM_MODEL_NAME,
            temperature=0
        )
    else:
        return init_chat_model(
            model=LLM_MODEL_NAME,
            model_provider=LLM_PROVIDER,
            temperature=0
        )

def generate_iac_script(user_query: str, iac_tool: str = "terraform") -> str:
    """
    Генерирует сценарий (IaC) на основе запроса и базы знаний RAG.
    
    Args:
        user_query (str): Описание требуемой инфраструктуры.
        iac_tool (str): Инструмент IaC (по умолчанию 'terraform').
        
    Returns:
        str: Сгенерированный код конфигурации.
    """
    logger.info(f"Генерация для {iac_tool.upper()} (Провайдер: {LLM_PROVIDER.upper()}, Модель: {LLM_MODEL_NAME})")
    
    context = get_relevant_context(user_query, k=3)
    
    llm = get_llm()
    
    system_prompt = """Ты опытный DevOps-инженер и системный архитектор. 
                    Твоя задача — писать конфигурационные файлы инфраструктуры как кода (IaC) для инструмента: {iac_tool}.

                    Используй СТРОГО следующую техническую документацию для написания кода:
                    ====================
                    {context}
                    ====================

                    ПРАВИЛА ГЕНЕРАЦИИ:
                    1. ЦЕЛЕВОЙ ПРОВАЙДЕР: Определи облачного провайдера (например, Yandex Cloud, AWS, Azure) из запроса пользователя. Если пользователь не указал провайдера явно, используй того, который описывается в переданном контексте документации.
                    2. ФОРМАТ: Выведи АБСОЛЮТНО ЧИСТЫЙ текст файла. СТРОГО ЗАПРЕЩАЕТСЯ использовать markdown-разметку (никаких ```hcl или ```yaml).
                    3. ЧИСТОТА КОДА: ЗАПРЕЩЕНО писать любые слова, комментарии или приветствия до или после кода. Выдавай ТОЛЬКО код конфигурации.
                    4. ДОСТОВЕРНОСТЬ: Опирайся на примеры из контекста. Если нужного ресурса нет в документации, используй свои знания (best practices) для выбранного провайдера.
                    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{query}")
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    try:
        response = chain.invoke({
            "context": context,
            "query": user_query,
            "iac_tool": iac_tool
        })
        logger.info("Генерация успешно завершена.")

        cleaned_response = clean_markdown(response)
        return cleaned_response
        
    except Exception as e:
        logger.error(f"Ошибка при обращении к LLM: {str(e)}")
        raise RuntimeError(f"Сбой компонента Generator: {str(e)}")