from quart import Blueprint, jsonify
from quart_jwt_extended import jwt_refresh_token_required

from .logic import (
    delete_all_documents,
    get_vector_store_stats,
    index_documents,
    sync_obsidian_documents,
)
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
        delete_all_documents()
        await index_documents()
        stats = get_vector_store_stats()
        return jsonify({"status": "success", "stats": stats})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@rag_blueprint.post("/index-obsidian")
@admin_required
async def trigger_obsidian_index():
    """Incrementally sync Obsidian documents into vector store. Admin only."""
    try:
        result = await sync_obsidian_documents()
        stats = get_vector_store_stats()
        return jsonify({"status": "success", "result": result, "stats": stats})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
