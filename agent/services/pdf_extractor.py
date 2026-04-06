# agent/app/services/pdf_extractor.py
from __future__ import annotations

import io
import json
from typing import Any
from fastapi import HTTPException
from pathlib import Path
from fastapi import File, HTTPException, UploadFile
import pdfplumber


UPLOAD_DIR = Path("/tmp/agent_uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def extract_pdf_content(file_bytes: bytes) -> dict[str, Any]:
    result: dict[str, Any] = {
        "pages": [],
        "tables": [],
        "full_text": "",
    }

    full_text_parts: list[str] = []

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text() or ""
            full_text_parts.append(f"\n--- Page {page_number} ---\n{page_text}")

            result["pages"].append(
                {
                    "page_number": page_number,
                    "text": page_text,
                }
            )

            page_tables = page.extract_tables()
            for table_index, table in enumerate(page_tables, start=1):
                result["tables"].append(
                    {
                        "page_number": page_number,
                        "table_index": table_index,
                        "rows": table,
                    }
                )

    result["full_text"] = "\n".join(full_text_parts)
    return result


async def extract_pdf_service(file: UploadFile = File(...)):
    if file.content_type not in {"application/pdf"}:
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    extracted = extract_pdf_content(file_bytes)

    saved_path = UPLOAD_DIR / f"{file.filename}.json"
    saved_path.write_text(json.dumps(extracted, ensure_ascii=False, indent=2))

    return {
        "filename": file.filename,
        "page_count": len(extracted["pages"]),
        "table_count": len(extracted["tables"]),
        "data": extracted,
        "saved_to": str(saved_path),
    }