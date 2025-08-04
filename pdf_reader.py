import requests
from io import BytesIO
import re

def download_pdf(url: str) -> BytesIO:
    # Try to extract the file ID from the shared Drive URL
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
    if not match:
        raise Exception("Invalid Google Drive file URL format")

    file_id = match.group(1)
    direct_url = f"https://drive.google.com/uc?export=download&id={file_id}"

    response = requests.get(direct_url)
    if response.status_code != 200:
        raise Exception(f"Failed to download PDF. Status: {response.status_code}")
    
    return BytesIO(response.content)
