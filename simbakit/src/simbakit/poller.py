import asyncio
import json
import logging
from datetime import datetime, timezone

import aiohttp
from pypetkitapi.client import PetKitClient

from simbakit.config import Config
from simbakit.database import Database

logger = logging.getLogger(__name__)


def _serialize_entity(entity: object) -> str:
    if hasattr(entity, "model_dump"):
        return json.dumps(entity.model_dump(), default=str)
    return json.dumps(vars(entity), default=str)


def _extract_fields(entity: object) -> dict:
    state = getattr(entity, "state", None)
    return {
        "name": getattr(entity, "name", None),
        "firmware": str(fw) if (fw := getattr(entity, "firmware", None)) else None,
        "error_code": getattr(state, "error_code", None)
        or getattr(entity, "error_code", None),
        "error_msg": getattr(state, "error_msg", None)
        or getattr(entity, "error_msg", None),
    }


def _extract_alerts(entity: object) -> list[dict]:
    """Extract active alerts from a device entity based on its type."""
    alerts = []
    state = getattr(entity, "state", None)
    if state is None:
        return alerts

    # --- Litter box alerts ---
    if hasattr(state, "box_full") and state.box_full:
        alerts.append(
            {"key": "box_full", "label": "Waste bin is full", "severity": "critical"}
        )

    if hasattr(state, "sand_lack") and state.sand_lack:
        alerts.append(
            {"key": "sand_lack", "label": "Litter is low", "severity": "warning"}
        )

    # sand_percent: 0 is a default/unused value on some models; cross-check with sand_weight
    sand_pct = getattr(state, "sand_percent", None)
    sand_weight = getattr(state, "sand_weight", None)
    if sand_pct is not None and isinstance(sand_pct, (int, float)) and sand_pct > 0:
        if sand_pct <= 15:
            alerts.append(
                {
                    "key": "sand_percent",
                    "label": f"Litter level critically low ({sand_pct}%)",
                    "severity": "critical",
                    "value": str(sand_pct),
                }
            )
        elif sand_pct <= 30:
            alerts.append(
                {
                    "key": "sand_percent",
                    "label": f"Litter level low ({sand_pct}%)",
                    "severity": "warning",
                    "value": str(sand_pct),
                }
            )
    elif (
        sand_pct == 0
        and sand_weight
        and isinstance(sand_weight, (int, float))
        and sand_weight < 1000
    ):
        alerts.append(
            {
                "key": "sand_percent",
                "label": "Litter level very low",
                "severity": "critical",
                "value": "0",
            }
        )

    if hasattr(state, "liquid_empty") and state.liquid_empty:
        alerts.append(
            {
                "key": "liquid_empty",
                "label": "Deodorant is empty",
                "severity": "critical",
            }
        )
    elif hasattr(state, "liquid_lack") and state.liquid_lack:
        alerts.append(
            {"key": "liquid_lack", "label": "Deodorant is low", "severity": "warning"}
        )

    # deodorant_left_days: 0 can mean "not installed" on some models; only alert if > 0 and low
    deo_days = getattr(state, "deodorant_left_days", None)
    if (
        deo_days is not None
        and isinstance(deo_days, (int, float))
        and 0 < deo_days <= 3
    ):
        alerts.append(
            {
                "key": "deodorant_left_days",
                "label": f"Deodorant expires in {deo_days} day(s)",
                "severity": "warning",
                "value": str(deo_days),
            }
        )

    if hasattr(state, "pet_error") and state.pet_error:
        alerts.append(
            {"key": "pet_error", "label": "Pet detection error", "severity": "warning"}
        )

    # Litter error state
    err_code = getattr(state, "error_code", None)
    err_msg = getattr(state, "error_msg", None)
    if err_code and str(err_code) != "0":
        alerts.append(
            {
                "key": "error",
                "label": f"Device error: {err_msg or err_code}",
                "severity": "critical",
                "value": str(err_code),
            }
        )

    # --- Water fountain alerts ---
    if hasattr(entity, "lack_warning") and entity.lack_warning:
        alerts.append(
            {
                "key": "lack_warning",
                "label": "Water level is low",
                "severity": "critical",
            }
        )

    if hasattr(entity, "filter_warning") and entity.filter_warning:
        alerts.append(
            {
                "key": "filter_warning",
                "label": "Filter needs replacement",
                "severity": "warning",
            }
        )

    filter_pct = getattr(entity, "filter_percent", None)
    if filter_pct is not None and isinstance(filter_pct, (int, float)):
        if filter_pct <= 10:
            alerts.append(
                {
                    "key": "filter_percent",
                    "label": f"Filter life critically low ({filter_pct}%)",
                    "severity": "critical",
                    "value": str(filter_pct),
                }
            )
        elif filter_pct <= 25:
            alerts.append(
                {
                    "key": "filter_percent",
                    "label": f"Filter life low ({filter_pct}%)",
                    "severity": "warning",
                    "value": str(filter_pct),
                }
            )

    if hasattr(entity, "breakdown_warning") and entity.breakdown_warning:
        alerts.append(
            {
                "key": "breakdown_warning",
                "label": "Fountain malfunction detected",
                "severity": "critical",
            }
        )

    # --- Eversweet Ultra (W7H) fountain alerts ---
    # cwt_state is distinctive to the W7H FountainState model
    if hasattr(state, "cwt_state"):
        if getattr(state, "stg_full_state", None) and getattr(
            state, "stg_install", None
        ):
            alerts.append(
                {
                    "key": "waste_tank_full",
                    "label": "Waste water tank is full",
                    "severity": "critical",
                }
            )

        filter_days = getattr(state, "filter_left_days", None)
        if filter_days is not None and isinstance(filter_days, (int, float)):
            if 0 < filter_days <= 3:
                alerts.append(
                    {
                        "key": "filter_left_days",
                        "label": f"Filter expires in {filter_days} day(s)",
                        "severity": "critical",
                        "value": str(filter_days),
                    }
                )
            elif 3 < filter_days <= 7:
                alerts.append(
                    {
                        "key": "filter_left_days",
                        "label": f"Filter expires in {filter_days} day(s)",
                        "severity": "warning",
                        "value": str(filter_days),
                    }
                )

        # Semantics of these state ints are unverified; log them so alert
        # thresholds can be tuned against real data later.
        logger.info(
            "W7H fountain state: cwt=%s wt=%s stg_full=%s pump=%s water_pump=%s filter_days=%s",
            getattr(state, "cwt_state", None),
            getattr(state, "wt_state", None),
            getattr(state, "stg_full_state", None),
            getattr(state, "pump_state", None),
            getattr(state, "water_pump_state", None),
            getattr(state, "filter_left_days", None),
        )

    # --- Feeder alerts ---
    food_level = getattr(state, "food", None)
    if food_level is not None and isinstance(food_level, (int, float)):
        if food_level <= 10:
            alerts.append(
                {
                    "key": "food",
                    "label": f"Food level critically low ({food_level}%)",
                    "severity": "critical",
                    "value": str(food_level),
                }
            )
        elif food_level <= 25:
            alerts.append(
                {
                    "key": "food",
                    "label": f"Food level low ({food_level}%)",
                    "severity": "warning",
                    "value": str(food_level),
                }
            )

    if hasattr(state, "block") and state.block:
        alerts.append(
            {
                "key": "block",
                "label": "Feeder blockage detected",
                "severity": "critical",
            }
        )

    desiccant_days = getattr(state, "desiccant_left_days", None)
    if (
        desiccant_days is not None
        and isinstance(desiccant_days, (int, float))
        and desiccant_days <= 3
    ):
        alerts.append(
            {
                "key": "desiccant_left_days",
                "label": f"Desiccant expires in {desiccant_days} day(s)",
                "severity": "warning",
                "value": str(desiccant_days),
            }
        )

    battery_pwr = getattr(state, "battery_power", None) or getattr(
        state, "battery", None
    )
    if (
        battery_pwr is not None
        and isinstance(battery_pwr, (int, float))
        and 0 <= battery_pwr <= 15
    ):
        alerts.append(
            {
                "key": "battery",
                "label": f"Battery low ({battery_pwr}%)",
                "severity": "warning",
                "value": str(battery_pwr),
            }
        )

    if hasattr(state, "low_power") and state.low_power:
        alerts.append({"key": "low_power", "label": "Low power", "severity": "warning"})

    # --- Purifier alerts ---
    if hasattr(entity, "liquid_lack") and entity.liquid_lack:
        alerts.append(
            {
                "key": "liquid_lack",
                "label": "Purifier liquid is low",
                "severity": "warning",
            }
        )

    left_day = getattr(state, "left_day", None)
    if left_day is not None and isinstance(left_day, (int, float)) and left_day <= 3:
        alerts.append(
            {
                "key": "left_day",
                "label": f"Purifier consumable expires in {left_day} day(s)",
                "severity": "warning",
                "value": str(left_day),
            }
        )

    return alerts


