import datetime
import logging
import os

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import create_engine, text

from .fetchers import PaperlessNGXService
from utils.obsidian_service import ObsidianService

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Convert Tortoise-style postgres:// URL to SQLAlchemy-style postgresql+psycopg://
_db_url = os.getenv(
    "DATABASE_URL", "postgres://raggr:raggr_dev_password@localhost:5432/raggr"
)
_pgvector_url = _db_url.replace("postgres://", "postgresql+psycopg://")

# Lazy-initialized vector store (defers DB connection to first use)
_vector_store = None


def _get_vector_store() -> PGVector:
    global _vector_store
    if _vector_store is None:
        _vector_store = PGVector(
            embeddings=embeddings,
            collection_name="simba_docs",
            connection=_pgvector_url,
            use_jsonb=True,
            create_extension=False,  # created by docker init script
            async_mode=True,
        )
    return _vector_store


def _get_engine():
    """Get a SQLAlchemy engine for direct queries."""
    if not hasattr(_get_engine, "_engine"):
        _get_engine._engine = create_engine(_pgvector_url)
    return _get_engine._engine


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,  # chunk size (characters)
    chunk_overlap=200,  # chunk overlap (characters)
    add_start_index=True,  # track index in original document
)


def _get_collection_id():
    """Get the UUID of our collection from the langchain_pg_collection table."""
    engine = _get_engine()
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT uuid FROM langchain_pg_collection WHERE name = :name"),
                {"name": "simba_docs"},
            )
            row = result.fetchone()
            return row[0] if row else None
    except Exception:
        # Table doesn't exist yet (first run before any indexing)
        return None


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
    """Index Paperless-NGX documents into vector store."""
    documents = await fetch_documents_from_paperless_ngx()

    splits = text_splitter.split_documents(documents)
    vector_store = _get_vector_store()
    await vector_store.aadd_documents(documents=splits)


async def fetch_obsidian_documents() -> list[Document]:
    """Fetch all markdown documents from Obsidian vault.

    Returns:
        List of LangChain Document objects with source='obsidian' metadata.
    """
    obsidian_service = ObsidianService()
    documents = []

    for md_path in obsidian_service.walk_vault():
        try:
            # Read markdown file
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse metadata
            parsed = obsidian_service.parse_markdown(content, md_path)

            # Create LangChain Document with obsidian source
            document = Document(
                page_content=parsed["content"],
                metadata={
                    "source": "obsidian",
                    "filepath": parsed["filepath"],
                    "tags": parsed["tags"],
                    "created_at": parsed["metadata"].get("created_at"),
                    **{
                        k: v
                        for k, v in parsed["metadata"].items()
                        if k not in ["created_at", "created_by"]
                    },
                },
            )
            documents.append(document)

        except Exception as e:
            logger.warning(f"Error reading {md_path}: {e}")
            continue

    return documents


async def index_obsidian_documents():
    """Index all Obsidian markdown documents into vector store.

    Deletes existing obsidian source chunks before re-indexing.
    """
    documents = await fetch_obsidian_documents()

    if not documents:
        logger.info("No Obsidian documents found to index")
        return {"indexed": 0}

    # Delete existing obsidian chunks
    delete_documents_by_metadata("source", "obsidian")

    # Split and index documents
    splits = text_splitter.split_documents(documents)
    vector_store = _get_vector_store()
    await vector_store.aadd_documents(documents=splits)

    return {"indexed": len(documents)}


async def query_vector_store(query: str):
    vector_store = _get_vector_store()
    retrieved_docs = await vector_store.asimilarity_search(query, k=2)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\nContent: {doc.page_content}")
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs


def delete_all_documents():
    """Delete all documents from the vector store collection."""
    collection_id = _get_collection_id()
    if not collection_id:
        return
    engine = _get_engine()
    with engine.connect() as conn:
        conn.execute(
            text("DELETE FROM langchain_pg_embedding WHERE collection_id = :cid"),
            {"cid": collection_id},
        )
        conn.commit()


def delete_documents_by_metadata(key: str, value: str):
    """Delete documents matching a metadata key/value pair."""
    collection_id = _get_collection_id()
    if not collection_id:
        return
    engine = _get_engine()
    with engine.connect() as conn:
        conn.execute(
            text(
                "DELETE FROM langchain_pg_embedding "
                "WHERE collection_id = :cid AND cmetadata->>:key = :value"
            ),
            {"cid": collection_id, "key": key, "value": value},
        )
        conn.commit()


def get_vector_store_stats():
    """Get statistics about the vector store."""
    collection_id = _get_collection_id()
    count = 0
    if collection_id:
        engine = _get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT COUNT(*) FROM langchain_pg_embedding WHERE collection_id = :cid"
                ),
                {"cid": collection_id},
            )
            count = result.scalar()
    return {
        "total_documents": count,
        "collection_name": "simba_docs",
    }


def list_all_documents(limit: int = 10):
    """List documents in the vector store with their metadata."""
    collection_id = _get_collection_id()
    if not collection_id:
        return []

    engine = _get_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT id, document, cmetadata FROM langchain_pg_embedding "
                "WHERE collection_id = :cid LIMIT :limit"
            ),
            {"cid": collection_id, "limit": limit},
        )
        documents = []
        for row in result:
            documents.append(
                {
                    "id": str(row[0]),
                    "metadata": row[2],
                    "content_preview": row[1][:200] if row[1] else None,
                }
            )

    return documents
