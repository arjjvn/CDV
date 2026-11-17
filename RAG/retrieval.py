import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import chromadb
import chromadb.utils.embedding_functions as ef
import ollama

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VECTOR_DIR = os.path.join(BASE_DIR, "RAG", "vectorstore")
os.makedirs(VECTOR_DIR, exist_ok=True)

client = chromadb.PersistentClient(path=VECTOR_DIR)
embed = ef.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
collection = client.get_collection(name="disaster_guidelines", embedding_function=embed)


def get_coordinator_directory() -> str:
    """Fetches approved disaster coordinators and their phone numbers from the CDVH database."""
    try:
        from Backend.database import SessionLocal
        from Backend.models import User
        db = SessionLocal()
        coords = db.query(User).filter(User.role == "coordinator", User.is_approved == True).all()
        if not coords:
            db.close()
            return ""
        lines = []
        for c in coords:
            name = f"{c.first_name or ''} {c.last_name or ''}".strip() or c.username
            loc = ", ".join(filter(None, [c.place, c.district])) or "Kerala"
            phone = c.phone or "112 / Hub Control"
            lines.append(f"- {name} ({loc}): {phone}")
        db.close()
        return "Official CDVH District Coordinators in Kerala:\n" + "\n".join(lines)
    except Exception:
        return ""


def search_database(query: str) -> str:
    retrieved_parts = []
    try:
        result = collection.query(query_texts=[query], n_results=3)
        if result and result.get("documents") and result["documents"][0]:
            retrieved_parts.append("\n\n".join(result["documents"][0]))
    except Exception:
        pass

    q_lower = query.lower()
    if any(k in q_lower for k in ("coordinator", "contact", "phone", "number", "officer", "help", "who", "call")):
        coord_info = get_coordinator_directory()
        if coord_info:
            retrieved_parts.append(coord_info)

    if not retrieved_parts:
        return "No specific guidelines found in knowledge base."
    return "\n\n".join(retrieved_parts)


def rag(user_question):
    system_prompt = """You are the CDVH Disaster Assistant for the Community Disaster Volunteer Hub in Kerala, India.

CRITICAL INSTRUCTIONS:
- Tone: Speak in a natural, calm, friendly, and normal human conversational tone.
- Do NOT use emoji bullet prefixes (do NOT start lines with emojis like 📱, ✅, 🚨, 📄, ⚠️, or 🔗).
- Do NOT output weird double dashes like "- -". Use standard single bullet points or clean paragraphs.
- Keep answers normal, clear, and concise. Provide direct, helpful answers without robotic filler.
- If asked about coordinator contact numbers, share the registered coordinators available in the directory or suggest contacting the 24/7 Kerala Emergency Control Room at 112.
- For emergency guidelines (floods, landslides, cyclones, first aid, evacuation, relief camps), provide practical, grounded advice from official Kerala disaster management protocols.
- Keep paragraphs short and readable.
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_question}
    ]

    response = ollama.chat(
        model="qwen3.5", 
        messages=messages,
        tools=[search_database]
    )

    if response.message.tool_calls:
        messages.append(response.message)
        
        for tool_call in response.message.tool_calls:
            if tool_call.function.name == "search_database":
                search_query = tool_call.function.arguments.get("query") or user_question
                retrieved_context = search_database(search_query)
                
                messages.append({
                    "role": "tool",
                    "content": retrieved_context,
                    "name": tool_call.function.name
                })
        
        final_response = ollama.chat(model="qwen3.5", messages=messages)
        return final_response.message.content

    return response.message.content


if __name__ == "__main__":
    user_question = input("Enter your question: ").strip()
    if user_question:
        answer = rag(user_question)
        print("\nCDVH Disaster Assistant:")
        print(answer)
    else:
        print("Please enter a question.")
