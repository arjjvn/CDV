import os
import chromadb
import chromadb.utils.embedding_functions as ef
from pypdf import PdfReader

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VECTOR_DIR = os.path.join(BASE_DIR, "RAG", "vectorstore")
DOCS_DIR = os.path.join(BASE_DIR, "RAG", "documents")

def chunk_text(text, chunk_size=1000, overlap=200):
    chunk=[]
    start=0
    while start<len(text):
        end=start+chunk_size
        chunk.append(text[start:end])
        start=end-overlap
    return chunk

def ingest_doc():
    docs=[]
    metadata=[]
    id=[]
    chunk_count=0
    for filename in os.listdir(DOCS_DIR):
        if filename.endswith(".pdf"):
            reader=PdfReader(os.path.join(DOCS_DIR,filename))
            for page_num,page in enumerate(reader.pages):
                text=page.extract_text()
                if text:
                    chunks = chunk_text(text)
                    for chunk in chunks:
                        docs.append(chunk)
                        metadata.append({"source":filename, "page":page_num})
                        id.append(f"chunk_{chunk_count}")
                        chunk_count+=1
    if not docs:
        print("no doc found")
        return
    client=chromadb.PersistentClient(path=VECTOR_DIR)
    embend_fun=ef.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection=client.get_or_create_collection(name="disaster_guidelines", embedding_function=embend_fun)
    collection.add(documents=docs, metadatas=metadata, ids=id)

if __name__=="__main__":
    ingest_doc()