.PHONY: deploy unit-test type-check

deploy:
	docker compose up --build

unit-test:
	python -m pytest

type-check:
	mypy -p agent