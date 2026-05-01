from agent.services.constants_and_dependencies import IS_STATEMENT_TRAIN_TRIGGERS, IS_STATEMENT_TRIGGERS, IS_TRANSACTION_TRAIN_TRIGGERS, IS_TRANSACTION_TRIGGERS, IS_WITHDRAW_TRIGGERS, SAVE_TRIGGERS

def normalize(text: str) -> str:
    return text.strip().lower()


def should_start_file_flow(message: str) -> bool:
    msg = normalize(message)
    return any(trigger in msg for trigger in SAVE_TRIGGERS)

def should_start_transaction_flow(message: str) -> bool:
    msg = normalize(message)
    return any(trigger in msg for trigger in IS_TRANSACTION_TRIGGERS)

def should_start_statement_flow(message: str) -> bool:
    msg = normalize(message)
    return any(trigger in msg for trigger in IS_STATEMENT_TRIGGERS)

def should_start_withdraw_flow(message: str) -> bool:
    msg = normalize(message)
    return any(trigger in msg for trigger in IS_WITHDRAW_TRIGGERS)

def should_start_statement_train_flow(message: str) -> bool:
    msg = normalize(message)
    return any(trigger in msg for trigger in IS_STATEMENT_TRAIN_TRIGGERS)

def should_start_transaction_train_flow(message: str) -> bool:
    msg = normalize(message)
    return any(trigger in msg for trigger in IS_TRANSACTION_TRAIN_TRIGGERS)