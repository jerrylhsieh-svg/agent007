import io
from typing import Any

import pdfplumber

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
                pass
            
            
