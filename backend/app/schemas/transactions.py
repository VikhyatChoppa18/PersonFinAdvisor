"""Transaction schemas."""
from pydantic import BaseModel
from datetime import datetime


class TransactionResponse(BaseModel):
    """Transaction response schema."""
    id: int
    transaction_id: str
    amount: float
    date: datetime
    name: str
    category: str | None
    merchant_name: str | None
    is_pending: bool
    
    class Config:
        from_attributes = True

