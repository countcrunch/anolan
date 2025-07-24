from pydantic import BaseModel
from typing import List
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
