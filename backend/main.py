import os

from dotenv import load_dotenv
from gigachat import GigaChat
from fastapi import FastAPI, HTTPException


load_dotenv()

api_key = os.getenv("API_KEY")

app = FastAPI()

@app.get("/gigachat")
def gigachat_query(query: str):
    try:
        return {
            "response": query
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))