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


# Initialize Tortoise ORM with lifecycle hooks
@app.while_serving
async def lifespan():
    logging.info("Initializing Tortoise ORM...")
    await Tortoise.init(config=TORTOISE_CONFIG)
    logging.info("Tortoise ORM initialized successfully")
    yield
    logging.info("Closing Tortoise ORM connections...")
    await Tortoise.close_connections()


# Serve React static files
@app.route("/static/<path:filename>")
async def static_files(filename):
    return await send_from_directory(app.static_folder, filename)


# Serve the React app for all routes (catch-all)
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
async def serve_react_app(path):
    if path and os.path.exists(os.path.join(app.template_folder, path)):
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
