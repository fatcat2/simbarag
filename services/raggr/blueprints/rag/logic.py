import datetime
import os

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .fetchers import PaperlessNGXService

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

vector_store = Chroma(
    collection_name="simba_docs",
    embedding_function=embeddings,
    persist_directory=os.getenv("CHROMADB_PATH", ""),
)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,  # chunk size (characters)
    chunk_overlap=200,  # chunk overlap (characters)
    add_start_index=True,  # track index in original document
)


def date_to_epoch(date_str: str) -> float:
    split_date = date_str.split("-")
    date = datetime.datetime(
        int(split_date[0]),
        int(split_date[1]),
        int(split_date[2]),
        0,
        0,
        0,
    )

    return date.timestamp()


async def fetch_documents_from_paperless_ngx() -> list[Document]:
    ppngx = PaperlessNGXService()
    data = ppngx.get_data()
    doctypes = ppngx.get_doctypes()
    documents = []
    for doc in data:
        metadata = {
            "created_date": date_to_epoch(doc["created_date"]),
            "filename": doc["original_file_name"],
            "document_type": doctypes.get(doc["document_type"], ""),
        }
        documents.append(Document(page_content=doc["content"], metadata=metadata))

    return documents


async def index_documents():
    documents = await fetch_documents_from_paperless_ngx()

    splits = text_splitter.split_documents(documents)
    await vector_store.aadd_documents(documents=splits)


async def query_vector_store(query: str):
    retrieved_docs = await vector_store.asimilarity_search(query, k=2)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\nContent: {doc.page_content}")
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs


def get_vector_store_stats():
    """Get statistics about the vector store."""
    collection = vector_store._collection
    count = collection.count()
    return {
        "total_documents": count,
        "collection_name": collection.name,
    }


def list_all_documents(limit: int = 10):
    """List documents in the vector store with their metadata."""
    collection = vector_store._collection
    results = collection.get(limit=limit, include=["metadatas", "documents"])

    documents = []
    for i, doc_id in enumerate(results["ids"]):
        documents.append(
            {
                "id": doc_id,
                "metadata": results["metadatas"][i]
                if results.get("metadatas")
                else None,
                "content_preview": results["documents"][i][:200]
                if results.get("documents")
                else None,
            }
        )

    return documents
