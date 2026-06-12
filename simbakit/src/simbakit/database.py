from pathlib import Path

import aiosqlite

_SCHEMA = """
CREATE TABLE IF NOT EXISTS devices (
    device_id       TEXT PRIMARY KEY,
    device_type     TEXT NOT NULL,
    name            TEXT,
    sn              TEXT,
    firmware        TEXT,
    first_seen_at   TEXT NOT NULL DEFAULT (datetime('now')),
    last_seen_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS device_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id       TEXT NOT NULL,
    device_type     TEXT NOT NULL,
    polled_at       TEXT NOT NULL DEFAULT (datetime('now')),
    raw_json        TEXT NOT NULL,
    name            TEXT,
    firmware        TEXT,
    error_code      INTEGER,
    error_msg       TEXT,
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
);

CREATE INDEX IF NOT EXISTS idx_snapshots_device_time
    ON device_snapshots(device_id, polled_at);

CREATE INDEX IF NOT EXISTS idx_snapshots_polled_at
    ON device_snapshots(polled_at);

CREATE TABLE IF NOT EXISTS alerts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id       TEXT NOT NULL,
    polled_at       TEXT NOT NULL DEFAULT (datetime('now')),
    alert_key       TEXT NOT NULL,
    alert_label     TEXT NOT NULL,
    severity        TEXT NOT NULL DEFAULT 'warning',
    value           TEXT,
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
);

CREATE INDEX IF NOT EXISTS idx_alerts_device_time
    ON alerts(device_id, polled_at);

CREATE INDEX IF NOT EXISTS idx_alerts_polled_at
    ON alerts(polled_at);

CREATE TABLE IF NOT EXISTS pet_weights (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id       TEXT NOT NULL,
    pet_name        TEXT,
    pet_id          TEXT,
    weight_g        INTEGER NOT NULL,
    recorded_at     TEXT NOT NULL,
    polled_at       TEXT NOT NULL DEFAULT (datetime('now')),
    duration_s      INTEGER,
    FOREIGN KEY (device_id) REFERENCES devices(device_id),
    UNIQUE(device_id, pet_name, recorded_at)
);

CREATE INDEX IF NOT EXISTS idx_pet_weights_name_time
    ON pet_weights(pet_name, recorded_at);

CREATE TABLE IF NOT EXISTS litter_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id       TEXT NOT NULL,
    event_id        TEXT UNIQUE,
    pet_name        TEXT,
    pet_id          TEXT,
    recorded_at     TEXT NOT NULL,
    polled_at       TEXT NOT NULL DEFAULT (datetime('now')),
    is_shit         INTEGER,
    pet_weight_g    INTEGER,
    shit_weight_g   INTEGER,
    duration_s      INTEGER,
    toilet_time_s   INTEGER,
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
);

CREATE INDEX IF NOT EXISTS idx_litter_events_time
    ON litter_events(recorded_at);

CREATE INDEX IF NOT EXISTS idx_litter_events_pet
    ON litter_events(pet_name, recorded_at);
"""

_UPSERT_DEVICE = """
INSERT INTO devices (device_id, device_type, name, sn, firmware, last_seen_at)
VALUES (?, ?, ?, ?, ?, datetime('now'))
ON CONFLICT(device_id) DO UPDATE SET
    device_type = excluded.device_type,
    name = excluded.name,
    sn = excluded.sn,
    firmware = excluded.firmware,
    last_seen_at = datetime('now');
"""

_INSERT_SNAPSHOT = """
INSERT INTO device_snapshots (device_id, device_type, raw_json, name, firmware, error_code, error_msg)
VALUES (?, ?, ?, ?, ?, ?, ?);
"""


