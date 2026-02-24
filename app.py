"""
Веб-интерфейс (Тонкий клиент) на базе Streamlit.

Служит для демонстрации работы REST API модуля генерации IaC.
Не содержит бизнес-логики генерации, общается с ядром через HTTP.
"""

import streamlit as st
import requests
from datetime import datetime

API_URL = "http://127.0.0.1:8080/api/v1/generate"

st.set_page_config(page_title="IaC RAG API Demo", page_icon="🤖", layout="wide")
st.title("🤖 RAG-генератор (API Web Client)")

with st.sidebar:
    st.header("⚙️ Настройки")
    iac_tool = st.selectbox(
        "Выберите целевой инструмент IaC:",
        ("terraform", "ansible")
    )
    st.info(
        "💡 **Архитектура:** Это приложение является лишь тонким клиентом. "
        "Вся магия RAG, обращение к LLM и строгая валидация (HCL/YAML) "
        "происходят под капотом в микросервисе REST API (FastAPI)."
    )

user_query = st.text_area(
    "Опишите целевую инфраструктуру:", 
    height=120,
    placeholder="Например: Создай виртуальную машину на Ubuntu с 2 ядрами и сетью..."
)

if st.button("🚀 Отправить API-запрос", type="primary"):
    if not user_query.strip():
        st.warning("Пожалуйста, введите запрос.")
    else:
        with st.spinner("Ожидание ответа от REST API (генерация и валидация)..."):
            try:
                response = requests.post(
                    API_URL, 
                    json={"query": user_query, "iac_tool": iac_tool},
                    proxies={"http": None, "https": None},
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    is_valid = data.get("is_valid")
                    code = data.get("code")
                    
                    if is_valid:
                        st.success(f"✅ Успешный ответ API. Синтаксис {iac_tool.upper()} проверен и полностью корректен!")
                        
                        lang = "hcl" if iac_tool == "terraform" else "yaml"
                        st.code(code, language=lang)
                        
                        ext = "tf" if iac_tool == "terraform" else "yml"
                        filename = f"main_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
                        
                        st.download_button(
                            label=f"⬇️ Скачать {filename}",
                            data=code,
                            file_name=filename,
                            mime="text/plain"
                        )
                    else:
                        st.error("❌ API сгенерировал код, но он не прошел строгую валидацию синтаксиса. Ошибка в структуре.")
                        st.code(code, language="text")
                else:
                    st.error(f"Ошибка API: {response.status_code} - {response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error(
                    "❌ Не удалось подключиться к REST API. "
                    "Убедитесь, что сервер FastAPI запущен в другом терминале командой: "
                    "`uvicorn src.api:app --reload`"
                )