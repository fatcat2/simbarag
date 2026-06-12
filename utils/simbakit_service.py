"""SimbaKit API service for querying PetKit device and pet data."""

import os
import logging
from typing import Any, Optional

import aiohttp
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class SimbaKitService:
    """Service for interacting with SimbaKit API."""

    def __init__(self):
        self.base_url = os.getenv("SIMBAKIT_URL", "")
        if not self.base_url:
            raise ValueError("SIMBAKIT_URL environment variable is required")
        self.base_url = self.base_url.rstrip("/")

    async def _get(self, path: str, params: Optional[dict] = None) -> Any:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}{path}", params=params) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def get_devices(self) -> str:
        """Get all devices with latest status."""
        devices = await self._get("/api/devices")
        if not devices:
            return "No PetKit devices found."

        lines = []
        for d in devices:
            snap = d.get("latest_snapshot", {})
            error = snap.get("error_code")
            status = f"Error {error}: {snap.get('error_msg', '')}" if error else "OK"
            lines.append(
                f"- {d.get('name', d['device_id'])} ({d.get('device_type', 'unknown')}): "
                f"Status={status}, Firmware={d.get('firmware', 'N/A')}, "
                f"Last seen={d.get('last_seen_at', 'N/A')}"
            )
        return "PetKit Devices:\n" + "\n".join(lines)

    async def get_alerts(self, device_id: Optional[str] = None) -> str:
        """Get active alerts, optionally filtered by device."""
        if device_id:
            alerts = await self._get(f"/api/devices/{device_id}/alerts")
        else:
            alerts = await self._get("/api/alerts")

        if not alerts:
            return "No active alerts."

        lines = []
        for a in alerts:
            device_name = a.get("device_name", a.get("device_id", "unknown"))
            lines.append(
                f"- [{a['severity'].upper()}] {a['alert_label']} "
                f"(device: {device_name}, at: {a.get('polled_at', 'N/A')})"
            )
        return "Active Alerts:\n" + "\n".join(lines)

    async def get_pet_weights(
        self, pet_name: Optional[str] = None, days: Optional[int] = None
    ) -> str:
        """Get pet weight records."""
        params: dict[str, str] = {}
        if pet_name:
            params["pet"] = pet_name
        if days:
            params["days"] = str(days)

        data = await self._get("/api/pets/weights", params=params or None)
        weights = data.get("weights", [])

        if not weights:
            return "No weight records found."

        # Summary stats
        weight_values = [w["weight_g"] for w in weights]
        latest = weights[-1]
        avg_g = sum(weight_values) / len(weight_values)

        lines = [
            f"Pet Weight Data ({len(weights)} records):",
            f"- Latest: {latest.get('pet_name', 'Unknown')} - {latest['weight_g'] / 1000:.2f} kg at {latest['recorded_at']}",
            f"- Average: {avg_g / 1000:.2f} kg",
            f"- Range: {min(weight_values) / 1000:.2f} - {max(weight_values) / 1000:.2f} kg",
        ]

        # Trend from last 5 vs previous 5
        if len(weights) >= 10:
            recent = sum(w["weight_g"] for w in weights[-5:]) / 5
            previous = sum(w["weight_g"] for w in weights[-10:-5]) / 5
            diff = recent - previous
            if abs(diff) > 10:
                direction = "gaining" if diff > 0 else "losing"
                lines.append(f"- Trend: {direction} ({diff / 1000:+.2f} kg)")
            else:
                lines.append("- Trend: stable")

        return "\n".join(lines)

    async def get_litter_events(
        self, pet_name: Optional[str] = None, days: Optional[int] = None
    ) -> str:
        """Get litter box activity events and stats."""
        params: dict[str, str] = {}
        if pet_name:
            params["pet"] = pet_name
        if days:
            params["days"] = str(days)

        data = await self._get("/api/pets/litter-events", params=params or None)
        events = data.get("events", [])
        stats = data.get("stats", {})

        if not events and not stats.get("total_visits"):
            return "No litter box activity found."

        lines = [
            f"Litter Box Activity ({stats.get('total_visits', 0)} visits):",
            f"- Poops: {stats.get('poop_count', 0)}",
            f"- Pees: {stats.get('pee_count', 0)}",
        ]

        avg_time = stats.get("avg_toilet_time", 0)
        if avg_time:
            lines.append(f"- Average time in box: {avg_time:.0f}s")

        avg_weight = stats.get("avg_shit_weight", 0)
        if avg_weight:
            lines.append(f"- Average poop weight: {avg_weight:.0f}g")

        # Recent events
        if events:
            lines.append("\nRecent events:")
            for e in events[:5]:
                event_type = "Pooped" if e.get("is_shit") == 1 else "Peed"
                pet = e.get("pet_name", "Unknown")
                time = e.get("recorded_at", "N/A")
                duration = f", {e['toilet_time_s']}s" if e.get("toilet_time_s") else ""
                lines.append(f"- {pet} {event_type} at {time}{duration}")

        return "\n".join(lines)
