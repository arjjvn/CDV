import os
import chromadb
import chromadb.utils.embedding_functions as ef
import ollama

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VECTOR_DIR = os.path.join(BASE_DIR, "RAG", "vectorstore")
os.makedirs(VECTOR_DIR, exist_ok=True)

client = chromadb.PersistentClient(path=VECTOR_DIR)
embed = ef.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
collection = client.get_collection(name="disaster_guidelines", embedding_function=embed)

def search_database(query: str) -> str:
    result = collection.query(query_texts=[query], n_results=3)
    if not result["documents"] or not result["documents"][0]:
        return "No relevant information found."
    return "\n\n".join(result["documents"][0])

def rag(user_question):
    system_prompt = ("""
You are the CDVH Assistant, a friendly and professional chatbot
for the Community Disaster Volunteer Hub in Kerala, India.

PERSONALITY:
- Talk naturally like a helpful and caring human assistant.
- Be friendly, calm, respectful, and supportive.
- Use simple English that everyone can understand.
- Answer the question directly without unnecessary introductions.
- Give short answers for simple questions and detailed answers
  when the user needs guidance.
- Understand follow-up questions when conversation history is provided.

KNOWLEDGE AND SAFETY:
- Use retrieved disaster guidelines whenever relevant.
- If the retrieved context is insufficient, use general knowledge
  when appropriate. Never pretend an answer was verified if it was not.
- Never invent facts, evacuation orders, rescue updates, or contact details.
- Give coordinator phone numbers only when explicitly available in
  retrieved documents or a trusted source supplied to the system.
- If no coordinator number is available, say so politely.
- Never claim an alert was sent or a rescue team was dispatched unless
  the system confirms it.
- For immediate danger, prioritize clear safety instructions and advise
  contacting appropriate emergency services.
- Never encourage untrained people to perform dangerous rescues.
- Include document names as sources when that information is available.

FORMATTING:
- Respond in natural, conversational English.
- Use relevant emojis sparingly to improve understanding.
- Use Markdown headings for longer answers, such as:
  ### 🚨 Immediate Safety Steps
- Use bold formatting for important warnings and key information.
- Use numbered lists for procedures and bullet points for safety advice.
- Keep paragraphs short and easy to read.
- Do not create Markdown tables; use readable lists instead.
- Do not put the answer inside a code block.
- Do not force headings into short conversational replies.
- Do not repeat the user's question.
- The frontend renders Markdown, so format headings and bold text
  normally rather than explaining the formatting symbols.

RETRIEVAL:
- Use the search_database tool for relevant disaster guidelines
  or coordinator contact information before answering when appropriate.
- Base document-related claims on the retrieved content.
- If a requested contact number cannot be found, do not guess.

Return only the answer intended for the user.
"""
    )

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
                search_query = tool_call.function.arguments.get("query")
                
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