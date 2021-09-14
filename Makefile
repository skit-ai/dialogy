SHELL := /bin/zsh
python_version = 3.8.5

.PHONY: all test docs

lint:
	@echo -e "Running linter"
	@isort dialogy
	@isort tests
	@black dialogy
	@black tests
	@echo -e "Running type checker"

typecheck:
	@mypy -p dialogy

test: ## Run the tests.conf
	@pytest --cov=dialogy --cov-report html --cov-report term:skip-covered tests/

docs:
	@echo -e "🦆🦕🐬🐶"
	@rm -rf docs_src/source/
	@sphinx-apidoc -o docs_src/source dialogy
	@$(MAKE) html -C docs_src
	@cp -r docs_src/_build/html/. ./docs

all: lint typecheck test docs
