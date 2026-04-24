from __future__ import annotations

import os
from typing import Any, Iterable

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

from agent.services.gsheet_config import SCOPES, STATEMENT_HEADERS, TRANSACTION_HEADERS



def get_gspread_client() -> gspread.Client:
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_FILE")
    if not creds_path:
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS_FILE is not set")

    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    return gspread.authorize(creds)


def get_or_create_worksheet(spreadsheet_name: str, worksheet_name: str):
    client = get_gspread_client()
    spreadsheet = client.open(spreadsheet_name)

    try:
        return spreadsheet.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=20)


def ensure_headers(worksheet, headers: list[str]) -> None:
    existing = worksheet.row_values(1)
    if existing != headers:
        if not existing:
            worksheet.append_row(headers)
        else:
            worksheet.update("A1", [headers])


def append_data(
    spreadsheet_name: str,
    worksheet_name: str,
    rows: Iterable[list],
    data_type: str,
) -> None:
    worksheet = get_or_create_worksheet(spreadsheet_name, worksheet_name)
    if data_type == "transaction":
        headers = TRANSACTION_HEADERS
    elif data_type == "statement":
        headers = STATEMENT_HEADERS
    else:
        raise ValueError("data type has to be either transaction or statement")
    
    ensure_headers(worksheet, headers)
    rows = list(rows)
    if rows:
        worksheet.append_rows(rows, value_input_option="USER_ENTERED")


def _build_gsheet_rows(filename: str | None, upload_id: str, data: list[dict[str, Any]], doc_tpye: str) -> list[list[Any]]:
    rows: list[list] = []
    for row in data:
        if doc_tpye == "BOA_bank":
            rows.append(
                [
                    upload_id,
                    filename,
                    row.get("date"),
                    row.get("description"),
                    row.get("statement_type"),
                    row.get("amount"),
                    row.get("raw_line"),
                ]
            )
        else:
            rows.append(
                [
                    upload_id,
                    filename,
                    row.get("date"),
                    row.get("description"),
                    row.get("amount"),
                ]
            )
    return rows

def read_transactions_df(
    spreadsheet_name: str,
    worksheet_name: str,
) -> pd.DataFrame:
    client = get_gspread_client()
    spreadsheet = client.open(spreadsheet_name)
    worksheet = spreadsheet.worksheet(worksheet_name)

    records = worksheet.get_all_records()
    df = pd.DataFrame(records)

    if df.empty:
        return df

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    for col in ["amount", "balance", "page_number"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "description" in df.columns:
        df["description"] = df["description"].fillna("").astype(str)

    if "source_file" in df.columns:
        df["source_file"] = df["source_file"].fillna("").astype(str)

    return df