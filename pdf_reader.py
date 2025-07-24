import requests
from io import BytesIO

def download_pdf(url: str) -> BytesIO:
    with open("test.pdf", "rb") as f:
        return BytesIO(f.read())

