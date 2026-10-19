from fastapi import APIRouter,HTTPException
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool


from RAG.retrieval import rag
router = APIRouter(prefix="/chatbot", tags=["chatbot"])

class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)

@router.post("/chat")
async def chat(request: ChatRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    try:
        answer= await run_in_threadpool(rag, question)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))