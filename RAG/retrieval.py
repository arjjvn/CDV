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
    result = collection.query(query_texts=[query], n_results=3)n
    if not result["documents"] or not result["documents"][0]:
        return "No relevant information found."
    return "\n\n".join(result["documents"][0])

def rag(user_question):
    system_prompt = (
        "You are an AI assistant for the Community Disaster Volunteer Hub. "
        "Use your search_database tool to look up procedures before answering disaster questions. "
        "If the tool returns no information, say you don't know and advise contacting a Coordinator. "
        "If the user is just saying hello, answer directly without searching."
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