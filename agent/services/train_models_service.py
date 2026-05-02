from typing import Literal

from agent.learning_models.train_merchant_model import train
from agent.services.call_model import call_model


def train_model(question: str, file_type: Literal["transaction", "statement"], history: list[dict] | None):
    context = train(file_type)
    question += f"""
The model training completed successfully.

Training result:
{context}

Now ask the user whether they want to re-predict existing unconfirmed {file_type} records using the newly trained model.

Keep the response concise. Include the exact phrase they can reply with:
"yes re-predict {file_type}"

Also mention that human-confirmed labels should not be overwritten.
"""

    return call_model(question, history or [])