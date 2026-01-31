# Deployment & Migrations Guide

This document covers database migrations and deployment workflows for SimbaRAG.

## Migration Workflow

Migrations are managed by [Aerich](https://github.com/tortoise/aerich), the migration tool for Tortoise ORM.

### Key Principles

1. **Generate migrations in Docker** - Aerich needs database access to detect schema changes
2. **Migrations auto-apply on startup** - Both `startup.sh` and `startup-dev.sh` run `aerich upgrade`
3. **Commit migrations to git** - Migration files must be in the repo for production deploys

### Generating a New Migration

#### Development (Recommended)

With `docker-compose.dev.yml`, your local `services/raggr` directory is synced to the container. Migrations generated inside the container appear on your host automatically.

```bash
# 1. Start the dev environment
docker compose -f docker-compose.dev.yml up -d

# 2. Generate migration (runs inside container, syncs to host)
docker compose -f docker-compose.dev.yml exec raggr aerich migrate --name describe_your_change

# 3. Verify migration was created
ls services/raggr/migrations/models/

# 4. Commit the migration
git add services/raggr/migrations/
git commit -m "Add migration: describe_your_change"
```

#### Production Container

For production, migration files are baked into the image. You must generate migrations in dev first.

```bash
# If you need to generate a migration from production (not recommended):
docker compose exec raggr aerich migrate --name describe_your_change

# Copy the file out of the container
docker cp $(docker compose ps -q raggr):/app/migrations/models/ ./services/raggr/migrations/
```

### Applying Migrations

Migrations apply automatically on container start via the startup scripts.

**Manual application (if needed):**

```bash
# Dev
docker compose -f docker-compose.dev.yml exec raggr aerich upgrade

# Production
docker compose exec raggr aerich upgrade
```

### Checking Migration Status

```bash
# View applied migrations
docker compose exec raggr aerich history

# View pending migrations
docker compose exec raggr aerich heads
```

### Rolling Back

```bash
# Downgrade one migration
docker compose exec raggr aerich downgrade

# Downgrade to specific version
docker compose exec raggr aerich downgrade -v 1
```

## Deployment Workflows

### Development

```bash
# Start with watch mode (auto-restarts on file changes)
docker compose -f docker-compose.dev.yml up

# Or with docker compose watch (requires Docker Compose v2.22+)
docker compose -f docker-compose.dev.yml watch
```

The dev environment:
- Syncs `services/raggr/` to `/app` in the container
- Rebuilds frontend on changes
- Auto-applies migrations on startup

### Production

```bash
# Build and deploy
docker compose build raggr
docker compose up -d

# View logs
docker compose logs -f raggr

# Verify migrations applied
docker compose exec raggr aerich history
```

### Fresh Deploy (New Database)

On first deploy with an empty database, `startup-dev.sh` runs `aerich init-db` instead of `aerich upgrade`. This creates all tables from the current models.

For production (`startup.sh`), ensure the database exists and run:

```bash
# If aerich table doesn't exist yet
docker compose exec raggr aerich init-db

# Or if migrating from existing schema
docker compose exec raggr aerich upgrade
```

## Troubleshooting

### "No migrations found" on startup

The `migrations/models/` directory is empty or not copied into the image.

**Fix:** Ensure migrations are committed and the Dockerfile copies them:
```dockerfile
COPY migrations ./migrations
```

### Migration fails with "relation already exists"

The database has tables but aerich doesn't know about them (fresh aerich setup on existing DB).

**Fix:** Fake the initial migration:
```bash
# Mark initial migration as applied without running it
docker compose exec raggr aerich upgrade --fake
```

### Model changes not detected

Aerich compares models against the last migration's state. If state is out of sync:

```bash
# Regenerate migration state (dangerous - review carefully)
docker compose exec raggr aerich migrate --name fix_state
```

### Database connection errors

Ensure PostgreSQL is healthy before running migrations:

```bash
# Check postgres status
docker compose ps postgres

# Wait for postgres then run migrations
docker compose exec raggr bash -c "sleep 5 && aerich upgrade"
```

## File Reference

| File | Purpose |
|------|---------|
| `pyproject.toml` | Aerich config (`[tool.aerich]` section) |
| `migrations/models/` | Migration files |
| `startup.sh` | Production startup (runs `aerich upgrade`) |
| `startup-dev.sh` | Dev startup (runs `aerich upgrade` or `init-db`) |
| `app.py` | Contains `TORTOISE_CONFIG` |
| `aerich_config.py` | Aerich initialization configuration |

## Quick Reference

| Task | Command |
|------|---------|
| Generate migration | `docker compose -f docker-compose.dev.yml exec raggr aerich migrate --name name` |
| Apply migrations | `docker compose exec raggr aerich upgrade` |
| View history | `docker compose exec raggr aerich history` |
| Rollback | `docker compose exec raggr aerich downgrade` |
| Fresh init | `docker compose exec raggr aerich init-db` |
