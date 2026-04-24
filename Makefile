.PHONY: deploy test type-check

deploy:
	docker compose up --build

test:
	python -m pytest

type-check:
	mypy -p agent

check: test type-check