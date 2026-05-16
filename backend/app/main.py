import asyncio
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI

from app.api import auth, career, chat, intelligence, interview, ml, resume
from app.core.config import settings
from app.db.session import Base, engine
from app.services.ai_service import advanced_career_chat, stream_chunks
from app.services.emotion_service import detect_emotion
from app.services.realtime_service import realtime_hub
from app import models

models
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)
router_client = (
    AsyncOpenAI(
        api_key=settings.openrouter_api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "http://localhost:5173",
            "X-Title": settings.app_name,
        },
    )
    if settings.openrouter_api_key
    else None
)
openai_client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_origin,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://172.20.10.3:5173",
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+|192\.168\.\d+\.\d+):5173",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(career.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(resume.router, prefix="/api")
app.include_router(interview.router, prefix="/api")
app.include_router(ml.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(intelligence.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.app_name}


@app.websocket("/ws/live")
async def live_updates(websocket: WebSocket):
    await realtime_hub.connect(websocket)
    heartbeat_task = asyncio.create_task(realtime_hub.heartbeat(websocket))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        realtime_hub.disconnect(websocket)
    finally:
        heartbeat_task.cancel()


@app.websocket("/ws/chat")
async def streaming_chat(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            raw_message = await websocket.receive_text()
            payload = json.loads(raw_message)
            emotion = detect_emotion(payload.get("message", ""))
            await websocket.send_json({"type": "emotion", "emotion": emotion})
            answer = advanced_career_chat(
                message=payload.get("message", ""),
                target_role=payload.get("target_role"),
                context=payload.get("context") or {},
                history=payload.get("history") or [],
            )
            await websocket.send_json({"type": "start"})
            if router_client:
                await websocket.send_json(
                    {
                        "type": "meta",
                        "mode": "openrouter",
                        "content": f"Streaming with OpenRouter: {settings.openrouter_model}.",
                    }
                )
                await stream_model_chat(websocket, payload, router_client, settings.openrouter_model)
            elif openai_client:
                await websocket.send_json(
                    {
                        "type": "meta",
                        "mode": "gpt",
                        "content": f"Streaming with OpenAI: {settings.openai_model}.",
                    }
                )
                await stream_model_chat(websocket, payload, openai_client, settings.openai_model)
            else:
                await websocket.send_json(
                    {
                        "type": "meta",
                        "mode": "local",
                        "content": "Local intelligence mode. Add OPENAI_API_KEY for true GPT answers.",
                    }
                )
                for chunk in stream_chunks(answer):
                    await asyncio.sleep(0.045)
                    await websocket.send_json({"type": "delta", "content": chunk})
            await websocket.send_json({"type": "done"})
            await realtime_hub.broadcast(
                {
                    "type": "streaming_coach",
                    "title": "Streaming AI coach completed",
                    "detail": "Realtime GPT-style career response generated.",
                    "score": None,
                }
            )
    except WebSocketDisconnect:
        return


async def stream_model_chat(websocket: WebSocket, payload: dict, client: AsyncOpenAI, model: str):
    messages = build_openai_messages(payload)
    stream = await client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
        temperature=0.65,
    )
    async for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content
        if delta:
            await websocket.send_json({"type": "delta", "content": delta})


def build_openai_messages(payload: dict) -> list[dict[str, str]]:
    context = payload.get("context") or {}
    history = payload.get("history") or []
    system = (
        "You are Ai Careers for Future Generation, a warm, advanced, GPT-style assistant. "
        "Answer any user question clearly and helpfully. You are especially strong at careers, resumes, "
        "jobs, coding, AI, interviews, planning, and project building. Use the user's app context when relevant, "
        "but do not force every answer to be career-related. Be practical, accurate, and concise."
    )
    context_message = (
        "Current app context: "
        f"target={context.get('activeTarget')}; "
        f"careerScore={context.get('careerScore')}; "
        f"resumeScore={context.get('resumeScore')}; "
        f"interviewScore={context.get('interviewScore')}; "
        f"skills={context.get('skills')}; "
        f"resumeReport={context.get('resumeReport')}"
    )
    messages = [{"role": "system", "content": system}, {"role": "system", "content": context_message}]
    for item in history[-10:]:
        role = item.get("role")
        content = item.get("content")
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": payload.get("message", "")})
    return messages
