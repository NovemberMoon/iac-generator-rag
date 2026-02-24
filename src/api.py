"""
REST API интерфейс для модуля генерации IaC.

Обеспечивает интеграцию компонента со сторонними системами (CI/CD, Web UI).
"""

import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.generator import generate_iac_script
from src.validator import validate_iac

logger = logging.getLogger(__name__)

app = FastAPI(
    title="IaC RAG API",
    description="API для автоматизированной генерации инфраструктурных сценариев.",
    version="1.0.0"
)


class GenerateRequest(BaseModel):
    """Модель запроса на генерацию кода."""
    query: str = Field(..., description="Текстовый запрос пользователя")
    iac_tool: str = Field("terraform", description="Целевой инструмент (terraform или ansible)")


class GenerateResponse(BaseModel):
    """Модель ответа с результатами генерации."""
    tool: str
    is_valid: bool
    code: str


@app.post("/api/v1/generate", response_model=GenerateResponse)
async def generate_endpoint(request: GenerateRequest):
    """
    Основной эндпоинт генерации кода.
    """
    logger.info(f"API Request: Генерация для {request.iac_tool.upper()}")
    try:
        generated_code = generate_iac_script(request.query, request.iac_tool)
        is_valid = validate_iac(generated_code, request.iac_tool)

        return GenerateResponse(
            tool=request.iac_tool,
            is_valid=is_valid,
            code=generated_code
        )
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))