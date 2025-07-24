from fastapi import FastAPI, HTTPException
from models import PDFRequest, PDFResponse
from pdf_reader import download_pdf
from parser_module import extract_order_info

app = FastAPI()

@app.post("/process-pdf", response_model=PDFResponse)
def process_pdf(request: PDFRequest):
    try:
        pdf_bytes = download_pdf(request.fileUrl)
        data = extract_order_info(pdf_bytes)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
