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

extract-content:
	poetry run python -m src.scripts.extract_content "$(URL)"
