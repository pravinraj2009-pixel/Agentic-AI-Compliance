
def clean_ocr_text(text):
    for a,b in {'O':'0','I':'1','l':'1'}.items():
        text = text.replace(a,b)
    return text
