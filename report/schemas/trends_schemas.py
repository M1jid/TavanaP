from pydantic import BaseModel, Field
from typing import List
from datetime import date, timedelta


class GetTopTrendsOverviewInput(BaseModel):
    end_date: str = Field(
        ..., 
        example=date.today().strftime("%Y-%m-%d"), 
        description="Start date of the analysis range"
    )
    start_date: str = Field(
        ..., 
        example=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"),
        description="End date of the analysis range"
    )


class GetTopTrendsTitleInput(BaseModel):
    title: str = Field(
        ..., 
        example="تورم", 
        description="Keyword for trend analysis"
    )
    end_date: str = Field(
        ..., 
        example=date.today().strftime("%Y-%m-%d"), 
        description="Start date of the analysis range"
    )
    start_date: str = Field(
        ..., 
        example=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"),
        description="End date of the analysis range"
    )


class GetTopTrendsContent(BaseModel):
    id: int = 0
    start_date: str = Field(
        ..., 
        example=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"),
        description="End date of the analysis range"
    )
    end_date: str = Field(
        ..., 
        example=date.today().strftime("%Y-%m-%d"), 
        description="Start date of the analysis range"
    )


class QueryClause(BaseModel):
    must: List[str] = Field(default_factory=list)
    must_not: List[str] = Field(default_factory=list)
    should: List[str] = Field(default_factory=list)


class GetTopTrendsFilter(BaseModel):
    query: List[QueryClause] = Field(..., example=[{"must": ["والیبال"], "must_not": ["شکست", "باخت", "حذف"], "should": ["ایران", "کشورمون"]}], description="Each query clause must only contain 'must', 'must_not', and 'should' as keys, and their values must be lists of strings.")
    start_date: str = Field(
        ..., 
        example=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"),
        description="End date of the analysis range"
    )
    end_date: str = Field(
        ..., 
        example=date.today().strftime("%Y-%m-%d"), 
        description="Start date of the analysis range"
    )
