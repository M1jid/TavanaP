from pickle import LIST
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, UTC
from typing import Optional, List, Dict, Any
from datetime import date, timedelta
from schemas.trends_schemas import QueryClause
from pydantic import BaseModel, model_validator
from enum import Enum


# ------------------------------------------- TelegramChannelsUnderFollow ------------------------------------------- #

class BaseTelegramChannelsUnderFollow(BaseModel):
    channel_id: int = Field(..., gt=0, description="Must be a positive integer referencing an existing telegram channel")
    added_at: Optional[datetime] = datetime.now(UTC)
    is_active: Optional[bool] = True
    priority: Optional[int] = 0
    notes: Optional[str] = None

class UpdateTelegramChannelsUnderFollow(BaseTelegramChannelsUnderFollow):
    pass

class CreateTelegramChannelsUnderFollow(BaseTelegramChannelsUnderFollow):
    pass

class TelegramChannelsUnderFollow(BaseModel):
    id: int

# ------------------------------------------- TelegramUsersUnderFollow ------------------------------------------- #

class BaseTelegramUsersUnderFollow(BaseModel):
    user_id: int = Field(..., gt=0, description="Must be a positive integer")
    username: Optional[str] = None
    added_at: Optional[datetime] = datetime.now(UTC)
    is_active: Optional[bool] = True
    priority: Optional[int] = 0
    notes: Optional[str] = None

class UpdateTelegramUsersUnderFollow(BaseTelegramUsersUnderFollow):
    pass

class CreateTelegramUsersUnderFollow(BaseTelegramUsersUnderFollow):
    pass

class TelegramUsersUnderFollow(BaseTelegramUsersUnderFollow):
    id: int


class TelegramWordcloudFilter(BaseModel):
    selectedChannels: List[int]
    end_date: str
    start_date: str
    search_text: str


class TelegramChannelsFilter(BaseModel):
    size: int = 12
    batch: int = 1
    selectedChannels: List[int] = []
    end_date: str = date.today().strftime("%Y-%m-%d")
    start_date: str = (date.today() - timedelta(days=10)).strftime("%Y-%m-%d")
    search_text: str = ""


class TelegramUsersFilter(BaseModel):
    size: int = 12
    batch: int = 1
    selectedUsers: List[int] = []
    end_date: str = date.today().strftime("%Y-%m-%d")
    start_date: str = (date.today() - timedelta(days=10)).strftime("%Y-%m-%d")
    search_text: str = ""


class Reaction(BaseModel):
    emoji: Optional[str] = Field(None, alias="EMOJI")
    count: Optional[int] = Field(None, alias="COUNT")


class TelegramMessage(BaseModel):
    AUTHOR_ID: Optional[int] = None
    SPOILER_PARTS: Optional[List[str]] = None
    PEER_TYPE: Optional[str] = None
    LINKS: Optional[List[str]] = None
    SENTIMENT: Optional[str] = None
    MESSAGE: Optional[str] = None
    CODES: Optional[List[str]] = None
    FORWARDS_COUNT: Optional[int] = None
    MESSAGE_ID: Optional[int] = None
    PRIVATE_URL: Optional[str] = None
    MEDIA: Optional[List[str]] = None
    TYPE: Optional[str] = None
    FWD_LINK: Optional[str] = None
    REPLY_LINK: Optional[str] = None
    REACTIONS: Optional[List[Reaction]] = None
    MONOSPACE_PARTS: Optional[List[str]] = None
    REACTIONS_COUNT: Optional[int] = None
    BLOCKQUOTE_PARTS: Optional[List[str]] = None
    VIEWS_COUNT: Optional[int] = None
    MENTIONS: Optional[List[str]] = None
    CLEANED_MESSAGE: Optional[str] = None
    HASHTAGS: Optional[List[str]] = None
    FWD_PEER_TYPE: Optional[str] = None
    DATE: Optional[str] = None
    REPLY_PEER_TYPE: Optional[str] = None
    REPLIES_COUNT: Optional[int] = None
    FWD_PEER_ID: Optional[int] = None
    BOLDED_PARTS: Optional[List[str]] = None
    AUTHOR_TYPE: Optional[str] = None
    STRIKETHROUGHED_PARTS: Optional[List[str]] = None
    FETCH_TIME: Optional[int] = None
    PUBLIC_URL: Optional[str] = None
    PEER_ID: Optional[int] = None
    SENSE: Optional[str] = None
    REPLY_PEER_ID: Optional[int] = None
    TAGS: Optional[List[str]] = None
    IMG: Optional[str] = None


