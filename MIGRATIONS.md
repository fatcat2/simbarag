# Database Migrations with Aerich

## Initial Setup (Run Once)

1. Install dependencies:
```bash
uv pip install -e .
```

2. Initialize Aerich:
```bash
aerich init-db
```

This will:
- Create a `migrations/` directory
- Generate the initial migration based on your models
- Create all tables in the database

## When You Add/Change Models

1. Generate a new migration:
```bash
aerich migrate --name "describe_your_changes"
```

Example:
```bash
aerich migrate --name "add_user_profile_model"
```

2. Apply the migration:
```bash
aerich upgrade
```

## Common Commands

- `aerich init-db` - Initialize database (first time only)
- `aerich migrate --name "description"` - Generate new migration
- `aerich upgrade` - Apply pending migrations
- `aerich downgrade` - Rollback last migration
- `aerich history` - Show migration history
- `aerich heads` - Show current migration heads

## Docker Setup

In Docker, migrations run automatically on container startup via the startup script.

## Notes

- Migration files are stored in `migrations/models/`
- Always commit migration files to version control
- Don't modify migration files manually after they're created
