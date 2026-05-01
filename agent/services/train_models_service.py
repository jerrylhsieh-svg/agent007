from typing import Literal

from agent.learning_models.train_merchant_model import train
from agent.services.call_model import call_model


def train_model(question: str, file_type: Literal["transaction", "statement"], history: list[dict] | None):
    context = train(file_type)
    history = history or []
    history.append({"role": "assistant", "content": context})
    return call_model(question, history)