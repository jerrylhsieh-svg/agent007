.PHONY: deploy test type-check train-model

deploy:
	docker compose up --build

test:
	python -m pytest

type-check:
	mypy -p agent

train-model:
	python -m agent.learning_models.transaction.train_merchant_model --csv data/description_labeled.csv

check: test type-check