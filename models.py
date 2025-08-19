from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class DeliveryStop(BaseModel):
    po_number: str
    store: str
    address: str
    datetime: datetime


class PDFResponse(BaseModel):
    sid: str
    order_number: str
    pickup_location: str
    pickup_address: str
    pickup_datetime: datetime
    deliveries: List[DeliveryStop]
    pickup_number: Optional[str] = None
    unmatched_stores: List[str] = []


class PDFRequest(BaseModel):
    fileUrl: str

