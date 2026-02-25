"""
Интерфейс командной строки (CLI) для модуля RAG IaC.

Служит оберткой для прямого вызова ядра (генератора и валидатора) 
из консоли или CI/CD пайплайнов без необходимости поднимать веб-сервер.
"""

import argparse
import sys
import logging
from datetime import datetime

from src.generator import generate_iac_script
from src.validator import validate_iac
from src.config import OUTPUT_DIR

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.WARNING)

def main():
    """Основная функция обработки аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description="CLI утилита для AI-генерации инфраструктуры (IaC) с помощью RAG."
    )
    
    parser.add_argument(
        "-q", "--query", 
        type=str, 
        required=True, 
        help="Текстовый запрос (например: 'Создай ВМ на Ubuntu с 2 ядрами')"
    )
    
    parser.add_argument(
        "-t", "--tool", 
        type=str, 
        choices=["terraform", "ansible"], 
        default="terraform", 
        help="Целевой инструмент IaC (по умолчанию: terraform)"
    )
    
    parser.add_argument(
        "-s", "--save", 
        action="store_true", 
        help="Флаг для автоматического сохранения результата в папку output/"
    )

    args = parser.parse_args()

    print("=" * 60)
    print(f" 🚀 Запуск генерации IaC для: {args.tool.upper()}")
    print(f" ❓ Запрос: {args.query}")
    print("=" * 60)

    try:
        code = generate_iac_script(args.query, args.tool)
        
        is_valid = validate_iac(code, args.tool)

        print("\n--- ИТОГОВЫЙ КОД ---")
        print(code)
        print("--------------------\n")

        if is_valid:
            print("✅ СТАТУС: Синтаксис полностью корректен.")
            
            if args.save:
                ext = "tf" if args.tool == "terraform" else "yml"
                filename = f"{args.tool}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
                filepath = OUTPUT_DIR / filename
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(code)
                print(f"💾 Файл успешно сохранен: {filepath}")
                
            sys.exit(0)
        else:
            print("❌ СТАТУС: Ошибка структуры/синтаксиса.")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Критическая системная ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()