class Database:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._conn: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        self._conn = await aiosqlite.connect(self._db_path)
        await self._conn.executescript(_SCHEMA)
        await self._conn.commit()

    async def upsert_device(
        self,
        device_id: str,
        device_type: str,
        name: str | None,
        sn: str | None,
        firmware: str | None,
    ) -> None:
        assert self._conn is not None
        await self._conn.execute(
            _UPSERT_DEVICE, (device_id, device_type, name, sn, firmware)
        )
        await self._conn.commit()

    async def insert_snapshot(
        self,
        device_id: str,
        device_type: str,
        raw_json: str,
        name: str | None = None,
        firmware: str | None = None,
        error_code: int | None = None,
        error_msg: str | None = None,
    ) -> None:
        assert self._conn is not None
        await self._conn.execute(
            _INSERT_SNAPSHOT,
            (device_id, device_type, raw_json, name, firmware, error_code, error_msg),
        )
        await self._conn.commit()

    async def insert_alerts(
        self,
        device_id: str,
        alerts: list[dict],
    ) -> None:
        assert self._conn is not None
        if not alerts:
            return
        await self._conn.executemany(
            "INSERT INTO alerts (device_id, alert_key, alert_label, severity, value) VALUES (?, ?, ?, ?, ?)",
            [
                (device_id, a["key"], a["label"], a["severity"], a.get("value"))
                for a in alerts
            ],
        )
        await self._conn.commit()

    async def get_active_alerts(self) -> list[dict]:
        """Get the most recent alerts per device (from latest poll only)."""
        assert self._conn is not None
        self._conn.row_factory = aiosqlite.Row
        cursor = await self._conn.execute("""
            SELECT a.*, d.name AS device_name, d.device_type
            FROM alerts a
            JOIN devices d ON a.device_id = d.device_id
            WHERE a.polled_at = d.last_seen_at
            ORDER BY
                CASE a.severity WHEN 'critical' THEN 0 WHEN 'warning' THEN 1 ELSE 2 END,
                a.polled_at DESC
        """)
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_alerts_for_device(
        self, device_id: str, limit: int = 50
    ) -> list[dict]:
        assert self._conn is not None
        self._conn.row_factory = aiosqlite.Row
        cursor = await self._conn.execute(
            "SELECT * FROM alerts WHERE device_id = ? ORDER BY polled_at DESC LIMIT ?",
            (device_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def insert_litter_events(self, events: list[dict]) -> None:
        assert self._conn is not None
        if not events:
            return
        await self._conn.executemany(
            """INSERT OR IGNORE INTO litter_events
               (device_id, event_id, pet_name, pet_id, recorded_at,
                is_shit, pet_weight_g, shit_weight_g, duration_s, toilet_time_s)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    e["device_id"],
                    e.get("event_id"),
                    e.get("pet_name"),
                    e.get("pet_id"),
                    e["recorded_at"],
                    e.get("is_shit"),
                    e.get("pet_weight_g"),
                    e.get("shit_weight_g"),
                    e.get("duration_s"),
                    e.get("toilet_time_s"),
                )
                for e in events
            ],
        )
        await self._conn.commit()

    async def get_litter_events(
        self, pet_name: str | None = None, days: int = 30
    ) -> list[dict]:
        assert self._conn is not None
        self._conn.row_factory = aiosqlite.Row
        if pet_name:
            cursor = await self._conn.execute(
                """SELECT * FROM litter_events
                   WHERE pet_name = ? AND recorded_at >= datetime('now', ?)
                   ORDER BY recorded_at DESC""",
                (pet_name, f"-{days} days"),
            )
        else:
            cursor = await self._conn.execute(
                """SELECT * FROM litter_events
                   WHERE recorded_at >= datetime('now', ?)
                   ORDER BY recorded_at DESC""",
                (f"-{days} days",),
            )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_litter_stats(
        self, pet_name: str | None = None, days: int = 7
    ) -> dict:
        assert self._conn is not None
        where = "WHERE recorded_at >= datetime('now', ?)"
        params: list = [f"-{days} days"]
        if pet_name:
            where += " AND pet_name = ?"
            params.append(pet_name)
        cursor = await self._conn.execute(
            f"""SELECT
                COUNT(*) as total_visits,
                SUM(CASE WHEN is_shit = 1 THEN 1 ELSE 0 END) as poop_count,
                SUM(CASE WHEN is_shit = 0 OR is_shit IS NULL THEN 1 ELSE 0 END) as pee_count,
                AVG(toilet_time_s) as avg_toilet_time,
                AVG(CASE WHEN shit_weight_g > 0 THEN shit_weight_g END) as avg_shit_weight
            FROM litter_events {where}""",
            params,
        )
        row = await cursor.fetchone()
        return {
            "total_visits": row[0] or 0,
            "poop_count": row[1] or 0,
            "pee_count": row[2] or 0,
            "avg_toilet_time": round(row[3], 1) if row[3] else 0,
            "avg_shit_weight": round(row[4], 1) if row[4] else 0,
        }

    async def insert_pet_weights(self, records: list[dict]) -> None:
        assert self._conn is not None
        if not records:
            return
        await self._conn.executemany(
            """INSERT OR IGNORE INTO pet_weights
               (device_id, pet_name, pet_id, weight_g, recorded_at, duration_s)
               VALUES (?, ?, ?, ?, ?, ?)""",
            [
                (
                    r["device_id"],
                    r["pet_name"],
                    r.get("pet_id"),
                    r["weight_g"],
                    r["recorded_at"],
                    r.get("duration_s"),
                )
                for r in records
            ],
        )
        await self._conn.commit()

    async def get_pet_weights(
        self, pet_name: str | None = None, days: int = 30
    ) -> list[dict]:
        assert self._conn is not None
        self._conn.row_factory = aiosqlite.Row
        if pet_name:
            cursor = await self._conn.execute(
                """SELECT * FROM pet_weights
                   WHERE pet_name = ? AND recorded_at >= datetime('now', ?)
                   ORDER BY recorded_at ASC""",
                (pet_name, f"-{days} days"),
            )
        else:
            cursor = await self._conn.execute(
                """SELECT * FROM pet_weights
                   WHERE recorded_at >= datetime('now', ?)
                   ORDER BY recorded_at ASC""",
                (f"-{days} days",),
            )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_pet_names(self) -> list[str]:
        assert self._conn is not None
        cursor = await self._conn.execute(
            "SELECT DISTINCT pet_name FROM pet_weights WHERE pet_name IS NOT NULL ORDER BY pet_name"
        )
        rows = await cursor.fetchall()
        return [r[0] for r in rows]

    async def get_all_devices(self) -> list[dict]:
        assert self._conn is not None
        self._conn.row_factory = aiosqlite.Row
        cursor = await self._conn.execute(
            "SELECT * FROM devices ORDER BY last_seen_at DESC"
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_latest_snapshot_per_device(self) -> dict[str, dict]:
        assert self._conn is not None
        self._conn.row_factory = aiosqlite.Row
        cursor = await self._conn.execute("""
            SELECT ds.* FROM device_snapshots ds
            INNER JOIN (
                SELECT device_id, MAX(polled_at) AS max_polled
                FROM device_snapshots GROUP BY device_id
            ) latest ON ds.device_id = latest.device_id
                AND ds.polled_at = latest.max_polled
        """)
        rows = await cursor.fetchall()
        return {r["device_id"]: dict(r) for r in rows}

    async def get_snapshots(
        self, device_id: str, limit: int = 100, offset: int = 0
    ) -> list[dict]:
        assert self._conn is not None
        self._conn.row_factory = aiosqlite.Row
        cursor = await self._conn.execute(
            "SELECT * FROM device_snapshots WHERE device_id = ? ORDER BY polled_at DESC LIMIT ? OFFSET ?",
            (device_id, limit, offset),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_snapshot_count(self, device_id: str) -> int:
        assert self._conn is not None
        cursor = await self._conn.execute(
            "SELECT COUNT(*) FROM device_snapshots WHERE device_id = ?",
            (device_id,),
        )
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def get_chart_data(self, device_id: str, hours: int = 24) -> list[dict]:
        assert self._conn is not None
        self._conn.row_factory = aiosqlite.Row
        cursor = await self._conn.execute(
            """SELECT id, polled_at, raw_json, error_code FROM device_snapshots
               WHERE device_id = ? AND polled_at >= datetime('now', ?)
               ORDER BY polled_at ASC""",
            (device_id, f"-{hours} hours"),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None
