quickstart:
	poetry install

format:
	poetry run ruff format --check

lint:
	poetry run ruff check

format-fix:
	poetry run ruff format

lint-fix:
	poetry run ruff check --fix

test:
	poetry run pytest -v

seed-sources:
	poetry run python -m src.scripts.seed_sources

check-feed:
	poetry run python -m src.scripts.check_feed "$(URL)"
