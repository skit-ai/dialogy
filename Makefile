SHELL := /bin/zsh
python_version = 3.8.5

lint:
	@echo -e "Running linter"
	@black dialogy
	@black tests
	@echo -e "Running type checker"
	@mypy dialogy

test: lint ## Run the tests.
	@pytest --cov=dialogy --cov-report html --cov-report term:skip-covered tests/
	@echo -e "The tests pass!" 

docs: test
	@echo -e "🦆🦕🐬🐶"
	@rm -rf dialogy/docs/dialogy
	@pycco dialogy/**/*.py -p -i
	@pycco tests/**/*.py -p
	@cp docs/pycco_edit.css docs/pycco.css

all: docs
