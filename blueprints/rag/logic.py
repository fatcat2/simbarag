import datetime
import logging
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from sqlalchemy import create_engine, text

from .fetchers import PaperlessNGXService
from utils.obsidian_service import ObsidianService

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

_embedding_server_url = os.getenv("EMBEDDING_SERVER_URL")
_embedding_model = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-3-small")

if _embedding_server_url:
    embeddings = OpenAIEmbeddings(
        model=_embedding_model,
        base_url=_embedding_server_url,
        api_key="not-needed",
        check_embedding_ctx_length=False,
    )
else:
    embeddings = OpenAIEmbeddings(model=_embedding_model)

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

md_header_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3")],
    strip_headers=False,
)

md_chunk_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    add_start_index=True,
)


def _split_markdown_document(doc: Document) -> list[Document]:
    """Split a markdown document by headers first, then by size.

    Prepends the note filename to each chunk so chunks are self-contained.
    """
    note_name = (
        Path(doc.metadata.get("filepath", "")).stem
        if doc.metadata.get("filepath")
        else ""
    )

    # Split by markdown headers
    header_splits = md_header_splitter.split_text(doc.page_content)

    # Carry over original document metadata to each header split
    for split in header_splits:
        split.metadata.update(doc.metadata)

    # Then apply size-based splitting on large sections
    sized_splits = md_chunk_splitter.split_documents(header_splits)

    # Prepend note name for self-contained context
    if note_name:
        for split in sized_splits:
            split.page_content = f"[Note: {note_name}]\n{split.page_content}"

    return sized_splits


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
            "source": "paperless",
            "created_date": date_to_epoch(doc["created_date"]),
            "filename": doc["original_file_name"],
            "document_type": doctypes.get(doc["document_type"], ""),
        }
        documents.append(Document(page_content=doc["content"], metadata=metadata))

    return documents


def _make_serializable(value):
    """Convert a value to a JSON-serializable type."""
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    if isinstance(value, (list, tuple)):
        return [_make_serializable(v) for v in value]
    if isinstance(value, dict):
        return {k: _make_serializable(v) for k, v in value.items()}
    return str(value)


def _sanitize_text(text_content: str) -> str:
    """Strip non-printable and invalid characters that break embedding tokenizers."""
    # Remove null bytes and control characters (keep newlines and tabs)
    text_content = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text_content)
    # Remove Unicode surrogates and other problematic Unicode
    text_content = re.sub(r"[\ud800-\udfff\ufffe\uffff]", "", text_content)
    # Remove replacement character clusters
    text_content = text_content.replace("\ufffd", "")
    # Collapse excessive whitespace
    text_content = re.sub(r" {3,}", "  ", text_content)
    return text_content.strip()


def _sanitize_documents(documents: list[Document]) -> list[Document]:
    """Sanitize page_content of all documents for embedding compatibility."""
    for doc in documents:
        doc.page_content = _sanitize_text(doc.page_content)
    return [doc for doc in documents if doc.page_content]


async def index_documents():
    """Index Paperless-NGX documents into vector store."""
    documents = await fetch_documents_from_paperless_ngx()

    splits = text_splitter.split_documents(documents)
    splits = _sanitize_documents(splits)
    logger.info(f"Indexing {len(splits)} chunks from {len(documents)} documents")
    vector_store = _get_vector_store()
    for i, split in enumerate(splits):
        try:
            await vector_store.aadd_documents(documents=[split])
        except Exception as e:
            logger.error(
                f"Failed to embed chunk {i} from {split.metadata.get('filename', 'unknown')}: {e}"
            )
            logger.debug(f"Chunk content preview: {split.page_content[:200]!r}")
            raise


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
            metadata = {
                "source": "obsidian",
                "filepath": parsed["filepath"],
                "folder": str(Path(parsed["filepath"]).parent)
                if parsed["filepath"]
                else "",
                "tags": parsed["tags"],
                "created_at": parsed["metadata"].get("created_at"),
                "indexed_at": time.time(),
                **{
                    k: v
                    for k, v in parsed["metadata"].items()
                    if k not in ["created_at", "created_by"]
                },
            }
            document = Document(
                page_content=parsed["content"],
                metadata=_make_serializable(metadata),
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

    # Split using markdown-aware chunking, sanitize, and index
    splits = []
    for doc in documents:
        splits.extend(_split_markdown_document(doc))
    splits = _sanitize_documents(splits)
    vector_store = _get_vector_store()
    await vector_store.aadd_documents(documents=splits)

    return {"indexed": len(documents)}


# In-memory cache of indexed obsidian files: {filepath: indexed_at}
_obsidian_index_cache: dict[str, float] = {}


def _load_obsidian_index_cache() -> dict[str, float]:
    """Load indexed obsidian files from DB into cache (cold start only)."""
    collection_id = _get_collection_id()
    if not collection_id:
        return {}
    engine = _get_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT DISTINCT cmetadata->>'filepath' AS filepath, "
                "MAX((cmetadata->>'indexed_at')::float) AS indexed_at "
                "FROM langchain_pg_embedding "
                "WHERE collection_id = :cid AND cmetadata->>'source' = 'obsidian' "
                "GROUP BY cmetadata->>'filepath'"
            ),
            {"cid": collection_id},
        )
        return {row[0]: row[1] for row in result if row[0] is not None}


