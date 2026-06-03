import asyncio
import logging
import os
from datetime import timedelta

from dotenv import load_dotenv
from quart import Quart, jsonify, render_template, send_from_directory
from quart_jwt_extended import JWTManager, get_jwt_identity, jwt_refresh_token_required
from tortoise import Tortoise

import blueprints.conversation
import blueprints.conversation.logic
import blueprints.email
import blueprints.rag
import blueprints.users
import blueprints.whatsapp
import blueprints.imessage
import blueprints.users.models
from config.db import TORTOISE_CONFIG

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

# Ensure YNAB and Mealie loggers are visible
logging.getLogger("utils.ynab_service").setLevel(logging.INFO)
logging.getLogger("utils.mealie_service").setLevel(logging.INFO)
logging.getLogger("blueprints.conversation.agents").setLevel(logging.INFO)

app = Quart(
    __name__,
    static_folder="raggr-frontend/dist/static",
    template_folder="raggr-frontend/dist",
)

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB upload limit
jwt = JWTManager(app)

# Register blueprints
app.register_blueprint(blueprints.users.user_blueprint)
app.register_blueprint(blueprints.conversation.conversation_blueprint)
app.register_blueprint(blueprints.email.email_blueprint)
app.register_blueprint(blueprints.rag.rag_blueprint)
app.register_blueprint(blueprints.whatsapp.whatsapp_blueprint)
app.register_blueprint(blueprints.imessage.imessage_blueprint)


async def _obsidian_sync_loop():
    """Background task that incrementally syncs Obsidian documents to pgvector."""
    from blueprints.rag.logic import sync_obsidian_documents

    interval = int(os.getenv("OBSIDIAN_SYNC_INTERVAL", "60"))
    logger = logging.getLogger("obsidian_sync")
    logger.info(f"Obsidian sync watcher started (interval={interval}s)")

    while True:
        try:
            result = await sync_obsidian_documents()
            if result["added"] or result["updated"] or result["deleted"]:
                logger.info(
                    f"Obsidian sync: {result['added']} added, "
                    f"{result['updated']} updated, {result['deleted']} deleted"
                )
        except Exception:
            logger.exception("Obsidian sync error")
        await asyncio.sleep(interval)


# Initialize Tortoise ORM with lifecycle hooks
@app.while_serving
async def lifespan():
    logging.info("Initializing Tortoise ORM...")
    await Tortoise.init(config=TORTOISE_CONFIG)
    logging.info("Tortoise ORM initialized successfully")

    watcher_task = None
    if os.getenv("OBSIDIAN_CONTINUOUS_SYNC") == "true":
        watcher_task = asyncio.create_task(_obsidian_sync_loop())

    yield

    if watcher_task is not None:
        watcher_task.cancel()

    logging.info("Closing Tortoise ORM connections...")
    await Tortoise.close_connections()


# Serve React static files
@app.route("/static/<path:filename>")
async def static_files(filename):
    return await send_from_directory(app.static_folder, filename)


# Allowed file extensions for static frontend assets
ALLOWED_STATIC_EXTENSIONS = {
    ".html",
    ".css",
    ".js",
    ".svg",
    ".png",
    ".ico",
    ".jpg",
    ".jpeg",
    ".webp",
    ".woff",
    ".woff2",
    ".ttf",
    ".txt",
}

# JSON files explicitly allowed to be served (e.g. PWA manifest)
ALLOWED_JSON_FILES = {"manifest.json"}


# Serve the React app for all routes (catch-all)
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
async def serve_react_app(path):
    if path:
        ext = os.path.splitext(path)[1].lower()
        basename = os.path.basename(path)
        allowed = ext in ALLOWED_STATIC_EXTENSIONS or (
            ext == ".json" and basename in ALLOWED_JSON_FILES
        )
        if allowed and os.path.exists(os.path.join(app.template_folder, path)):
            return await send_from_directory(app.template_folder, path)
    return await render_template("index.html")


@app.route("/api/messages", methods=["GET"])
@jwt_refresh_token_required
async def get_messages():
    current_user_uuid = get_jwt_identity()
    user = await blueprints.users.models.User.get(id=current_user_uuid)

    conversation = await blueprints.conversation.logic.get_conversation_for_user(
        user=user
    )
    # Prefetch related messages
    await conversation.fetch_related("messages")

    # Manually serialize the conversation with messages
    messages = []
    for msg in conversation.messages:
        messages.append(
            {
                "id": str(msg.id),
                "text": msg.text,
                "speaker": msg.speaker.value,
                "created_at": msg.created_at.isoformat(),
            }
        )

    return jsonify(
        {
            "id": str(conversation.id),
            "name": conversation.name,
            "messages": messages,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
