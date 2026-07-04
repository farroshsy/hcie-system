# HCIE — one-command orchestration of the full event-sourced stack.
# Quickstart:  make init && make build && make up && make migrate && make verify
COMPOSE := HCIE_SYSTEM_BACKEND_FINAL/05_deployment/00_docker/01_compose/docker-compose.final.yml
DC := docker compose -f $(COMPOSE)

.DEFAULT_GOAL := help
.PHONY: help init build fe-build up down migrate seed reseal test verify logs ps clean

help:  ## show targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-12s %s\n", $$1, $$2}'

init:  ## create .env from template + the runtime data dirs the compose mounts
	@[ -f .env ] || cp .env.example .env
	@mkdir -p research_validation/grounding research_validation/reports/grounding research_validation/external_datasets paper
	@echo "init done — edit .env (ADMIN_PASSWORD, JWT_SECRET_KEY) before 'make up'"

build:  ## build the API + worker images (Postgres/Redis/Kafka are pulled)
	$(DC) build

fe-build:  ## build the Next.js frontend image
	$(DC) --profile frontend build frontend

up:  ## start the full stack (api + 7 workers + datastores) detached
	$(DC) up -d

down:  ## stop + remove the stack
	$(DC) down

migrate:  ## apply Alembic migrations (07_database) inside the api container
	$(DC) exec api alembic -c 07_database/00_migrations/alembic.ini upgrade head

seed:  ## canonical idempotent seed (migrate + admin/tenant + verify) in the api container
	$(DC) exec -T api python /app/07_database/00_seeds/seed.py

reseal:  ## seal/re-seal a run: make reseal RUN=<run_id> [NOTE="..."]
	@[ -n "$(RUN)" ] || { echo "usage: make reseal RUN=<run_id> [NOTE=\"...\"]"; exit 1; }
	$(DC) exec -T api python /app/03_scripts/01_maintenance/reseal.py $(RUN) --note "$(NOTE)"

test:  ## run the functional suite on an ISOLATED stack (never the live DB)
	bash scripts/run_tests.sh

verify:  ## full check: functional suite + bit-identical determinism parity
	bash scripts/run_tests.sh
	bash scripts/run_determinism_parity.sh

logs:  ## tail logs from all services
	$(DC) logs -f --tail=100

ps:  ## show service status
	$(DC) ps

clean:  ## stop stack + drop volumes (DESTRUCTIVE — wipes local data)
	$(DC) down -v
