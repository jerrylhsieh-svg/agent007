from agent.db.models.TransactionRecord import TransactionRecord
from agent.db.models.BankStatementRecord import BankStatementRecord
from agent.db.models.UnlabeledRecord import UnlabeledRecord
from agent.db.models.UnlabeledRecordGroup import UnlabeledRecordGroup
from agent.db.session import Base, engine


def init_db() -> None:
    Base.metadata.create_all(bind=engine)