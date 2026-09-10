"""Tests for SimbaKit service data formatting logic."""

import os
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
def simbakit_service():
    """Create a SimbaKitService pointed at a fake URL."""
    with patch.dict(os.environ, {"SIMBAKIT_URL": "http://simbakit:8585"}):
        from utils.simbakit_service import SimbaKitService

        yield SimbaKitService()


class TestGetDrinkingEvents:
    @pytest.mark.asyncio
    async def test_formats_stats_and_events(self, simbakit_service):
        payload = {
            "pet_names": ["Simba"],
            "events": [
                {
                    "pet_name": "Simba",
                    "recorded_at": "2026-07-09 14:00:00",
                    "record_type": "drink_over",
                    "duration_s": 25,
                    "stay_time_s": 40,
                },
                {
                    "pet_name": "Simba",
                    "recorded_at": "2026-07-09 10:00:00",
                    "record_type": "pet_detect",
                    "duration_s": None,
                    "stay_time_s": None,
                },
            ],
            "stats": {
                "total_drinks": 12,
                "detections": 3,
                "avg_duration": 23.2,
                "avg_stay_time": 35.0,
                "per_pet": [{"pet_name": "Simba", "drinks": 12, "avg_duration": 23.2}],
            },
        }
        simbakit_service._get = AsyncMock(return_value=payload)

        result = await simbakit_service.get_drinking_events(pet_name="Simba", days=7)

        simbakit_service._get.assert_awaited_once_with(
            "/api/pets/drinking-events", params={"pet": "Simba", "days": "7"}
        )
        assert "12 drinking sessions" in result
        assert "Average drink duration: 23s" in result
        assert "Camera detections (visits without drinking): 3" in result
        assert "Simba drank at 2026-07-09 14:00:00 for 25s" in result
        assert "Simba visited the fountain at 2026-07-09 10:00:00" in result
        # Single pet: no per-pet breakdown
        assert "By pet:" not in result

    @pytest.mark.asyncio
    async def test_per_pet_breakdown_with_multiple_pets(self, simbakit_service):
        payload = {
            "pet_names": ["Nala", "Simba"],
            "events": [],
            "stats": {
                "total_drinks": 20,
                "detections": 0,
                "avg_duration": 18.0,
                "avg_stay_time": 30.0,
                "per_pet": [
                    {"pet_name": "Simba", "drinks": 14, "avg_duration": 20.0},
                    {"pet_name": "Nala", "drinks": 6, "avg_duration": 14.0},
                ],
            },
        }
        simbakit_service._get = AsyncMock(return_value=payload)

        result = await simbakit_service.get_drinking_events()

        assert "By pet:" in result
        assert "Simba: 14 drinks" in result
        assert "Nala: 6 drinks" in result

    @pytest.mark.asyncio
    async def test_empty_data(self, simbakit_service):
        payload = {
            "pet_names": [],
            "events": [],
            "stats": {
                "total_drinks": 0,
                "detections": 0,
                "avg_duration": 0,
                "avg_stay_time": 0,
                "per_pet": [],
            },
        }
        simbakit_service._get = AsyncMock(return_value=payload)

        result = await simbakit_service.get_drinking_events()

        assert result == "No water fountain activity found."
