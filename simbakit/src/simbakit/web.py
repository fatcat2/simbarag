import json
import logging
from pathlib import Path

from aiohttp import web

from simbakit.database import Database

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"


def create_app(db: Database) -> web.Application:
    app = web.Application()
    app["db"] = db
    app.router.add_get("/", index)
    app.router.add_get("/api/devices", api_devices)
    app.router.add_get("/api/devices/{device_id}/snapshots", api_snapshots)
    app.router.add_get("/api/devices/{device_id}/chart", api_chart)
    app.router.add_get("/api/alerts", api_alerts)
    app.router.add_get("/api/devices/{device_id}/alerts", api_device_alerts)
    app.router.add_get("/api/pets/weights", api_pet_weights)
    app.router.add_get("/api/pets/litter-events", api_litter_events)
    app.router.add_get("/api/pets/drinking-events", api_drinking_events)
    return app


async def index(request: web.Request) -> web.FileResponse:
    return web.FileResponse(STATIC_DIR / "index.html")


async def api_devices(request: web.Request) -> web.Response:
    db: Database = request.app["db"]
    devices = await db.get_all_devices()
    latest = await db.get_latest_snapshot_per_device()

    result = []
    for d in devices:
        snap = latest.get(d["device_id"])
        entry = {**d}
        if snap:
            entry["latest_snapshot"] = {
                "polled_at": snap["polled_at"],
                "error_code": snap["error_code"],
                "error_msg": snap["error_msg"],
                "raw_json": snap["raw_json"],
            }
        result.append(entry)

    return web.json_response(result)


async def api_snapshots(request: web.Request) -> web.Response:
    db: Database = request.app["db"]
    device_id = request.match_info["device_id"]
    limit = min(int(request.query.get("limit", "50")), 500)
    offset = int(request.query.get("offset", "0"))

    snapshots = await db.get_snapshots(device_id, limit=limit, offset=offset)
    total = await db.get_snapshot_count(device_id)

    return web.json_response(
        {"total": total, "limit": limit, "offset": offset, "snapshots": snapshots}
    )


async def api_chart(request: web.Request) -> web.Response:
    db: Database = request.app["db"]
    device_id = request.match_info["device_id"]
    hours = min(int(request.query.get("hours", "24")), 168)

    rows = await db.get_chart_data(device_id, hours=hours)

    timestamps = []
    error_codes = []
    metrics: dict[str, list] = {}

    for row in rows:
        timestamps.append(row["polled_at"])
        error_codes.append(row["error_code"] or 0)

        try:
            raw = json.loads(row["raw_json"])
        except (json.JSONDecodeError, TypeError):
            continue

        # Extract numeric fields from state for charting
        state = raw.get("state", {})
        if isinstance(state, dict):
            for key, val in state.items():
                if isinstance(val, (int, float)) and not isinstance(val, bool):
                    metrics.setdefault(key, []).append(
                        {"t": row["polled_at"], "v": val}
                    )

    return web.json_response(
        {
            "timestamps": timestamps,
            "error_codes": error_codes,
            "metrics": metrics,
        }
    )


async def api_alerts(request: web.Request) -> web.Response:
    db: Database = request.app["db"]
    alerts = await db.get_active_alerts()
    return web.json_response(alerts)


async def api_device_alerts(request: web.Request) -> web.Response:
    db: Database = request.app["db"]
    device_id = request.match_info["device_id"]
    limit = min(int(request.query.get("limit", "50")), 200)
    alerts = await db.get_alerts_for_device(device_id, limit=limit)
    return web.json_response(alerts)


async def api_pet_weights(request: web.Request) -> web.Response:
    db: Database = request.app["db"]
    pet_name = request.query.get("pet")
    days = min(int(request.query.get("days", "30")), 365)
    weights = await db.get_pet_weights(pet_name=pet_name, days=days)
    pet_names = await db.get_pet_names()
    return web.json_response({"pet_names": pet_names, "weights": weights})


async def api_litter_events(request: web.Request) -> web.Response:
    db: Database = request.app["db"]
    pet_name = request.query.get("pet")
    days = min(int(request.query.get("days", "7")), 90)
    events = await db.get_litter_events(pet_name=pet_name, days=days)
    stats = await db.get_litter_stats(pet_name=pet_name, days=days)
    pet_names = await db.get_pet_names()
    return web.json_response({"pet_names": pet_names, "events": events, "stats": stats})


async def api_drinking_events(request: web.Request) -> web.Response:
    db: Database = request.app["db"]
    pet_name = request.query.get("pet")
    days = min(int(request.query.get("days", "7")), 90)
    events = await db.get_drinking_events(pet_name=pet_name, days=days)
    stats = await db.get_drinking_stats(pet_name=pet_name, days=days)
    pet_names = await db.get_pet_names()
    return web.json_response({"pet_names": pet_names, "events": events, "stats": stats})
