import os

from quart import Quart, request, jsonify, render_template, send_from_directory
from tortoise.contrib.quart import register_tortoise

from quart_jwt_extended import JWTManager

from main import consult_simba_oracle
from blueprints.conversation.logic import (
    get_the_only_conversation,
    add_message_to_conversation,
)

app = Quart(
    __name__,
    static_folder="raggr-frontend/dist/static",
    template_folder="raggr-frontend/dist",
)

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "SECRET_KEY")
jwt = JWTManager(app)

# Initialize Tortoise ORM
register_tortoise(
    app,
    db_url=os.getenv("DATABASE_URL", "sqlite://raggr.db"),
    modules={"models": ["blueprints.conversation.models"]},
    generate_schemas=True,
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
async def query():
    data = await request.get_json()
    query = data.get("query")
    # add message to database
    conversation = await get_the_only_conversation()
    print(conversation)
    await add_message_to_conversation(
        conversation=conversation, message=query, speaker="user"
    )

    response = consult_simba_oracle(query)
    await add_message_to_conversation(
        conversation=conversation, message=response, speaker="simba"
    )
    return jsonify({"response": response})


@app.route("/api/messages", methods=["GET"])
async def get_messages():
    conversation = await get_the_only_conversation()
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


# @app.route("/api/ingest", methods=["POST"])
# def webhook():
# data = request.get_json()
# print(data)
# return jsonify({"status": "received"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
