from __future__ import annotations

import os
from typing import Any, Iterable

import gspread
from google.oauth2.service_account import Credentials


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_gspread_client() -> gspread.Client:
    creds_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    if not creds_path:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_FILE is not set")

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


def append_transactions(
    spreadsheet_name: str,
    worksheet_name: str,
    rows: Iterable[list],
) -> None:
    worksheet = get_or_create_worksheet(spreadsheet_name, worksheet_name)

    headers = [
        "upload_id",
        "source_file",
        "page_number",
        "date",
        "description",
        "amount",
        "balance",
        "raw_line",
    ]
    ensure_headers(worksheet, headers)
    rows = list(rows)
    if rows:
        worksheet.append_rows(rows, value_input_option="USER_ENTERED")

def _build_gsheet_rows(filename: str, upload_id: str, transactions: list[dict[str, Any]]) -> list[list]:
    rows: list[list] = []
    for tx in transactions:
        rows.append(
            [
                upload_id,
                filename,
                tx.get("page_number"),
                tx.get("date"),
                tx.get("description"),
                tx.get("amount"),
                tx.get("balance"),
                tx.get("raw_line"),
            ]
        )
    return rows