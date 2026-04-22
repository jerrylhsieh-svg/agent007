import io
from typing import Any

import pdfplumber


def extract_pdf_content(file_bytes: bytes) -> dict[str, Any]:
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            pass