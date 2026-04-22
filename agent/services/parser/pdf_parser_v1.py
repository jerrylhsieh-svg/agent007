from dataclasses import asdict
import io
from typing import Any

import pdfplumber

from agent.services.parser.boa_bank_parser import BOABankPdfParser
from agent.services.parser.boa_credit_parser import BOACreditPdfParser

def determin_pdf_type(line, pdf_info):
        if "Bank of America" in line and pdf_info["bank"] is None:
            pdf_info["bank"] = "BOA"
    
        if "your statement" in line and pdf_info["credit"] is None:
            pdf_info["credit"] = False
        elif "Minimum payment due" in line and pdf_info["credit"] is None:
            pdf_info["credit"] = True
        
        return pdf_info

def extract_pdf_content(file_bytes: bytes) -> dict[str, Any]:
    pdf_info: dict[str, Any] = {"bank":None, "credit":None}
    full_text_parts: list[str] = []
    data = []
    result: dict[str, Any] = {}
    pdf_parser: BOACreditPdfParser | BOABankPdfParser
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            if pdf_info["bank"] is None or pdf_info["credit"] is None:
                page_text = page.extract_text() or ""
                for raw_line in page_text.splitlines():
                    line = raw_line.strip()
                    if not line:
                        continue

                    pdf_info = determin_pdf_type(line, pdf_info)
            else:
                if pdf_info["credit"] is True:
                    pdf_parser = BOACreditPdfParser()
                else:
                    pdf_parser = BOABankPdfParser()
                
                page_result = pdf_parser.process_page(page_number, page)

                full_text_parts.append(f"\n--- Page {page_number} ---\n{page_result['page_text']}")
                data.extend(page_result["data"])

    result["full_text"] = "\n".join(full_text_parts)
    pdf_parser.normalize_records(data, result["full_text"])
    result["data"] = [asdict(row) for row in data]

    return result
                
            
