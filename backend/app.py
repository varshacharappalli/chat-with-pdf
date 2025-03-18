from fastapi import FastAPI, UploadFile, File
import numpy as np
import faiss
import requests
import os
import pymupdf as fitz
from dotenv import load_dotenv
import textwrap

app = FastAPI()

load_dotenv()
print(os.getenv("API_KEY"))

api_key = os.getenv('API_KEY')
API_TOKEN = os.getenv('API_TOKEN')

dimension = 1536
index = faiss.IndexFlatL2(dimension)
documents = []

def extract_text_from_pdf(file_path):
    text_data = []
    doc = fitz.open(file_path)
    for page in doc:
        text_data.append(page.get_text("text"))
    return text_data

def chunk_text(text, chunk_size=1000, overlap=200):
    chunks = []
    if len(text) <= chunk_size:
        chunks.append(text)
    else:
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            
            if end < len(text):
                look_back = min(100, chunk_size // 4)
                break_point = text.rfind(". ", end - look_back, end)
                if break_point == -1:
                    break_point = text.rfind("\n", end - look_back, end)
                
                if break_point != -1:
                    end = break_point + 1 
            
            chunks.append(text[start:end].strip())
            start = end - overlap if end - overlap > start else start + chunk_size // 2
    
    return chunks

def get_embedding(text):
    url = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    data = {"inputs": [text]}
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        return response.json()[0]
    else:
        print("Error:", response.json())
        return None

@app.post("/upload/")
async def upload_pdf(file: UploadFile = File(...), chunk_size: int = 1000, overlap: int = 200):
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext != "pdf":
        return {"error": "Only PDF files are supported."}
    
    file_path = f"./uploads/{file.filename}"
    os.makedirs("uploads", exist_ok=True)
    
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    text_data = extract_text_from_pdf(file_path)
    
    global index, documents
    documents.clear()
    index.reset()
    
    chunks_processed = 0
    
    for page_num, text in enumerate(text_data):
        chunks = chunk_text(text, chunk_size, overlap)
        
        for i, chunk in enumerate(chunks):
            chunk_with_metadata = f"Page {page_num + 1}, Chunk {i + 1}: {chunk}"
            
            embedding = get_embedding(chunk)
            if embedding is not None:
                index.add(np.array([embedding], dtype=np.float32))
                documents.append(chunk_with_metadata)
                chunks_processed += 1
    
    return {
        "message": "PDF uploaded and processed successfully", 
        "pages_processed": len(text_data),
        "chunks_processed": chunks_processed
    }

@app.get("/chat/")
async def chat_with_pdf(query: str, top_k: int = 3):
    query_embedding = get_embedding(query)
    if query_embedding is None:
        return {"error": "Failed to generate embedding for query"}
    
    distances, nearest_indices = index.search(np.array([query_embedding], dtype=np.float32), top_k)
    
    context = "\n\n---\n\n".join([documents[idx] for idx in nearest_indices[0] if idx < len(documents)])
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": "deepseek-ai/deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant. Answer questions based on the provided document context."},
            {"role": "user", "content": f"Use this document context to answer the question:\n\n{context}\n\nQuestion: {query}"}
        ]
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return {
            "response": response.json()["choices"][0]["message"]["content"],
            "sources": [documents[idx].split(": ", 1)[0] for idx in nearest_indices[0] if idx < len(documents)]
        }
    else:
        return {"error": "Failed to get response from LLM", "details": response.json()}