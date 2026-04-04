.PHONY: deploy build up down restart logs migrate migrate-new frontend

# Build and deploy
deploy: build up

build:
	docker compose build raggr

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart raggr

logs:
	docker compose logs -f raggr

# Database migrations
migrate:
	docker compose exec raggr aerich upgrade

migrate-new:
	@read -p "Migration name: " name; \
	docker compose exec raggr aerich migrate --name $$name

migrate-history:
	docker compose exec raggr aerich history

# Frontend
frontend:
	cd raggr-frontend && yarn install && yarn build
