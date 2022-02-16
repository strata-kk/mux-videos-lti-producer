.DEFAULT_GOAL := help

###### Development commands

test: test-lint test-unit test-types test-format  ## Run all tests

test-lint:  ## Run linting tests on the codebase
	pylint --load-plugins=pylint_django muxltiproducer/ tests/

test-unit:  ## Run unit tests
	DJANGO_SETTINGS_MODULE=tests.settings ./manage.py test

test-types: ## Check type definitions
	mypy --ignore-missing-imports --exclude=migrations muxltiproducer/ tests/

test-format:  ## Run formatting tests
	black --check muxltiproducer/ tests/

format:  ## Format code with black
	black muxltiproducer/ tests/

###### Additional commands

ESCAPE = 
help: ## Print this help
	@grep -E '^([a-zA-Z_-]+:.*?## .*|######* .+)$$' Makefile \
		| sed 's/######* \(.*\)/@               $(ESCAPE)[1;31m\1$(ESCAPE)[0m/g' | tr '@' '\n' \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[33m%-30s\033[0m %s\n", $$1, $$2}'
