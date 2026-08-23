import sqlalchemy as sql
from sqlalchemy.dialects.postgresql import ARRAY

from app.core.database import Base


class TelegramAccount(Base):
    __tablename__ = "telegram_accounts"

    id = sql.Column(sql.BigInteger, primary_key=True, autoincrement=True)
    phone = sql.Column(sql.BigInteger, nullable=False, unique=True)
    api_id = sql.Column(sql.BigInteger, nullable=False, unique=False)
    api_hash = sql.Column(sql.String(100), nullable=False, unique=False)
    session_file = sql.Column(sql.String(100), nullable=False, unique=True)
    process = sql.Column(sql.Integer, nullable=False, default=0)
    roles = sql.Column(ARRAY(sql.String(10)), default=[])
