from fastapi import FastAPI, HTTPException
# обработка запроса пользователя через gigachat
from chat import process_user_query
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