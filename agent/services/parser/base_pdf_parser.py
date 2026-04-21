import io
from typing import Any

import pdfplumber


class BasePdfParser:
    document_type = "unknown"

    def _build_base_result(self) -> dict[str, Any]:
        return {
            "pages": [],
            "tables": [],
            "transactions": [],
            "statements": [],
            "full_text": "",
            "quality": {},
        }

    def parse(self, file_bytes: bytes) -> dict[str, Any]:
        result = self._build_base_result()

        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text() or ""
                self.process_page(result, page_number, page, page_text)

        return result

    def process_page(self, result: dict[str, Any], page_number: int, page, page_text: str) -> None:
        raise NotImplementedError