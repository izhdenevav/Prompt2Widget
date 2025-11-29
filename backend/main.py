from fastapi import FastAPI, HTTPException
from chat import process_user_query
from database import init_db, get_history
from fastapi.middleware.cors import CORSMiddleware


init_db()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/gigachat")
def gigachat_query(query: str, session_id: str):
    try:
        response = process_user_query(session_id, query)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
def get_chat_history(session_id: str):
    try:
        # Получаем список сообщений из базы
        history = get_history(session_id)
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))