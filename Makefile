.PHONY: up down logs pull-model test lint fmt cli run-example

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

pull-model:
	docker compose exec ollama ollama pull gemma3:12b

test:
	docker compose run --rm api pytest -v

lint:
	docker compose run --rm api ruff check .

fmt:
	docker compose run --rm api ruff format .

cli:
	docker compose run --rm api python -m research_agent.cli.main $(ARGS)

run-example:
	docker compose run --rm api python -m research_agent.cli.main \
		"What are the best practices for deploying LLMs in production?"
