.PHONY: deploy redeploy build up down restart logs migrate migrate-new frontend test

# Build and deploy
deploy: build up

redeploy:
	git pull && $(MAKE) down && $(MAKE) up

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

# Tests
test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov

# Frontend
frontend:
	cd raggr-frontend && yarn install && yarn build
