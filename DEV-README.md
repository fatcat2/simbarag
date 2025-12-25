# Development Environment Setup

This guide explains how to run the application in development mode with hot reload enabled.

## Quick Start

### Development Mode (Hot Reload)

```bash
# Start all services in development mode
docker-compose -f docker-compose.dev.yml up --build

# Or run in detached mode
docker-compose -f docker-compose.dev.yml up -d --build
```

### Production Mode

```bash
# Start production services
docker-compose up --build
```

## What's Different in Dev Mode?

### Backend (Quart/Flask)
- **Hot Reload**: Python code changes are automatically detected and the server restarts
- **Source Mounted**: Your local `services/raggr` directory is mounted as a volume
- **Debug Mode**: Flask runs with `debug=True` for better error messages
- **Environment**: `FLASK_ENV=development` and `PYTHONUNBUFFERED=1` for immediate log output

### Frontend (React + rsbuild)
- **Auto Rebuild**: Frontend automatically rebuilds when files change
- **Watch Mode**: rsbuild runs in watch mode, rebuilding to `dist/` on save
- **Source Mounted**: Your local `services/raggr/raggr-frontend` directory is mounted as a volume
- **Served by Backend**: Built files are served by the backend, no separate dev server

## Ports

- **Application**: 8080 (accessible at `http://localhost:8080` or `http://YOUR_IP:8080`)

The backend serves both the API and the auto-rebuilt frontend, making it accessible from other machines on your network.

## Useful Commands

```bash
# View logs
docker-compose -f docker-compose.dev.yml logs -f

# View logs for specific service
docker-compose -f docker-compose.dev.yml logs -f raggr-backend
docker-compose -f docker-compose.dev.yml logs -f raggr-frontend

# Rebuild after dependency changes
docker-compose -f docker-compose.dev.yml up --build

# Stop all services
docker-compose -f docker-compose.dev.yml down

# Stop and remove volumes (fresh start)
docker-compose -f docker-compose.dev.yml down -v
```

## Making Changes

### Backend Changes
1. Edit any Python file in `services/raggr/`
2. Save the file
3. The Quart server will automatically restart
4. Check logs to confirm reload

### Frontend Changes
1. Edit any file in `services/raggr/raggr-frontend/src/`
2. Save the file
3. The browser will automatically refresh (Hot Module Replacement)
4. No need to rebuild

### Dependency Changes

**Backend** (pyproject.toml):
```bash
# Rebuild the backend service
docker-compose -f docker-compose.dev.yml up --build raggr-backend
```

**Frontend** (package.json):
```bash
# Rebuild the frontend service
docker-compose -f docker-compose.dev.yml up --build raggr-frontend
```

## Troubleshooting

### Port Already in Use
If you see port binding errors, make sure no other services are running on ports 8080 or 3000.

### Changes Not Reflected
1. Check if the file is properly mounted (check docker-compose.dev.yml volumes)
2. Verify the file isn't in an excluded directory (node_modules, __pycache__)
3. Check container logs for errors

### Frontend Not Connecting to Backend
Make sure your frontend API calls point to the correct backend URL. If accessing from the same machine, use `http://localhost:8080`. If accessing from another device on the network, use `http://YOUR_IP:8080`.

## Notes

- Both services bind to `0.0.0.0` and expose ports, making them accessible on your network
- Node modules and Python cache are excluded from volume mounts to use container versions
- Database and ChromaDB data persist in Docker volumes across restarts
- Access the app from any device on your network using your host machine's IP address
