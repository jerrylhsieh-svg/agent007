from agent.db.models.financial_records.TransactionRecord import TransactionRecord
from agent.db.models.financial_records.BankStatementRecord import BankStatementRecord
from agent.db.models.unlabeled.UnlabeledStatementGroup import UnlabeledStatementGroup
from agent.db.models.unlabeled.UnlabeledTransactionGroup import UnlabeledTransactionGroup
from agent.db.models.unlabeled.UnlabeledStatementRecord import UnlabeledStatementnRecord
from agent.db.models.unlabeled.UnlabeledTransactionRecord import UnlabeledTransactionRecord

from agent.db.session import Base, engine


def init_db() -> None:
    Base.metadata.create_all(bind=engine)