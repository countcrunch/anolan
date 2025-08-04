import requests
from io import BytesIO

def download_pdf(url: str) -> BytesIO:
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to download PDF. Status: {response.status_code}")
    return BytesIO(response.content)
