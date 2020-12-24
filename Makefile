SHELL := /bin/bash
python_version = 3.8.5

test:  ## Run the tests.
	@echo -e "🐟🐳🐠🦐🐡🐟🦑🐙🦞🦀🦎🐊🐢🐸🐠🐚🦆🐟🐡🦕🦐🐙🦕🐬"
	@echo -e "Running linter 📃"
	@black dialogy
	@echo -e "🐟🐳🐠🦐🐡🐟🦑🐙🦞🦀🦎🐊🐢🐸🐠🐚🦆🐟🐡🦕🦐🐙🦕🐬"
	@echo -e "Running type checker 🔍"
	@mypy dialogy
	@echo -e "🐟🐳🐠🦐🐡🐟🦑🐙🦞🦀🦎🐊🐢🐸🐠🐚🦆🐟🐡🦕🦐🐙🦕🐬"
	@pytest --cov=dialogy --cov-report html --cov-report term:skip-covered tests/
	@echo -e "The tests pass! ✨ 🍰 ✨"
	@echo -e "🐟🐳🐠🦐🐡🐟🦑🐙🦞🦀🦎🐊🐢🐸🐠🐚🦆🐟🐡🦕🦐🐙🦕🐬"
