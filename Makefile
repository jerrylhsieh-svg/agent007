.PHONY: deploy test type-check train-model

deploy:
	docker compose up --build

test:
	python -m pytest

type-check:
	mypy -p agent

train-trasaction:
	python -m agent.learning_models.train_merchant_model --csv data/description_labeled.csv --file-type transaction

check: test type-check