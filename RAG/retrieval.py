import os
import chromadb
import chromadb.utils.embedding_functions as ef
import ollama

VECTOR_DIR="D:\code\CDV\RAG\vectorstore"

def rag(user_question):
    client=chromadb.PersistentClient(path=VECTOR_DIR)
    embed=ef.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection=client.get_collection(name="disaster_guidlines", embedding_function=embed)
    result=collection.query(query_texts=[user_question], n_results=3)
    retrieved_chunks= result["Documents"][0]
    context="/n/n".join(retrieved_chunks)

    system_prompt = (
        "You are an AI assistant for the Community Disaster Volunteer Hub. "
        "Use the following pieces of retrieved context from official disaster guidelines "
        "to answer the volunteer's question accurately. "
        "If you don't know the answer or the information is not in the context, "
        "state that you do not know and advise them to contact their Coordinator. "
        "Do not hallucinate or make up emergency procedures.\n\n"
        f"Context:\n{context}"
    )

    response = ollama.chat(model="deepseek-r1:32b", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_question}])
    return response.choices[0].message.content

if __name__=="__main__":
    user_question = ""
    print("Enter your question:")

    answer = rag(user_question)