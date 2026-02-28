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
    """
    Инициализирует и возвращает объект языковой модели 
    в зависимости от выбранного провайдера.
    """
    provider = LLM_PROVIDER.lower()
    verify_ssl = os.getenv("CUSTOM_LLM_VERIFY_SSL", "true").lower() != "false"

    if provider == "custom":
        import httpx
        from langchain_openai import ChatOpenAI
        http_client = httpx.Client(verify=verify_ssl) if not verify_ssl else None
        return ChatOpenAI(
            base_url=CUSTOM_LLM_URL,
            api_key=os.getenv("CUSTOM_LLM_KEY", "not-needed"),
            model_name=LLM_MODEL_NAME,
            temperature=0,
            http_client=http_client
        )
        
    elif provider == "gigachat":
        from langchain_gigachat.chat_models import GigaChat
        return GigaChat(
            credentials=os.getenv("GIGACHAT_CREDENTIALS"),
            model=LLM_MODEL_NAME,
            verify_ssl_certs=verify_ssl,
            temperature=0
        )
        
    elif provider == "yandex":
        from langchain_community.chat_models import ChatYandexGPT
        return ChatYandexGPT(
            model_name=LLM_MODEL_NAME,
            temperature=0
            )
        
    else:
        return init_chat_model(
            model=LLM_MODEL_NAME,
            model_provider=provider,
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
    
    context = get_relevant_context(user_query, k=5)
    
    llm = get_llm()
    
    system_prompt = """Ты опытный DevOps-инженер и системный архитектор. 
                    Твоя задача — писать конфигурационные файлы инфраструктуры как кода (IaC) для инструмента: {iac_tool}.

                    Используй СТРОГО следующую техническую документацию для написания кода:
                    ====================
                    {context}
                    ====================

                    ПРАВИЛА ГЕНЕРАЦИИ (КРИТИЧЕСКИ ВАЖНО):
                    1. ЦЕЛЕВОЙ ПРОВАЙДЕР: Определи целевого провайдера (любую ИТ-платформу, сервис, систему или оборудование с доступным API) из запроса пользователя. Если провайдер не указан явно, используй того, который описывается в переданном контексте документации.
                    2. ФОРМАТ: Выведи АБСОЛЮТНО ЧИСТЫЙ текст файла. СТРОГО ЗАПРЕЩАЕТСЯ использовать markdown-разметку (никаких ```hcl или ```yaml).
                    3. ЧИСТОТА КОДА: ЗАПРЕЩЕНО писать ЛЮБЫЕ комментарии ВНУТРИ кода (строки с '#' или '//'). ЗАПРЕЩЕНО писать приветствия или пояснения текста до/после кода. Выдавай ТОЛЬКО рабочий синтаксис ресурсов и ничего более. 
                    4. КОРПОРАТИВНЫЕ СТАНДАРТЫ (АБСОЛЮТНЫЙ ПРИОРИТЕТ): В переданном контексте могут содержаться внутренние регламенты, политики безопасности, стандарты кодирования и обязательные параметры. Ты ОБЯЗАН самостоятельно выявить их и неукоснительно применить ко всем генерируемым ресурсам. Игнорирование любых требований или стандартов из контекста категорически запрещено!
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