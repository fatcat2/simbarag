# Petlibro Integration (Future)

No standalone PyPI package exists. Best source is the Home Assistant custom integration:
https://github.com/jjjonesjr33/petlibro

## API Overview

- **Base URL**: `https://api.us.petlibro.com`
- **Auth**: POST `/member/auth/login` with email + MD5(password), returns token
- **Token**: passed in `token` header on all subsequent requests
- **Deps**: just `aiohttp`

## Key Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/device/device/list` | List all devices |
| `/device/device/realInfo` | Real-time device status |
| `/data/data/realInfo` | Real-time sensor data |
| `/data/event/deviceEventsV2` | Event/activity logs |
| `/device/feedingPlan/list` | Feeding schedules |
| `/device/device/manualFeed` | Trigger manual feed |

## Available Data (Feeders)

- Serial number, model, MAC, firmware
- Wi-Fi SSID + signal strength
- Battery level/percentage
- Today's total feeding amount (weight & volume)
- Last/next feed time
- Feeding plan status
- Desiccant/filter cycle info

## Supported Devices

- Granary Smart Feeder (PLAF103)
- Space Smart Feeder (PLAF107)
- Air Smart Feeder (PLAF108)
- Polar Wet Food Feeder (PLAF109)
- Granary Smart Camera Feeder (PLAF203)
- One RFID Smart Feeder (PLAF301)
- Dockstream Smart Fountain (PLWF105)
- Dockstream RFID Smart Fountain (PLWF305)

## Extraction Plan

Extract from HA integration (`custom_components/petlibro/`):
- `api.py` - main client (remove HA imports, use standalone aiohttp session)
- `const.py` - constants/enums
- `exceptions.py` - error handling
- `devices/` - device model classes (optional)

Request headers:
```
source: ANDROID
language: EN
timezone: [configured]
version: 1.3.45
Content-Type: application/json
token: [auth_token]
```

## Config Vars Needed

```
PETLIBRO_EMAIL=
PETLIBRO_PASSWORD=
PETLIBRO_REGION=US
```
