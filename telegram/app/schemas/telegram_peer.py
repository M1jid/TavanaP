from pydantic import BaseModel, model_validator
from typing import Optional


class TelegramSchemaBasePeer(BaseModel):
    username: str
    url: str
    peer_id: int
    blocked: bool
    linked_peer_id: int
    subscriber: int
    is_channel: bool
    on_waiting: bool


class TelegramSchemaResponsePeer(TelegramSchemaBasePeer):
    id: int


class TelegramSchemaCreatePeer(BaseModel):
    username: Optional[str] = None
    url: Optional[str] = None
    peer_id: Optional[int] = None
    blocked: Optional[bool] = False
    linked_peer_id: Optional[int] = None
    subscriber: Optional[int] = None
    is_channel: Optional[bool] = False
    on_waiting: Optional[bool] = False

    @model_validator(mode="after")
    def check_constraints(self):
        if self.username or self.url:
            if self.username:
                if self.username.startswith("@"):
                    self.username = self.username[1:]
                elif self.username.startswith("https://t.me/"):
                    self.username = self.username[13:]

            if self.url:
                if self.url.startswith("@"):
                    self.url = f'https://t.me/{self.url[1:]}'
                elif not self.url.startswith("https://t.me/"):
                    self.url = f'https://t.me/{self.url}'

            if not self.url:
                self.url = f'https://t.me/{self.username}'
            if not self.username:
                self.username = self.url[13:]

            return self

        if self.linked_peer_id and not self.is_channel:
            return self
        raise ValueError(
            "Must provide (username and url) OR (linked_peer_id with is_channel=False)"
        )


class TelegramSchemaUpdatePeer(BaseModel):
    username: Optional[str] = None
    url: Optional[str] = None
    peer_id: Optional[int] = None
    blocked: Optional[bool] = None
    linked_peer_id: Optional[int] = None
    subscriber: Optional[int] = None
    is_channel: Optional[bool] = None
    on_waiting: Optional[bool] = None
