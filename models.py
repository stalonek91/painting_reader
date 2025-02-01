from pydantic import BaseModel

class PaintingInfo(BaseModel):
    title: str  
    author: str
    year: int   
    description_of_historical_event_in_3_sentences: str  
    total_tokens_usage_cost: int


class New_paint(BaseModel):
    title: str
    author: str
    year: int
    total_tokens_usage_cost: int