class TelegramChannelMessage(BaseModel):
    messages: List[TelegramMessage]
    total_messages: int
    has_more: bool


class UpdateTelegramChannels(BaseModel):
    url: Optional[str] = None
    username: Optional[str] = None
    peer_id: Optional[int] = None
    blocked: Optional[bool] = None
    linked_peer_id: Optional[int] = None
    subscriber: Optional[int] = None
    is_channel: Optional[bool] = None

class CreateTelegramChannels(BaseModel):
    username: Optional[str] = None
    peer_id: Optional[int] = None
    blocked: Optional[bool] = None
    linked_peer_id: Optional[int] = None
    subscriber: Optional[int] = None
    is_channel: Optional[bool] = None

class ExtendedTelegramMessage(BaseModel):
    message: TelegramMessage
    replies: List[TelegramMessage]


class TelegramCommentDetails(BaseModel):
    message: TelegramMessage
    root_message: Optional[TelegramMessage] = None

# ---------------------- #
class BaseFilterQuery(BaseModel):
    query: List[QueryClause] = Field(
        ...,
        example=[
            {
                "must": ["والیبال"],
                "must_not": ["شکست", "باخت", "حذف"],
                "should": ["ایران", "کشورمون"]
            }
        ],
        description="Each query clause must only contain 'must', 'must_not', and 'should' as keys, and their values must be lists of strings."
    )


class UpdateUserQuery(BaseFilterQuery):
    id: int
    user_id: int


class CreateUserQuery(BaseFilterQuery):
    user_id: int


class BaseFilterQuery(BaseModel):
    query: List[QueryClause] = Field(
        ...,
        example=[
            {
                "must": ["والیبال"],
                "must_not": ["شکست", "باخت", "حذف"],
                "should": ["ایران", "کشورمون"]
            }
        ],
        description="Each query clause must only contain 'must', 'must_not', and 'should' as keys, and their values must be lists of strings."
    )


class Date(BaseModel):
    date_format: str = Field(..., example="yyyy-MM-dd HH:mm", description="date format")
    date_from: Optional[str] = Field(None, example="now-0d/d", description="Start date of the analysis range")
    date_to: Optional[str] = Field(None, example="now-0d/d", description="Start date of the analysis range")
    start_date: Optional[date] = Field(None, example="2025-05-01", description="Start date of the analysis range")
    end_date: Optional[date] = Field(None, example="2025-06-01", description="End date of the analysis range")

    @model_validator(mode="after")
    def check_date_input(self):
        if not self.date_from and not (self.start_date and self.end_date):
            raise ValueError("Provide either `date_from` or both `start_date` and `end_date`.")
        return self


class Query(BaseModel):
    field: str = Field(..., example="MESSAGE", description="The field should pass the query")
    op:    str = Field(..., example="match_phrase", description="")
    type:  str = Field(..., example="text", description="Fields type")
    value: str = Field(..., example="ایران", description="Phrase that we are searching")


class RegularFilter(BaseModel):
    query: List[Query]
    date: Date
    timezone: str = Field(..., example="Asia/Tehran", description="Timezone of contrent times")


class PagingFilter(BaseModel):
    query: List[Query]
    limit: int
    date: Date
    limit:    int = Field(..., example=12, description="Total content count on each page")
    page:     int = Field(..., example=1, description="Current page number")
    timezone: str = Field(..., example="Asia/Tehran", description="Timezone of contrent times")


class TrendsPayload(BaseModel):
    filter: RegularFilter


class TelegramPlatformEntity(str, Enum):
    channel_post = "channel_post"
    channel_comment = "channel_comment"
    group_post = "group_post"


