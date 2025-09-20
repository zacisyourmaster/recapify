from typing import Optional
from sqlmodel import SQLModel, Field


class Users(SQLModel, table=True):

    id: Optional[int] = Field(default=None, primary_key=True)
    spotify_user_id: str = Field(index=True, unique=True, nullable=False)
    email: Optional[str] = Field(default=None)
    display_name: Optional[str] = Field(default=None)
    access_token: Optional[str] = Field(default=None)
    refresh_token: str = Field(nullable=False)
