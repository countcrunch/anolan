from fastapi import FastAPI, HTTPException, Header, Request
from models import PDFRequest, PDFResponse
from pdf_reader import download_pdf
from parser_module import extract_order_info

API_KEY = "supersecret"  # Match this in Google Apps Script

app = FastAPI()

@app.post("/process-pdf", response_model=PDFResponse)
def process_pdf(request: PDFRequest, x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        pdf_bytes = download_pdf(request.fileUrl)
        data = extract_order_info(pdf_bytes)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
