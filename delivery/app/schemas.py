from pydantic import BaseModel
from typing import Optional


class FilePayload(BaseModel):
    channel_id: int
    file_path: str
    caption: Optional[str] = ""
    pin: Optional[bool] = False
