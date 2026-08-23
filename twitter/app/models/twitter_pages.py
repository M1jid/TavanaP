import sqlalchemy as sql

from app.core.database import Base


class TwitterPage(Base):
    __tablename__ = "twitter_pages"

    id = sql.Column(sql.BigInteger, primary_key=True, autoincrement=True)
    user_id: str = sql.Column(sql.String(32), nullable=True, default=None)
    rest_id: str = sql.Column(sql.BigInteger, nullable=True, default=None)
    link: str = sql.Column(sql.String(100), nullable=True, default=None)
    avatar_url: str = sql.Column(sql.String(100), nullable=True, default=None)
    name: str = sql.Column(sql.String(100), nullable=True, default=None)
    screen_name: str = sql.Column(sql.String(100), nullable=True, default=None)
    join_date: str = sql.Column(sql.DateTime, nullable=True, default=None)
    verified: bool = sql.Column(sql.Boolean, default=False)
    description: str = sql.Column(sql.String(1000), nullable=True, default=None)
    favourites_count: int = sql.Column(sql.BigInteger, nullable=True, default=0)
    followers_count: int = sql.Column(sql.BigInteger, nullable=True, default=0)
    friends_count: int = sql.Column(sql.BigInteger, nullable=True, default=0)
    normal_followers_count: int = sql.Column(sql.BigInteger, nullable=True, default=0)
    profile_banner_url: str = sql.Column(sql.String(200), nullable=True, default=None)
    statuses_count: int = sql.Column(sql.BigInteger, nullable=True, default=0)
    location: str = sql.Column(sql.String(100), nullable=True, default=None)
    protected: bool = sql.Column(sql.Boolean, default=False)
    listed_count: int = sql.Column(sql.BigInteger, nullable=True, default=0)
    media_count: int = sql.Column(sql.BigInteger, nullable=True, default=0)
