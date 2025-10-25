import os

from quart import Quart, request, jsonify, render_template, send_from_directory
from tortoise.contrib.quart import register_tortoise

from quart_jwt_extended import JWTManager, jwt_refresh_token_required, get_jwt_identity

from main import consult_simba_oracle

import blueprints.users
import blueprints.conversation
import blueprints.conversation.logic
import blueprints.users.models

app = Quart(
    __name__,
    static_folder="raggr-frontend/dist/static",
    template_folder="raggr-frontend/dist",
)

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "SECRET_KEY")
jwt = JWTManager(app)

# Register blueprints
app.register_blueprint(blueprints.users.user_blueprint)
app.register_blueprint(blueprints.conversation.conversation_blueprint)


TORTOISE_CONFIG = {
    "connections": {"default": "sqlite://raggr.db"},
    "apps": {
        "models": {
            "models": [
                "blueprints.conversation.models",
                "blueprints.users.models",
                "aerich.models",
            ]
        },
    },
}

# Initialize Tortoise ORM
register_tortoise(
    app,
    config=TORTOISE_CONFIG,
    generate_schemas=False,  # Disabled - using Aerich for migrations
)


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


@app.route("/api/query", methods=["POST"])
@jwt_refresh_token_required
async def query():
    current_user_uuid = get_jwt_identity()
    user = await blueprints.users.models.User.get(id=current_user_uuid)
    data = await request.get_json()
    query = data.get("query")
    conversation = await blueprints.conversation.logic.get_conversation_for_user(
        user=user
    )
    await blueprints.conversation.logic.add_message_to_conversation(
        conversation=conversation,
        message=query,
        speaker="user",
        user=user,
    )

    response = consult_simba_oracle(query)
    await blueprints.conversation.logic.add_message_to_conversation(
        conversation=conversation,
        message=response,
        speaker="simba",
        user=user,
    )
    return jsonify({"response": response})


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
