from pydantic import BaseModel, Field

class InstagramTopTrend(BaseModel):
    start_date: str = Field(..., example="2025-05-01", description="Start date of the analysis range")
    end_date: str = Field(..., example="2025-06-10", description="End date of the analysis range")