class TelegramHistogramPayload(BaseModel):
    query: List[Query]
    timezone: str = Field(..., example="Asia/Tehran", description="Timezone of contrent times")
    limit:    int = Field(..., example=7, description="Total content count on each page")
    interval: str = Field(..., example="1d", description="Interval")
    platform_entity: TelegramPlatformEntity = Field(
        ..., 
        example="channel_post", 
        description="Total content count on each page"
    )

# -------------------------------------------------------------------------------------------------------
class GetTopTrendsInput(BaseModel):
    title: str = Field(..., example="تورم", description="Keyword for trend analysis")
    start_date: str = Field(..., example="2025-05-01", description="Start date of the analysis range")
    end_date: str = Field(..., example="2025-06-10", description="End date of the analysis range")


class TopTrendsInput(BaseModel):
    start_date: str = Field(..., example="2025-05-01", description="Start date of the analysis range")
    end_date: str = Field(..., example="2025-06-10", description="End date of the analysis range")


class SentimentBreakdown(BaseModel):
    positive: int = 0
    negative: int = 0
    neutral: int = 0


class TelegramPosts(BaseModel):
    DATE: str
    TYPE: str
    FETCH_TIME: int
    LINKS: List[str]
    MENTIONS: List[str]
    HASHTAGS: List[str]
    BOLDED_PARTS: List[str]
    STRIKETHROUGHED_PARTS: List[str]
    MONOSPACE_PARTS: List[str]
    SPOILER_PARTS: List[str]
    BLOCKQUOTE_PARTS: List[str]
    CODES: List[str]
    MEDIA: List[str]
    AUTHOR_ID: int
    AUTHOR_TYPE: str
    PEER_ID: int
    PEER_TYPE: str
    PUBLIC_URL: str
    PRIVATE_URL: str
    MESSAGE_ID: int
    MESSAGE: str
    CLEANED_MESSAGE: str
    REPLY_PEER_TYPE: str
    REPLY_PEER_ID: int
    REPLY_LINK: str
    FWD_PEER_TYPE: str
    FWD_PEER_ID: int
    FWD_LINK: str
    REACTIONS: int
    REACTIONS_COUNT: int
    REPLIES_COUNT: int
    VIEWS_COUNT: int
    FORWARDS_COUNT: int
    TAGS: List[str]
    SENTIMENT: str
    SENSE: str


class TopTrendOutput(BaseModel):
    id: str
    doc_count: int
    platform: str
    name: str
    mentions: int
    growth: int
    sentiment: str
    icon: str
    history: List[int]
    sentimentBreakdown: SentimentBreakdown
    stats: Dict[str, int]
    top_posts: List[TelegramPosts]


class GetChannel(BaseModel):
    CHANNEL_ID: int = Field(..., example=123456789, description="Telegram channel numeric ID")


class word_cloud(BaseModel):
    MESSAGE: str = Field(..., example="وضعیت اقتصادی کشور", description="Keyword to search in messages")
    start_date: str = Field(..., example="2025-05-01", description="Start date of the analysis period")
    end_date: str = Field(..., example="2025-06-10", description="End date of the analysis period")


class SourceTracing(BaseModel):
    MESSAGE: str = Field(..., example=" تهران", description="Keyword to trace sources")
    start_date: str = Field(..., example="2025-05-01", description="Start date of the search")
    end_date: str = Field(..., example="2025-06-10", description="End date of the search")
    Range: str = Field(..., example="10", description="Number of results to return")


class CHannelinsights(BaseModel):
    MESSAGE: str = Field(..., example="خمینی", description="Keyword to analyze sentiment distribution")
    Range: str = Field(..., example="10", description="Number of top channels to include in results")


class Find_Similar(BaseModel):
    MESSAGE: str = Field(..., example="دلار ", description="Reference message text")
    start_date: str = Field(..., example="2025-05-01", description="Start date of the similarity search")
    end_date: str = Field(..., example="2025-06-10", description="End date of the similarity search")
    sort: str = Field(..., example="MULT", description="Sort method: MULT, DATE, or VIEWS")
