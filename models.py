from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class DeliveryStop(BaseModel):
    po_number: str
    store: str
    address: str
    datetime: datetime


class PDFResponse(BaseModel):
    sid: Optional[str] = ""
    order_number: Optional[str] = ""
    pickup_location: Optional[str] = ""
    pickup_address: Optional[str] = ""
    pickup_datetime: Optional[datetime] = None
    deliveries: List[DeliveryStop] = Field(default_factory=list)
    pickup_number: Optional[str] = None
    unmatched_stores: List[str] = Field(default_factory=list)


class PDFRequest(BaseModel):
    fileUrl: str

