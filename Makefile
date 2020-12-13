SHELL := /bin/bash
python_version = 3.8.5


test:  ## Run the tests.
	@pytest --cov=dialogy --cov-report html --cov-report term:skip-covered tests/
	@echo -e "The tests pass! ✨ 🍰 ✨"
