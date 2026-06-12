# SimbaKit

A self-hosted PetKit data polling service with a web dashboard. Polls the PetKit cloud API every 2 minutes and stores everything in SQLite — device snapshots, alerts, pet weight, and litter box activity.

## Stack

- **Python 3.14** + **uv** for package management
- **pypetkitapi** for PetKit cloud API
- **aiohttp** for HTTP + web server
- **aiosqlite** for async SQLite
- **Chart.js** for frontend charts
- **Docker** for deployment

## Features

### Dashboard
- Device cards with live status (firmware, serial, last seen)
- Alert banner — surfaces warnings and critical issues from all devices
- Per-device detail panel with time-series charts and snapshot history
- Full raw JSON stored per poll (nothing is ever lost)

### Alerts
Automatically extracted per poll cycle based on device state:

| Device | Alerts |
|--------|--------|
| Litter box | Waste bin full, litter low, deodorant empty/low/expiring, pet detection error, device errors |
| Water fountain | Water low, filter warning/low %, malfunction |
| Feeder | Food low, blockage, desiccant expiring, battery low |
| Purifier | Liquid low, consumable expiring |

### Weight Tracker
- Pulls pet weight from litter box camera events (`device_pet_graph_out`)
- Stats: latest, average, min/max range, trend direction
- Chart with multi-pet support
- Filter by pet and time range (7d / 30d / 90d / 1y)

### Litter Activity
- Tracks every litter box visit — poop vs pee (`is_shit`)
- Stats: total visits, poop/pee count, avg time in box, avg poop weight
- Event timeline with pet name, duration, weight

## Running

### Local
```bash
cp .env.example .env  # fill in PetKit credentials
uv sync
uv run python -m simbakit
```

### Docker
```bash
docker compose up -d --build
```

Dashboard at `http://localhost:8585`.

## Config (`.env`)

```
PETKIT_USERNAME=your_email@example.com
PETKIT_PASSWORD=your_password
PETKIT_REGION=US
PETKIT_TIMEZONE=America/New_York
POLL_INTERVAL_SECONDS=120
DB_PATH=simbakit.db
WEB_HOST=127.0.0.1
WEB_PORT=8585
```

## Project Structure

```
simbakit/
├── Dockerfile
├── compose.yaml
├── pyproject.toml
├── .env.example
├── docs/
│   └── petlibro-integration.md   # future: Petlibro feeder support
└── src/simbakit/
    ├── __main__.py                # entry point, signal handling
    ├── config.py                  # frozen dataclass from env vars
    ├── database.py                # SQLite schema + read/write
    ├── poller.py                  # PetKit polling + field extraction
    ├── web.py                     # REST API (aiohttp)
    └── static/index.html          # dashboard SPA
```

## Database

| Table | Purpose |
|-------|---------|
| `devices` | Device registry, upserted each poll |
| `device_snapshots` | Append-only full state snapshots with raw JSON |
| `alerts` | Extracted alerts per poll cycle |
| `pet_weights` | Weight measurements from litter box events |
| `litter_events` | Poop/pee visit log with duration and weights |

## Future

- **Petlibro feeder support** — API research done, notes in `docs/petlibro-integration.md`
