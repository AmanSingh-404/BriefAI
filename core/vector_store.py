import os
# pyrefly: ignore [missing-import]
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

CHROMA_DIR = "vector_db"
COLLECTION_NAME = "meeting_transscript"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


def get_embedding():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs = {"device":'cpu'}
    )

def build_vector_store(transcript:str)->Chroma:
    print("Building vector store...")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = splitter.split_text(transcript)

    docs = [
        Document(page_content=chunk, metadata={"chunk_index": str(i)})
        for i, chunk in enumerate(chunks)
    ]
    
    embeddings = get_embedding()
    vector_store = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
        collection_name=COLLECTION_NAME
    )

    return vector_store

def load_vector_store()->Chroma:
    embeddings = get_embedding()
    vector_store = Chroma(
        persist_directory=CHROMA_DIR,
        collection_name=COLLECTION_NAME,
        embedding=embeddings
    )
    return vector_store


