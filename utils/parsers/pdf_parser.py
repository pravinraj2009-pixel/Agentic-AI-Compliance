
import pdfplumber, hashlib
from utils.parsers.base_parser import BaseParser

class PDFParser(BaseParser):
    def parse(self, file_path):
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return {
            "raw_text": text,
            "fields": {},
            "metadata": {
                "source_type": "PDF",
                "file_hash": hashlib.md5(open(file_path,'rb').read()).hexdigest(),
                "ocr_used": False
            }
        }
