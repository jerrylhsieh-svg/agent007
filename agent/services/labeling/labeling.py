from agent.models.label import TrainRecord
from agent.repo.TrainRecordRepository import TrainRecordRepository
from agent.repo.UnlabeledRecordRepository import UnlabeledRecordRepository
from agent.services.constants_and_dependencies import GSHEET_LABEL_STATEMENT_GROUP_TAB, GSHEET_LABEL_STATEMENT_TRAIN_TAB, GSHEET_LABEL_TRANSACTION_GROUP_TAB, GSHEET_LABEL_TRANSACTION_TRAIN_TAB
from agent.services.labeling.label_suggester import LabelSuggester
from agent.services.triggers import should_start_label_flow


label_sessions: dict[str, dict] = {}


def handle_label_flow(session_id: str, message: str):
    state = label_sessions.get(session_id)
    suggester = LabelSuggester()
    

    if state is None:
        state["step"] = "awaiting_file_type"
        
        return {
            "handled": True,
            "reply": "Which file type you want to help with the labeling, transaction or statement?"
        }

    step = state["step"]

    if step == "awaiting_file_type":
        file_type = message.strip()
        if file_type not in {"transaction", "statement"}:
            return {
                "handled": True,
                "reply": """Please give me a valid file type. Answer "transaction" or "statement only."""
            }
        state["step"] = "awaiting_approval"
        state["file_type"] = file_type

        unlabel_repo = UnlabeledRecordRepository(GSHEET_LABEL_TRANSACTION_GROUP_TAB if file_type == "transaction" else GSHEET_LABEL_STATEMENT_GROUP_TAB)
        first_record = unlabel_repo.get_first_record()
        state["unlabel_record"] = first_record
        state["unlabel_repo"] = unlabel_repo
        if first_record is None:
            return  {
                "handled": True,
                "reply": f"No recrod found for {file_type} that has not been labeled"
            }
        
        label_suggested = suggester.suggest_one_label(first_record)
        state["label_suggestsed"] = label_suggested

        return {
            "handled": True,
            "reply": f"""The record's description is {first_record.description} and machine learning model suggested {first_record.predicted_label}.
            I suggest the label should be {label_suggested.suggested_label} and reason is {label_suggested.reason}. Do you approve?
            Reply `approve` or `not approve` only.
"""
        }

    if step == "awaiting_approval":
        file_type = state["file_type"]
        tried = state.get("tried", 0)
        approval = message.strip()

        if approval not in {'approve', 'not approve'} and tried < 1:
            state["tried"] += 1
            return {
                "handled": True,
                "reply": """Please give me a valid respone. Answer "approve" only for approval else it will not proceed."""
            }
        elif approval != 'approve' and tried > 0:
            return {
                "handled": False,
                "reply": "Unable to proceed due to no clear approval",
            }
        if approval == "not approve":
            return {"handled": False}
        
        train_repo = TrainRecordRepository(GSHEET_LABEL_TRANSACTION_TRAIN_TAB if file_type == "transaction" else GSHEET_LABEL_STATEMENT_TRAIN_TAB)
        train_record = TrainRecord(
            description=state["unlabel_record"].description,
            label=state["label_suggestsed"].suggested_label,
            statement_type=state["unlabel_record"].statement_type,
        )
        train_repo.insert_many([train_record])
        unlabel_repo.delete_record(state["unlabel_record"])
        label_sessions.pop(session_id, None)
        return {
            "handled": True,
            "reply": f"train_record description: {train_record.description},\n label: {train_record.label}\n, statement_type: {train_record.statement_type}\n has been added to train data."
        }
    
    label_sessions.pop(session_id, None)
    return {"handled": False}
        
