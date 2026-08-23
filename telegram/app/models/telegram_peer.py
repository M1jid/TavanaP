import sqlalchemy as sql

from app.core.database import Base


class TelegramPeer(Base):
    __tablename__ = "telegram_peers"

    id = sql.Column(sql.BigInteger, primary_key=True, autoincrement=True)
    username = sql.Column(sql.String(33), nullable=True, default=None)
    url = sql.Column(sql.String(100), nullable=True, default=None)
    peer_id = sql.Column(sql.BigInteger, unique=True, nullable=True, default=None)
    blocked = sql.Column(sql.Boolean, default=False)
    linked_peer_id = sql.Column(sql.BigInteger, nullable=True, default=None)
    subscriber = sql.Column(sql.BigInteger, nullable=True, default=None)
    is_channel = sql.Column(sql.Boolean, nullable=True, default=True)
    on_waiting = sql.Column(sql.Boolean, default=False)
