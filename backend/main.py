from fastapi import FastAPI, HTTPException
from chat import (
    process_user_query,
    process_qwen_query,
    check_qwen_server_status
)
# инициализация бд и получение истории чата
from database import init_db, get_history
from fastapi.middleware.cors import CORSMiddleware

# создаём таблицу при старте приложения
init_db()
app = FastAPI()

# разрешаем cors-запросы с любых источников (для разработки и простых развёртываний)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/gigachat")
def gigachat_query(query: str, session_id: str):
    """
        эндпоинт для отправки запроса пользователя в gigachat.
        принимает текст запроса и идентификатор сессии, возвращает ответ модели.
    """
    try:
        response = process_user_query(session_id, query)
        return response
    except Exception as e:
        # непредвиденная ошибка в процессоре запросов
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
def get_chat_history(session_id: str):
    """
        эндпоинт для получения истории переписки по session_id.
        возвращает список сообщений в формате [{"role": ..., "content": ...}, ...].
    """
    try:
        # получаем список сообщений из базы
        history = get_history(session_id)
        return {"history": history}
    except Exception as e:
        # ошибка чтения из бд или неверный session_id
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/qwen")
def qwen_query(query: str, session_id: str, max_tokens: int = 4096, add_bos: bool = True):
    """
    Эндпоинт для запросов к локальной модели Qwen

    Args:
        query: текст запроса пользователя
        session_id: идентификатор сессии для истории
        max_tokens: максимальное количество токенов в ответе (опционально)
        add_bos: добавлять ли BOS токен (опционально, по умолчанию True)

    Returns:
        dict с полями:
            - response: текст ответа
            - generation_time: время генерации
            - tokens_generated: количество токенов

    Example:
        GET /qwen?query=Привет&session_id=user123
    """
    try:
        response = process_qwen_query(session_id, query, max_tokens, add_bos)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/qwen/status")
def qwen_server_status():
    """
    Проверка статуса сервера Qwen

    Returns:
        dict с информацией о доступности и состоянии модели

    Example:
        GET /qwen/status

        Response:
        {
            "available": true,
            "model_loaded": true,
            "status": "healthy"
        }
    """
    try:
        status = check_qwen_server_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

