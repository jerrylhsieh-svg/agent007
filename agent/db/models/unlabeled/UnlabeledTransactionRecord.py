from agent.db.models.unlabeled.UnlabeledRecord import UnlabeledBaseRecord


class UnlabeledTransactionRecord(UnlabeledBaseRecord):
    __tablename__ = "unlabeled_transaction_records"