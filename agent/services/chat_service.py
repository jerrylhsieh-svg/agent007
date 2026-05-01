from agent.models.chat import ChatRequest
from agent.services.analyzer.bank_statement_analyzer import generate_bank_statement_summary, generate_bank_withdraw_summary
from agent.services.call_model import call_model
from agent.services.file_flow import handle_file_flow
from agent.services.train_models_service import train_model
from agent.services.triggers import should_start_statement_flow, should_start_statement_train_flow, should_start_transaction_flow, should_start_transaction_train_flow, should_start_withdraw_flow
from agent.services.analyzer.transaction_analyzer import generate_credit_card_summary


def get_reply(req: ChatRequest) -> str:
    result = handle_file_flow(req.session_id, req.message)
    if result["handled"]:
        return result["reply"]

    if should_start_transaction_flow(req.message):
        return generate_credit_card_summary(req.message, req.history)

    if should_start_statement_flow(req.message):
        return generate_bank_statement_summary(req.message, req.history)
    
    if should_start_withdraw_flow(req.message):
        return generate_bank_withdraw_summary(req.message, req.history)
    
    if should_start_statement_train_flow(req.message):
        return train_model(req.message, "transaction", req.history)
    
    if should_start_transaction_train_flow(req.message):
        return train_model(req.message, "statement", req.history)

    return call_model(req.message, req.history)