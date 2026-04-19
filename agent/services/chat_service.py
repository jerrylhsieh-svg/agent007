from agent.models.chat import ChatRequest
from agent.services.bank_statement_report import generate_bank_statement_summary
from agent.services.call_model import call_model
from agent.services.file_flow import handle_file_flow, should_start_statement_flow, should_start_transaction_flow
from agent.services.transaction_analysis import generate_credit_card_summary


def get_reply(req: ChatRequest) -> str:
    result = handle_file_flow(req.session_id, req.message)
    if result["handled"]:
        return result["reply"]

    if should_start_transaction_flow(req.message):
        return generate_credit_card_summary(req.message, req.history)

    if should_start_statement_flow(req.message):
        return generate_bank_statement_summary(req.message, req.history)

    return call_model(req.message, req.history)