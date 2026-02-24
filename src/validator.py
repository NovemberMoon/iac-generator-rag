"""
Модуль валидации сгенерированных сценариев инфраструктуры.

Поддерживает синтаксическую проверку YAML (Ansible) и HCL (Terraform)
"""

import yaml
import hcl2
import logging

logger = logging.getLogger(__name__)

def validate_iac(content: str, iac_tool: str) -> bool:
    """
    Проверяет валидность кода в зависимости от выбранного инструмента.
    
    Args:
        content (str): Сгенерированный код.
        iac_tool (str): Целевой инструмент ('terraform' или 'ansible').
        
    Returns:
        bool: True, если валидация пройдена.
    """
    logger.info(f"Запуск валидации кода для инструмента: {iac_tool.upper()}")
    
    if iac_tool == 'ansible':
        try:
            parsed_data = yaml.safe_load(content)
            if not parsed_data or not isinstance(parsed_data, (dict, list)):
                logger.warning("Сгенерированный код пуст или не является валидной структурой.")
                return False
            logger.info("Синтаксис YAML (Ansible) корректен.")
            return True
        except yaml.YAMLError as exc:
            logger.error(f"Ошибка парсинга YAML: {exc}")
            return False

    elif iac_tool == 'terraform':
        try:
            parsed_data = hcl2.loads(content)
            if not parsed_data:
                logger.warning("Сгенерированный код HCL пуст или не содержит структур данных.")
                return False
            logger.info("Синтаксис HCL (Terraform) корректен.")
            return True
        except Exception as exc:
            logger.error(f"Ошибка парсинга HCL (Terraform): {exc}")
            return False

    else:
        logger.warning(f"Неизвестный тип IaC: {iac_tool}. Валидация пропущена.")
        return True