import sqlalchemy as sql
from sqlalchemy.dialects.postgresql import ARRAY

from app.core.database import Base


class TwitterAccount(Base):
    __tablename__ = "twitter_accounts"

    id = sql.Column(sql.BigInteger, primary_key=True, autoincrement=True)
    oauth_token = sql.Column(sql.String(100), nullable=False, unique=True)
    oauth_token_secret = sql.Column(sql.String(100), nullable=False, unique=True)
