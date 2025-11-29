import os

from dotenv import load_dotenv
from gigachat import GigaChat
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

api_key = os.getenv("API_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/gigachat")
def gigachat_query(query: str):
    try:
        giga = GigaChat(
            credentials=api_key,
            model='GigaChat-2',
            verify_ssl_certs=False
        )
        response = giga.chat(query)
        return {
            "response": response.choices[0].message.content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))