SHELL := /bin/zsh
python_version = 3.8.5

lint:
	@echo -e "Running linter"
	@isort dialogy
	@isort tests
	@black dialogy
	@black tests
	@echo -e "remove unused imports"
	@pycln dialogy
	@echo -e "Running type checker"
	@mypy dialogy

test: lint ## Run the tests.
	@pytest --cov=dialogy --cov-report html --cov-report term:skip-covered tests/
	@echo -e "The tests pass!" 

docs: test
	@echo -e "🦆🦕🐬🐶"
	@rm -rf docs_src/source/
	@sphinx-apidoc -o docs_src/source dialogy
	@$(MAKE) html -C docs_src
	@cp -r docs_src/_build/html/. ./docs

all: docs
