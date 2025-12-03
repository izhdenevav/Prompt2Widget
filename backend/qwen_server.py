"""
Сервер для модели Qwen 2.5 Coder
Держит модель загруженной в памяти и обрабатывает запросы через FastAPI
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import torch
import time
import os
import asyncio

from exllamav2 import (
    ExLlamaV2,
    ExLlamaV2Config,
    ExLlamaV2Cache,
    ExLlamaV2Cache_Q4,
    ExLlamaV2Tokenizer,
)

from exllamav2.generator import (
    ExLlamaV2StreamingGenerator,
    ExLlamaV2Sampler
)

class Message(BaseModel):
    role: str
    content: str


class GenerateRequest(BaseModel):
    messages: List[Message]
    max_tokens: Optional[int] = 4096
    temperature: Optional[float] = 0.22
    top_p: Optional[float] = 0.9
    top_k: Optional[int] = 50
    repetition_penalty: Optional[float] = 1.1
    add_bos: Optional[bool] = True
    system_prompt: Optional[str] = None


class GenerateResponse(BaseModel):
    response: str
    generation_time: float
    tokens_generated: int


# Глобальные переменные для модели
model = None
tokenizer = None
cache = None
streaming_generator = None
model_loaded = False


gen_lock = asyncio.Lock()

app = FastAPI(title="Qwen Model Server")


def load_model(
        model_dir: str,
        cache_type: str,
        max_seq_len: Optional[int] = None
):
    """Загрузка модели Qwen в память"""
    global model, tokenizer, cache, streaming_generator, model_loaded

    print("=" * 80)
    print("Загрузка модели Qwen 2.5 Coder...")
    print("=" * 80)

    # Конфигурация
    print(f"\n[1/4] Загрузка конфигурации из: {model_dir}")
    config = ExLlamaV2Config()
    config.model_dir = model_dir
    config.prepare()

    if max_seq_len:
        config.max_seq_len = max_seq_len

    # Модель и токенизатор
    print(f"\n[2/4] Инициализация модели...")
    model = ExLlamaV2(config)
    tokenizer = ExLlamaV2Tokenizer(config)

    # Создание кэша
    print(f"\n[3/4] Создание кэша типа: {cache_type}")
    if cache_type == "q4":
        cache = ExLlamaV2Cache_Q4(model, lazy=True)
        print("  └─ Q4 кэш (экономия памяти ~75%)")
    else:
        cache = ExLlamaV2Cache(model, lazy=True)
        print("  └─ Стандартный кэш")

    # Загрузка весов
    print(f"\n[4/4] Загрузка весов модели...")
    load_start = time.time()
    model.load_autosplit(cache, progress=True)
    load_time = time.time() - load_start
    print(f"\n✓ Модель загружена за {load_time:.2f} секунд")

    # Streaming генератор (возвращает чанки и token ids)
    streaming_generator = ExLlamaV2StreamingGenerator(model, cache, tokenizer)

    # Warmup
    print(f"\n[Warmup] Прогрев CUDA kernels...")
    streaming_generator.warmup()
    print(f"✓ Модель готова к работе!")
    print("=" * 80 + "\n")

    model_loaded = True


def format_chat_prompt(messages: List[Message], system_prompt: str = None) -> str:
    prompt = ""

    # Системный промпт в начале
    if system_prompt:
        prompt += f"<|im_start|>system\n{system_prompt}<|im_end|>\n"

    # История сообщений
    for msg in messages:
        prompt += f"<|im_start|>{msg.role}\n{msg.content}<|im_end|>\n"

    # Начало ответа ассистента
    prompt += "<|im_start|>assistant\n"

    return prompt


@app.on_event("startup")
async def startup_event():
    """Загрузка модели при запуске сервера"""
    import os

    model_dir = os.getenv("QWEN_MODEL_DIR", None)
    cache_type = os.getenv("QWEN_CACHE_TYPE", "q4")
    max_seq_len = os.getenv("QWEN_MAX_SEQ_LEN", None)

    if max_seq_len:
        max_seq_len = int(max_seq_len)

    load_model(model_dir, cache_type, max_seq_len)


@app.get("/health")
async def health_check():
    """Проверка состояния сервера"""
    return {
        "status": "healthy" if model_loaded else "loading",
        "model_loaded": model_loaded
    }


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """
    Генерация ответа от модели Qwen
    """
    if not model_loaded:
        raise HTTPException(status_code=503, detail="Model is still loading")

    # Формируем промпт
    prompt = format_chat_prompt(request.messages, request.system_prompt)

    # Сэмплинг настройки
    settings = ExLlamaV2Sampler.Settings()
    settings.temperature = request.temperature
    settings.top_k = request.top_k
    settings.top_p = request.top_p
    settings.token_repetition_penalty = request.repetition_penalty

    # Кодируем промпт в токены
    prompt_ids = tokenizer.encode(prompt)
    # Приводим к torch.Tensor с формой (1, L)
    if not isinstance(prompt_ids, torch.Tensor):
        prompt_ids = torch.tensor([prompt_ids], dtype=torch.long)
    if prompt_ids.dim() == 1:
        prompt_ids = prompt_ids.unsqueeze(0)

    # Обычный безопасный блок для генерации на GPU
    gen_start_time = time.time()
    async with gen_lock:
        try:
            # Сбрасываем кэш на новую сессию
            cache.current_seq_len = 0

            # Начинаем потоковую генерацию
            streaming_generator.begin_stream_ex(prompt_ids, settings)

            generated_tokens = []
            response_chunks = []
            total_tokens = 0

            # Итеративно читаем чанки
            while True:
                res = streaming_generator.stream_ex()
                chunk = res.get("chunk", "")
                eos = res.get("eos", False)
                tokens = res.get("chunk_token_ids", None)

                if chunk:
                    # аккумулируем текст и токены
                    response_chunks.append(chunk)

                if tokens is not None:
                    # tokens ожидается как tensor shape (1, n)
                    if isinstance(tokens, torch.Tensor):
                        generated_tokens.append(tokens)
                        total_tokens += tokens.shape[-1]
                    else:
                        # если вернулся список/питоновский объект
                        try:
                            t = torch.tensor(tokens, dtype=torch.long).unsqueeze(0)
                            generated_tokens.append(t)
                            total_tokens += t.shape[-1]
                        except Exception:
                            pass

                if eos or total_tokens >= request.max_tokens:
                    break

            # Собираем все токены ответа в один тензор (если есть)
            if generated_tokens:
                gen_ids = torch.cat(generated_tokens, dim=-1)
            else:
                gen_ids = torch.empty((1, 0), dtype=torch.long)

            # Декодируем только ответ (генерируемые токены)
            try:
                response_text = tokenizer.decode(gen_ids[0])
            except Exception:
                # fallback — конкатенация текстовых чанков
                response_text = "".join(response_chunks)

            # Убираем системные/специальные маркеры, если они есть
            if "<|im_end|>" in response_text:
                response_text = response_text.split("<|im_end|>")[0].strip()

            torch.cuda.synchronize()
            gen_time = time.time() - gen_start_time

            return GenerateResponse(
                response=response_text,
                generation_time=gen_time,
                tokens_generated=gen_ids.shape[-1]
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Qwen Model Server")
    parser.add_argument("-m", "--model_dir", type=str, required=True,
                        help="Путь к директории модели")
    parser.add_argument("-p", "--port", type=int, default=8001,
                        help="Порт сервера (по умолчанию 8001)")
    parser.add_argument("-host", "--host", type=str, default="0.0.0.0",
                        help="Хост сервера")
    parser.add_argument("-cache", "--cache_type", type=str, default="q4",
                        choices=["normal", "q4"],
                        help="Тип кэша")
    parser.add_argument("-l", "--max_seq_len", type=int, default=None,
                        help="Максимальная длина последовательности")

    args = parser.parse_args()

    os.environ["QWEN_MODEL_DIR"] = args.model_dir
    os.environ["QWEN_CACHE_TYPE"] = args.cache_type
    if args.max_seq_len:
        os.environ["QWEN_MAX_SEQ_LEN"] = str(args.max_seq_len)

    uvicorn.run(app, host=args.host, port=args.port)
