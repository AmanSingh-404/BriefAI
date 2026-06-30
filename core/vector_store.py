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

