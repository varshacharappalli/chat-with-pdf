from fastapi import FastAPI, UploadFile, File
import numpy as np
import requests
import os
import pymupdf as fitz
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

app = FastAPI()

load_dotenv()

api_key = os.getenv('API_KEY')

embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

vector_store = None
documents = []  

def extract_text_from_pdf(file_path):
    text_data = []
    doc = fitz.open(file_path)
    for page in doc:
        text_data.append(page.get_text("text"))
    return text_data

def split_text_with_langchain(text, chunk_size=1000, overlap=200):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=overlap, separators=["\n\n", "\n", " ", ""]
    )
    return text_splitter.split_text(text)

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
    
    global vector_store, documents
    documents.clear()
    
    chunks_processed = 0
    all_chunks = []
    
    for page_num, text in enumerate(text_data):
        chunks = split_text_with_langchain(text, chunk_size, overlap)
        for i, chunk in enumerate(chunks):
            chunk_with_metadata = f"Page {page_num + 1}, Chunk {i + 1}: {chunk}"
            all_chunks.append((chunk_with_metadata, {"source": f"Page {page_num + 1}, Chunk {i + 1}"}))
    
    if all_chunks:
        texts = [all_chunks[0][0]]
        metadatas = [all_chunks[0][1]]
        vector_store = FAISS.from_texts(texts=texts, metadatas=metadatas, embedding=embedding_function)
        documents.append(all_chunks[0][0])
        chunks_processed = 1
        
        if len(all_chunks) > 1:
            texts = [chunk[0] for chunk in all_chunks[1:]]
            metadatas = [chunk[1] for chunk in all_chunks[1:]]
            vector_store.add_texts(texts=texts, metadatas=metadatas)
            documents.extend(texts)
            chunks_processed += len(texts)
    
    return {
        "message": "PDF uploaded and processed successfully", 
        "pages_processed": len(text_data),
        "chunks_processed": chunks_processed
    }

def process_pdf(file_path: str, chunk_size: int = 1000, overlap: int = 200):
    file_ext = file_path.split(".")[-1].lower()
    if file_ext != "pdf":
        return {"error": "Only PDF files are supported."}
    
    if not os.path.exists(file_path):
        return {"error": "File does not exist."}
    
    text_data = extract_text_from_pdf(file_path)
    
    global vector_store, documents
    documents.clear()
    
    chunks_processed = 0
    all_chunks = []
    
    for page_num, text in enumerate(text_data):
        chunks = split_text_with_langchain(text, chunk_size, overlap)
        for i, chunk in enumerate(chunks):
            chunk_with_metadata = f"Page {page_num + 1}, Chunk {i + 1}: {chunk}"
            all_chunks.append((chunk_with_metadata, {"source": f"Page {page_num + 1}, Chunk {i + 1}"}))
    
    if all_chunks:
        texts = [all_chunks[0][0]]
        metadatas = [all_chunks[0][1]]
        vector_store = FAISS.from_texts(texts=texts, metadatas=metadatas, embedding=embedding_function)
        documents.append(all_chunks[0][0])
        chunks_processed = 1
        
        if len(all_chunks) > 1:
            texts = [chunk[0] for chunk in all_chunks[1:]]
            metadatas = [chunk[1] for chunk in all_chunks[1:]]
            vector_store.add_texts(texts=texts, metadatas=metadatas)
            documents.extend(texts)
            chunks_processed += len(texts)
    
    return {
        "message": "PDF processed successfully", 
        "pages_processed": len(text_data),
        "chunks_processed": chunks_processed
    }

@app.get("/chat/")
async def chat_with_pdf(query: str, top_k: int = 3):
    global vector_store
    
    if vector_store is None:
        return {"error": "No PDF has been processed yet. Please upload a PDF first."}
    
    query_embedding = embedding_function.embed_query(query)
    if query_embedding is None:
        return {"error": "Failed to generate embedding for query"}
    
    results = vector_store.similarity_search(query, k=top_k)
    
    context = "\n\n---\n\n".join([doc.page_content for doc in results])
    
    sources = [doc.metadata.get("source", "Unknown") for doc in results]
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": "deepseek/deepseek-r1:free",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant. Answer questions based on the provided document context."},
            {"role": "user", "content": f"Use this document context to answer the question:\n\n{context}\n\nQuestion: {query}"}
        ]
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return {
            "response": response.json()["choices"][0]["message"]["content"],
            "sources": sources
        }
    else:
        return {"error": "Failed to get response from LLM", "details": response.json()}

file_path = r"C:\Users\cvars\Downloads\Unit 3 (2).pdf"
result = process_pdf(file_path)
print(result)