def _extract_pet_weights(entity: object, device_id: str) -> list[dict]:
    """Extract pet weight records from litter box PetOutGraph data."""
    records = []

    # From device_pet_graph_out (T5/T6/T7 with camera)
    graph_out = getattr(entity, "device_pet_graph_out", None)
    if graph_out:
        for event in graph_out:
            content = getattr(event, "content", None)
            weight = getattr(content, "pet_weight", None) if content else None
            if weight and isinstance(weight, (int, float)) and weight > 0:
                ts = getattr(event, "time", None)
                recorded_at = (
                    datetime.fromtimestamp(ts, tz=timezone.utc).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    if ts
                    else None
                )
                if recorded_at:
                    duration = getattr(event, "duration", None)
                    records.append(
                        {
                            "device_id": device_id,
                            "pet_name": getattr(event, "pet_name", None),
                            "pet_id": str(pid)
                            if (pid := getattr(event, "pet_id", None))
                            else None,
                            "weight_g": int(weight),
                            "recorded_at": recorded_at,
                            "duration_s": duration,
                        }
                    )

    # From device_records (T3/T4 and others) - may be a list or a single object
    device_records = getattr(entity, "device_records", None)
    if device_records and isinstance(device_records, list):
        for rec in device_records:
            content = getattr(rec, "content", None)
            weight = getattr(content, "pet_weight", None) if content else None
            if weight and isinstance(weight, (int, float)) and weight > 0:
                ts = getattr(content, "time_in", None) or getattr(rec, "time", None)
                recorded_at = (
                    datetime.fromtimestamp(ts, tz=timezone.utc).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    if ts
                    else None
                )
                if recorded_at:
                    records.append(
                        {
                            "device_id": device_id,
                            "pet_name": getattr(rec, "pet_name", None),
                            "pet_id": str(pid)
                            if (pid := getattr(rec, "pet_id", None))
                            else None,
                            "weight_g": int(weight),
                            "recorded_at": recorded_at,
                            "duration_s": getattr(content, "interval", None),
                        }
                    )

    return records


