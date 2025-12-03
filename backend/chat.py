import os
import requests
from dotenv import load_dotenv
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

from database import save_message, get_history, trim_history

load_dotenv()
api_key = os.getenv("API_KEY")

def process_user_query(session_id: str, user_query: str):
    """
    Обрабатывает запрос пользователя через GigaChat, сохраняя историю сообщений в SQLite:
        1. Сохраняет сообщение пользователя в базу данных.
        2. Загружает последние 10 сообщений истории сессии.
        3. Преобразует историю сообщений в формат `Messages` для GigaChat.
        4. Добавляет текущий запрос пользователя к истории.
        5. Отправляет все сообщения в GigaChat и получает ответ.
        6. Сохраняет ответ модели в базе данных.
        7. Обрезает историю до последних 10 сообщений.

    Args:
        session_id (str): уникальный идентификатор сессии пользователя.
        user_query (str): текст запроса пользователя.

    Returns:
        dict: словарь с ключом "response", содержащий текст ответа модели.
    """
    api_key = os.getenv("API_KEY")

    history = get_history(session_id)
    messages = []
    for message in history:
        role, content = message["role"], message["content"]
        if role == "user":
            messages.append(Messages(role=MessagesRole.USER, content=content))
        else:
            messages.append(Messages(role=MessagesRole.ASSISTANT, content=content))

    # текущий запрос пользователя
    messages.append(Messages(role=MessagesRole.USER, content=user_query))

    chat_request = Chat(messages=messages)

    with GigaChat(credentials=api_key, verify_ssl_certs=False, model="GigaChat") as giga:
        response = giga.chat(chat_request)

    bot_reply = response.choices[0].message.content

    save_message(session_id, "user", user_query)
    save_message(session_id, "assistant", bot_reply)

    trim_history(session_id)

    return {"response": bot_reply}


QWEN_SERVER_URL = os.getenv("QWEN_SERVER_URL", "http://localhost:8001")

def process_qwen_query(session_id: str, user_query: str, max_tokens: int = 4096, add_bos: bool = True):
    """
    Обрабатывает запрос пользователя через локальную модель Qwen:
        1. Загружает последние 10 сообщений истории сессии из базы.
        2. Преобразует историю в формат для Qwen сервера.
        3. Добавляет текущий запрос пользователя к истории.
        4. Отправляет запрос на Qwen сервер и получает ответ.
        5. Сохраняет запрос пользователя и ответ модели в базе данных.
        6. Обрезает историю до последних 10 сообщений.

    Args:
        session_id (str): уникальный идентификатор сессии пользователя.
        user_query (str): текст запроса пользователя.
        max_tokens (int): максимальное количество токенов в ответе (по умолчанию 512).
        add_bos (bool): добавлять ли BOS токен в начало промпта (по умолчанию True).

    Returns:
        dict: словарь с ключами:
            - "response": текст ответа модели
            - "generation_time": время генерации в секундах
            - "tokens_generated": количество сгенерированных токенов

    Raises:
        Exception: если сервер Qwen недоступен или произошла ошибка генерации
    """

    # Проверяем доступность сервера
    try:
        health_response = requests.get(f"{QWEN_SERVER_URL}/health", timeout=5)
        if health_response.status_code != 200:
            raise Exception("Qwen server is not healthy")

        health_data = health_response.json()
        if not health_data.get("model_loaded", False):
            raise Exception("Qwen model is still loading, please wait")

    except requests.exceptions.RequestException as e:
        raise Exception(f"Cannot connect to Qwen server at {QWEN_SERVER_URL}: {str(e)}")

    # Загружаем историю сообщений
    history = get_history(session_id)

    # Преобразуем историю в формат для Qwen
    messages = []
    for message in history:
        messages.append({
            "role": message["role"],
            "content": message["content"]
        })

    # Добавляем текущий запрос пользователя
    messages.append({
        "role": "user",
        "content": user_query
    })

    # Формируем запрос к серверу
    request_data = {
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.4,
        "top_p": 0.9,
        "top_k": 60,
        "repetition_penalty": 1.1,
        "add_bos": add_bos,
        "system_prompt": os.getenv("DEFAULT_SYSTEM_PROMPT")
    }

    # Отправляем запрос на генерацию
    try:
        response = requests.post(
            f"{QWEN_SERVER_URL}/generate",
            json=request_data,
            timeout=120  # Увеличенный таймаут для генерации
        )
        response.raise_for_status()

    except requests.exceptions.Timeout:
        raise Exception("Qwen server request timeout. The generation is taking too long.")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error communicating with Qwen server: {str(e)}")

    result = response.json()
    bot_reply = result["response"]

    # Сохраняем в базу данных
    save_message(session_id, "user", user_query)
    save_message(session_id, "assistant", bot_reply)

    # Обрезаем историю
    trim_history(session_id)

    return {
        "response": bot_reply,
        "generation_time": result.get("generation_time", 0),
        "tokens_generated": result.get("tokens_generated", 0)
    }


def check_qwen_server_status():
    """
    Проверяет статус сервера Qwen

    Returns:
        dict: статус сервера с полями:
            - "available": bool - доступен ли сервер
            - "model_loaded": bool - загружена ли модель
            - "status": str - текстовое описание статуса
    """
    try:
        response = requests.get(f"{QWEN_SERVER_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "available": True,
                "model_loaded": data.get("model_loaded", False),
                "status": data.get("status", "unknown")
            }
        else:
            return {
                "available": False,
                "model_loaded": False,
                "status": f"Server returned status code {response.status_code}"
            }
    except requests.exceptions.RequestException as e:
        return {
            "available": False,
            "model_loaded": False,
            "status": f"Connection error: {str(e)}"
        }