from quart import Blueprint, jsonify
from quart_jwt_extended import jwt_refresh_token_required

from .logic import get_vector_store_stats, index_documents, vector_store
from blueprints.users.decorators import admin_required

rag_blueprint = Blueprint("rag_api", __name__, url_prefix="/api/rag")


@rag_blueprint.get("/stats")
@jwt_refresh_token_required
async def get_stats():
    """Get vector store statistics."""
    stats = get_vector_store_stats()
    return jsonify(stats)


@rag_blueprint.post("/index")
@admin_required
async def trigger_index():
    """Trigger indexing of documents from Paperless-NGX. Admin only."""
    try:
        await index_documents()
        stats = get_vector_store_stats()
        return jsonify({"status": "success", "stats": stats})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@rag_blueprint.post("/reindex")
@admin_required
async def trigger_reindex():
    """Clear and reindex all documents. Admin only."""
    try:
        # Clear existing documents
        collection = vector_store._collection
        all_docs = collection.get()

        if all_docs["ids"]:
            collection.delete(ids=all_docs["ids"])

        # Reindex
        await index_documents()
        stats = get_vector_store_stats()
        return jsonify({"status": "success", "stats": stats})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
