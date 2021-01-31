SHELL := /bin/bash
python_version = 3.8.5

lint:
	@echo -e "🐟🐳🐠🦐"
	@echo -e "Running linter 📃"
	@black dialogy
	@black tests
	@echo -e "🐡🐲🦑🐙"
	@echo -e "Running type checker 🔍"
	@mypy dialogy

test: lint ## Run the tests.
	@echo -e "🦎🐊🐢🐸"
	@pytest --cov=dialogy --cov-report html --cov-report term:skip-covered tests/
	@echo -e "The tests pass!" 
	@echo -e "✨ 🍰 ✨"

docs: test
	@echo -e "🦆🦕🐬🐶"
	@rm -rf dialogy/docs/dialogy
	@pycco dialogy/**/*.py -p
	@pycco tests/**/*.py -p
	@echo "🌟🌟🌟"

all: docs
