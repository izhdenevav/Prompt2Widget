import os
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