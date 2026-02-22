
import pytesseract, cv2, hashlib
from utils.parsers.base_parser import BaseParser

class ImageParser(BaseParser):
    def parse(self, file_path):
        img = cv2.imread(file_path)
        text = pytesseract.image_to_string(img)
        return {
            "raw_text": text,
            "fields": {},
            "metadata": {
                "source_type": "IMAGE",
                "file_hash": hashlib.md5(open(file_path,'rb').read()).hexdigest(),
                "ocr_used": True
            }
        }
