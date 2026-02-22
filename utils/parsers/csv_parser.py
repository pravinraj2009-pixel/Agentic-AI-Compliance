
import csv, hashlib
from utils.parsers.base_parser import BaseParser

class CSVParser(BaseParser):
    def parse(self, file_path):
        with open(file_path) as f:
            rows = list(csv.DictReader(f))
        return {
            "raw_text": str(rows),
            "fields": rows,
            "metadata": {
                "source_type": "CSV",
                "file_hash": hashlib.md5(open(file_path,'rb').read()).hexdigest(),
                "ocr_used": False
            }
        }
