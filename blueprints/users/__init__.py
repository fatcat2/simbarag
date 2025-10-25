from quart import Blueprint, jsonify, request
from quart_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_refresh_token_required,
    get_jwt_identity,
)
from .models import User


user_blueprint = Blueprint("user_api", __name__, url_prefix="/api/user")


@user_blueprint.route("/login", methods=["POST"])
async def login():
    data = await request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = await User.filter(username=username).first()

    if not user or not user.verify_password(password):
        return jsonify({"msg": "Invalid credentials"}), 401

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify(
        access_token=access_token,
        refresh_token=refresh_token,
        user={"id": user.id, "username": user.username},
    )


@user_blueprint.route("/refresh", methods=["POST"])
@jwt_refresh_token_required
async def refresh():
    user_id = get_jwt_identity()
    new_token = create_access_token(identity=user_id)
    return jsonify(access_token=new_token)
