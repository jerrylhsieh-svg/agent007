from __future__ import annotations

import os
from typing import Any, Iterable

import gspread
from google.oauth2.service_account import Credentials
from gspread.utils import rowcol_to_a1
import pandas as pd

from agent.services.constants_and_dependencies import GSHEET_NAME, SCOPES, STATEMENT_HEADERS, TRANSACTION_HEADERS



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
    headers: list[str],
) -> None:
    worksheet = get_or_create_worksheet(spreadsheet_name, worksheet_name)
    
    ensure_headers(worksheet, headers)
    rows = list(rows)
    if rows:
        worksheet.append_rows(rows, value_input_option="USER_ENTERED")

def add_labels(
    worksheet_name: str,
    rows: Iterable[tuple[str, str]],
    spreadsheet_name: str = GSHEET_NAME
) -> None:
    worksheet = get_or_create_worksheet(spreadsheet_name, worksheet_name)
    existing_values = worksheet.get_all_values()

    if not existing_values:
        raise ValueError("Worksheet is empty. Expected a header row with an 'id' column.")

    header = existing_values[0]

    if "id" not in header:
        raise ValueError("Worksheet must contain an 'id' column.")

    if "label" not in header:
        raise ValueError("Worksheet must contain a 'label' column.")

    id_col_index = header.index("id")         
    label_col_index = header.index("label")

    id_to_sheet_row_number: dict[str, int] = {}

    for sheet_row_number, row in enumerate(existing_values[1:], start=2):
        if len(row) > id_col_index:
            row_id = row[id_col_index]
            if row_id:
                id_to_sheet_row_number[row_id] = sheet_row_number

    updates = []

    for row_id, label in rows:
        sheet_row_number = id_to_sheet_row_number[row_id]

        label_cell = rowcol_to_a1(sheet_row_number, label_col_index + 1)

        updates.append(
            {
                "range": label_cell,
                "values": [[label]],
            }
        )

    if updates:
        worksheet.batch_update(updates)


def build_gsheet_rows(data: list[dict[str, Any]], fields: list[str]) -> list[list[Any]]:
    rows: list[list] = []
    for row in data:
        rows.append(
            [row.get(field, "") for field in fields]
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