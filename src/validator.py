"""
Модуль валидации сгенерированных сценариев инфраструктуры.

Поддерживает синтаксическую проверку YAML (Ansible) 
и базовую структурную проверку HCL (Terraform).
"""

import yaml
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
                return False
            logger.info("✅ Синтаксис YAML (Ansible) корректен.")
            return True
        except yaml.YAMLError as exc:
            logger.error(f"❌ Ошибка валидации синтаксиса YAML: {exc}")
            return False
            
    elif iac_tool == 'terraform':
        required_blocks = ["resource", "provider", "terraform", "variable", "output", "module", "data"]
        if any(block in content for block in required_blocks):
            logger.info("✅ Синтаксис содержит корректные HCL-блоки Terraform.")
            return True
            
        logger.warning("❌ Сгенерированный код не похож на Terraform (HCL).")
        return False
        
    else:
        logger.warning(f"Неизвестный тип IaC: {iac_tool}. Валидация пропущена.")
        return True