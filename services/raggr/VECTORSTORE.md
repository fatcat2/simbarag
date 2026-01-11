# Vector Store Management

This document describes how to manage the ChromaDB vector store used for RAG (Retrieval-Augmented Generation).

## Configuration

The vector store location is controlled by the `CHROMADB_PATH` environment variable:

- **Development (local)**: Set in `.env` to a local path (e.g., `/path/to/chromadb`)
- **Docker**: Automatically set to `/app/data/chromadb` and persisted via Docker volume

## Management Commands

### CLI (Command Line)

Use the `manage_vectorstore.py` script for vector store operations:

```bash
# Show statistics
python manage_vectorstore.py stats

# Index documents from Paperless-NGX (incremental)
python manage_vectorstore.py index

# Clear and reindex all documents
python manage_vectorstore.py reindex

# List documents
python manage_vectorstore.py list 10
python manage_vectorstore.py list 20 --show-content
```

### Docker

Run commands inside the Docker container:

```bash
# Show statistics
docker compose -f docker-compose.dev.yml exec -T raggr python manage_vectorstore.py stats

# Reindex all documents
docker compose -f docker-compose.dev.yml exec -T raggr python manage_vectorstore.py reindex
```

### API Endpoints

The following authenticated endpoints are available:

- `GET /api/rag/stats` - Get vector store statistics
- `POST /api/rag/index` - Trigger indexing of new documents
- `POST /api/rag/reindex` - Clear and reindex all documents

## How It Works

1. **Document Fetching**: Documents are fetched from Paperless-NGX via the API
2. **Chunking**: Documents are split into chunks of ~1000 characters with 200 character overlap
3. **Embedding**: Chunks are embedded using OpenAI's `text-embedding-3-large` model
4. **Storage**: Embeddings are stored in ChromaDB with metadata (filename, document type, date)
5. **Retrieval**: User queries are embedded and similar chunks are retrieved for RAG

## Troubleshooting

### "Error creating hnsw segment reader"

This indicates a corrupted index. Solution:

```bash
python manage_vectorstore.py reindex
```

### Empty results

Check if documents are indexed:

```bash
python manage_vectorstore.py stats
```

If count is 0, run:

```bash
python manage_vectorstore.py index
```

### Different results in Docker vs local

Docker and local environments use separate ChromaDB instances. To sync:

1. Index inside Docker: `docker compose exec -T raggr python manage_vectorstore.py reindex`
2. Or mount the same volume for both environments

## Production Considerations

1. **Volume Persistence**: Use Docker volumes or persistent storage for ChromaDB
2. **Backup**: Regularly backup the ChromaDB data directory
3. **Reindexing**: Schedule periodic reindexing to keep data fresh
4. **Monitoring**: Monitor the `/api/rag/stats` endpoint for document counts