def _extract_litter_events(entity: object, device_id: str) -> list[dict]:
    """Extract litter box visit events (poop/pee) from PetOutGraph data."""
    events = []

    graph_out = getattr(entity, "device_pet_graph_out", None)
    if not graph_out:
        return events

    for event in graph_out:
        ts = getattr(event, "time", None)
        if not ts:
            continue
        recorded_at = datetime.fromtimestamp(ts, tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        content = getattr(event, "content", None)

        events.append(
            {
                "device_id": device_id,
                "event_id": getattr(event, "event_id", None),
                "pet_name": getattr(event, "pet_name", None),
                "pet_id": str(pid) if (pid := getattr(event, "pet_id", None)) else None,
                "recorded_at": recorded_at,
                "is_shit": getattr(content, "is_shit", None) if content else None,
                "pet_weight_g": getattr(content, "pet_weight", None)
                if content
                else None,
                "shit_weight_g": getattr(content, "shit_weight", None)
                if content
                else None,
                "duration_s": getattr(event, "duration", None),
                "toilet_time_s": getattr(event, "toilet_time", None),
            }
        )

    return events


DRINKING_RECORD_TYPES = {"drink_over", "pet_detect"}


def _extract_drinking_events(entity: object, device_id: str) -> list[dict]:
    """Extract fountain drinking/visit events from W7H device records."""
    events = []

    # Litter boxes also populate device_records; only fountains have drink data
    if type(entity).__name__ != "WaterFountain":
        return events

    device_records = getattr(entity, "device_records", None)
    if not device_records or not isinstance(device_records, list):
        return events

    for rec in device_records:
        raw_type = getattr(rec, "enum_event_type", None)
        record_type = str(getattr(raw_type, "value", raw_type)) if raw_type else None
        if record_type not in DRINKING_RECORD_TYPES:
            continue

        ts = getattr(rec, "timestamp", None)
        if not ts:
            continue
        recorded_at = datetime.fromtimestamp(ts, tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        events.append(
            {
                "device_id": device_id,
                "event_id": getattr(rec, "event_id", None),
                "pet_name": getattr(rec, "pet_name", None),
                "pet_id": str(pid) if (pid := getattr(rec, "pet_id", None)) else None,
                "recorded_at": recorded_at,
                "record_type": record_type,
                "duration_s": getattr(rec, "duration", None),
                "stay_time_s": getattr(rec, "stay_time", None),
            }
        )

    return events


async def poll_once(config: Config, db: Database) -> int:
    async with aiohttp.ClientSession() as session:
        client = PetKitClient(
            username=config.petkit_username,
            password=config.petkit_password,
            region=config.petkit_region,
            timezone=config.petkit_timezone,
            session=session,
        )
        await client.get_devices_data()

    count = 0
    for device_id, entity in client.petkit_entities.items():
        device_type = type(entity).__name__
        raw_json = _serialize_entity(entity)
        fields = _extract_fields(entity)

        await db.upsert_device(
            device_id=str(device_id),
            device_type=device_type,
            name=fields["name"],
            sn=getattr(entity, "sn", None),
            firmware=fields["firmware"],
        )
        await db.insert_snapshot(
            device_id=str(device_id),
            device_type=device_type,
            raw_json=raw_json,
            **fields,
        )

        alerts = _extract_alerts(entity)
        if alerts:
            await db.insert_alerts(str(device_id), alerts)
            for a in alerts:
                logger.warning(
                    "ALERT [%s] %s: %s",
                    fields["name"],
                    a["severity"].upper(),
                    a["label"],
                )

        weight_records = _extract_pet_weights(entity, str(device_id))
        if weight_records:
            await db.insert_pet_weights(weight_records)
            logger.info(
                "Stored %d pet weight record(s) from %s",
                len(weight_records),
                fields["name"],
            )

        litter_events = _extract_litter_events(entity, str(device_id))
        if litter_events:
            await db.insert_litter_events(litter_events)
            logger.info(
                "Stored %d litter event(s) from %s", len(litter_events), fields["name"]
            )

        drinking_events = _extract_drinking_events(entity, str(device_id))
        if drinking_events:
            await db.insert_drinking_events(drinking_events)
            logger.info(
                "Stored %d drinking event(s) from %s",
                len(drinking_events),
                fields["name"],
            )

        count += 1
        logger.info(
            "Stored snapshot for %s '%s' (id=%s, alerts=%d)",
            device_type,
            fields["name"],
            device_id,
            len(alerts),
        )

    return count


async def run_poller(
    config: Config, db: Database, shutdown_event: asyncio.Event
) -> None:
    logger.info("Poller starting (interval=%ds)", config.poll_interval_seconds)
    while not shutdown_event.is_set():
        try:
            count = await poll_once(config, db)
            logger.info("Poll complete: %d entities stored", count)
        except Exception:
            logger.exception("Poll failed, will retry next cycle")

        try:
            await asyncio.wait_for(
                shutdown_event.wait(), timeout=config.poll_interval_seconds
            )
        except asyncio.TimeoutError:
            pass
    logger.info("Poller stopped")
