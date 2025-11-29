import os
import sqlite3

from dotenv import load_dotenv


load_dotenv()
DB_PATH = os.getenv("DB_PATH")


def init_db():
    """
    Создает таблицу `messages` в базе данных, если она еще не существует.

    Таблица содержит следующие поля:
        - id: автоинкрементный идентификатор сообщения
        - session_id: идентификатор сессии пользователя
        - role: роль сообщения ("user" или "assistant")
        - content: текст сообщения
        - timestamp: время создания сообщения (по умолчанию текущее время)

    Используется при инициализации приложения для подготовки базы данных.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_message(session_id: str, role: str, content: str):
    """
    Сохраняет сообщение пользователя или модели в базе данных.

    Также ограничивает историю сообщений для данной сессии последними 10 сообщениями.

    Args:
        session_id (str): уникальный идентификатор сессии пользователя.
        role (str): роль сообщения, например "user" или "assistant".
        content (str): текст сообщения, который необходимо сохранить.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO messages (session_id, role, content)
        VALUES (?, ?, ?)
    """, (session_id, role, content))

    # оставить только последние 10 сообщений для конкретной сессии
    cursor.execute("""
        DELETE FROM messages
        WHERE id NOT IN (
            SELECT id FROM messages 
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT 10
        )
        AND session_id = ?
    """, (session_id, session_id))

    conn.commit()
    conn.close()


def get_history(session_id: str):
    """
    Получает историю сообщений для указанной сессии в порядке от старых к новым.

    Args:
        session_id (str): уникальный идентификатор сессии пользователя.

    Returns:
        list[dict]: список сообщений, где каждое сообщение представлено словарем
                    с ключами "role" и "content".
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT role, content 
        FROM messages 
        WHERE session_id = ?
        ORDER BY timestamp ASC
    """, (session_id,))

    rows = cursor.fetchall()
    conn.close()

    return [{"role": r, "content": c} for r, c in rows]

def trim_history(session_id: str):
    """
    Обрезает историю сообщений для указанной сессии, оставляя только последние 10 сообщений.
        (5 сообщений от user и 5 от assistant)

    Args:
        session_id (str): уникальный идентификатор сессии пользователя.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM messages
        WHERE id NOT IN (
            SELECT id FROM messages WHERE session_id=? ORDER BY id DESC LIMIT 10
        )
        AND session_id=?
    """, (session_id, session_id))

    conn.commit()
    conn.close()