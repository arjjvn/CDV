from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool
import json
from urllib.parse import quote, unquote

from RAG.retrieval import rag
router = APIRouter(prefix="/chatbot", tags=["chatbot"])

class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


@router.post("/chat")
async def chat(payload: ChatRequest, request: Request):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    try:
        answer = await run_in_threadpool(rag, question)

        raw_history = request.cookies.get("cdvh_chat_history")
        try:
            chat_history = json.loads(unquote(raw_history)) if raw_history else []
        except Exception:
            chat_history = []

        chat_history.append({"sender": "user", "text": question})
        chat_history.append({"sender": "bot", "text": answer})
        chat_history = chat_history[-10:]

        res = JSONResponse(content={"success": True, "answer": answer, "history": chat_history})
        res.set_cookie(key="cdvh_chat_history", value=quote(json.dumps(chat_history)), max_age=86400, path="/")
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
