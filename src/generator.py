"""
Модуль генерации инфраструктурного кода (IaC).

Связывает извлеченный контекст из документации с пользовательским запросом,
формирует абстрактный системный промпт и обращается к API LLM для генерации.
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
    
    try:
        llm = get_llm()
        context = get_relevant_context(user_query, llm=llm, k=3)
        
        system_prompt = """Ты – профессиональный DevOps-архитектор. Твоя цель – генерировать конфигурационные файлы {iac_tool} на основе предоставленного контекста.

                        КОНТЕКСТ С КОРПОРАТИВНЫМИ ПРАВИЛАМИ:
                        ====================
                        {context}
                        ====================

                        ЖЕСТКИЕ ПРАВИЛА (STOP-RULES):
                        1. ВЫВОД: Выведи АБСОЛЮТНО ЧИСТЫЙ текст файла. СТРОГО ЗАПРЕЩАЕТСЯ использовать markdown-разметку (никаких ```hcl или ```yaml).
                        2. КОММЕНТАРИИ: Строго запрещено писать какие-либо пояснения, приветствия или комментарии до и после кода. Выдавай ТОЛЬКО рабочий синтаксис ресурсов и ничего более.
                        3. СТАНДАРТЫ: Ты обязан неукоснительно применять все найденные в контексте внутренние регламенты, стандарты и политики. Игнорирование любых требований из контекста категорически запрещено!
                        4. ФУНКЦИОНАЛЬНАЯ ПОЛНОТА: Код должен быть логически связанным и работоспособным. Используй свои внутренние знания о {iac_tool} и целевом облачном провайдере, чтобы самостоятельно добавить необходимые зависимости и сопутствующие ресурсы связности, без которых запрошенная инфраструктура не сможет функционировать.
                        5. ЕСЛИ ТЫ НАПИШЕШЬ ТЕКСТ ПОМИМО КОДА – СИСТЕМА УПАДЕТ. Твой ответ должен начинаться сразу с кода.
                        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{query}")
        ])
        
        chain = prompt | llm | StrOutputParser()
        
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