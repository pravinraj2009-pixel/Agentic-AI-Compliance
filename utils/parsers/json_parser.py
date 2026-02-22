
import json, hashlib
from utils.parsers.base_parser import BaseParser

class JSONParser(BaseParser):
    def parse(self, file_path):
        with open(file_path) as f:
            data = json.load(f)
        return {
            "raw_text": json.dumps(data),
            "fields": data,
            "metadata": {
                "source_type": "JSON",
                "file_hash": hashlib.md5(open(file_path,'rb').read()).hexdigest(),
                "ocr_used": False
            }
        }