async def sync_obsidian_documents() -> dict[str, int]:
    """Incrementally sync Obsidian documents to pgvector.

    Compares file mtimes against stored indexed_at timestamps to only
    re-index changed/new files and remove deleted ones.

    Returns:
        Dict with counts of added, updated, and deleted files.
    """
    global _obsidian_index_cache

    obsidian_service = ObsidianService()

    # Load cache from DB on first run
    if not _obsidian_index_cache:
        _obsidian_index_cache = _load_obsidian_index_cache()

    # Build map of current vault files -> mtime
    vault_files: dict[str, float] = {}
    for md_path in obsidian_service.walk_vault():
        vault_files[str(md_path)] = md_path.stat().st_mtime

    added = 0
    updated = 0
    deleted = 0

    # Find files to add or update
    files_to_index: list[str] = []
    for filepath, mtime in vault_files.items():
        indexed_at = _obsidian_index_cache.get(filepath)
        if indexed_at is None:
            files_to_index.append(filepath)
            added += 1
        elif mtime > indexed_at:
            # Delete old chunks first
            delete_documents_by_metadata("filepath", filepath)
            files_to_index.append(filepath)
            updated += 1

    # Find deleted files (in cache but not on disk)
    for filepath in list(_obsidian_index_cache):
        if filepath not in vault_files:
            delete_documents_by_metadata("filepath", filepath)
            del _obsidian_index_cache[filepath]
            deleted += 1

    # Index new/changed files
    if files_to_index:
        now = time.time()
        documents = []
        for filepath in files_to_index:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                parsed = obsidian_service.parse_markdown(content, filepath)
                metadata = {
                    "source": "obsidian",
                    "filepath": parsed["filepath"],
                    "folder": str(Path(parsed["filepath"]).parent)
                    if parsed["filepath"]
                    else "",
                    "tags": parsed["tags"],
                    "created_at": parsed["metadata"].get("created_at"),
                    "indexed_at": now,
                    **{
                        k: v
                        for k, v in parsed["metadata"].items()
                        if k not in ["created_at", "created_by"]
                    },
                }
                document = Document(
                    page_content=parsed["content"],
                    metadata=_make_serializable(metadata),
                )
                documents.append(document)
            except Exception as e:
                logger.warning(f"Error reading {filepath}: {e}")
                continue

        if documents:
            splits = []
            for doc in documents:
                splits.extend(_split_markdown_document(doc))
            splits = _sanitize_documents(splits)
            if splits:
                vector_store = _get_vector_store()
                await vector_store.aadd_documents(documents=splits)

        # Update cache for successfully processed files
        for filepath in files_to_index:
            _obsidian_index_cache[filepath] = now

    logger.info(
        f"Obsidian sync complete: {added} added, {updated} updated, {deleted} deleted"
    )
    return {"added": added, "updated": updated, "deleted": deleted}


async def query_vector_store(
    query: str,
    source: str | None = None,
    k: int = 8,
):
    """Query the vector store with optional source filtering and MMR.

    Args:
        query: Search query text
        source: Filter by source metadata (e.g., "obsidian", "paperless")
        k: Number of results to return
    """
    vector_store = _get_vector_store()
    filter_dict = {"source": source} if source else None
    retrieved_docs = await vector_store.amax_marginal_relevance_search(
        query,
        k=k,
        fetch_k=k * 3,
        filter=filter_dict,
    )
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
