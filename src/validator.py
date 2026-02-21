"""
Модуль валидации сгенерированных сценариев инфраструктуры.

Осуществляет синтаксическую проверку кода перед его сохранением на диск.
"""

import yaml
import logging

logger = logging.getLogger(__name__)

def validate_yaml(content: str) -> bool:
    """
    Проверяет, является ли переданная строка валидным YAML форматом.
    
    Args:
        content (str): Строка со сгенерированным IaC кодом.
        
    Returns:
        bool: True, если синтаксис корректен, иначе False.
    """
    logger.info("Запуск проверки синтаксиса сгенерированного YAML-кода...")
    
    try:
        parsed_data = yaml.safe_load(content)
        
        if not parsed_data or not isinstance(parsed_data, dict):
            logger.warning("Сгенерированный код пуст или не является валидной структурой (словарем).")
            return False
            
        logger.info("✅ Синтаксис YAML корректен.")
        return True
        
    except yaml.YAMLError as exc:
        logger.error(f"❌ Ошибка валидации синтаксиса YAML: {exc}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    logger.info("ТЕСТ 1: Правильный YAML")
    good_yaml = """
services:
  web:
    image: nginx:alpine
    ports:
      - "80:80"
"""
    result_good = validate_yaml(good_yaml)
    print(f"Результат ТЕСТА 1: {result_good}\n")

    logger.info("ТЕСТ 2: Сломанный YAML (ошибка отступов)")
    bad_yaml = """
services:
  web:
    image: nginx:alpine
     ports:
      - "80:80"
"""
    result_bad = validate_yaml(bad_yaml)
    print(f"Результат ТЕСТА 2: {result_bad}")