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

# EVAL_ARGS contains the flags shown by `make evaluate-help`.
# Override EVAL_PYTHON when Poetry cannot find the service's Python environment.
EVAL_PYTHON ?= poetry run python
EVAL_ARGS ?=

.PHONY: evaluate evaluate-help

evaluate-help:
	@$(EVAL_PYTHON) -m src.scripts.evaluate_providers --help

evaluate:
	@$(EVAL_PYTHON) -m src.scripts.evaluate_providers $(EVAL_ARGS)
