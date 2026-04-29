.PHONY: deploy test type-check

deploy:
	docker compose up --build

test:
	python -m pytest

type-check:
	mypy -p agent

train-trasaction:
	python -m agent.learning_models.train_merchant_model --file-type transaction

train-statement:
	python -m agent.learning_models.train_merchant_model --file-type statement

check: test type-check

train: train-trasaction train-statement