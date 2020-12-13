SHELL := /bin/bash
python_version = 3.8.5

PYLINT = pylint
PYLINTFLAGS = -rn

PYTHONFILES := $(wildcard *.py)


%.pylint:
	$(PYLINT) $(PYLINTFLAGS) $*.py

test:  ## Run the tests.
	@pytest --cov=dialogy --cov-report html --cov-report term:skip-covered tests/
	@mypy dialogy
	@echo -e "The tests pass! ✨ 🍰 ✨"

lint:
	$(patsubst %.py,%.pylint,$(PYTHONFILES))
	@echo -e "No linting errors! ✨ 🍰 ✨"
