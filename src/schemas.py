from pydantic import BaseModel, ConfigDict
from typing import Optional, List

class ChatModel(BaseModel):
    id: int
    title: str
    type: str
    added_at: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class UserModel(BaseModel):
    id: int
    username: Optional[str]
    full_name: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class InviteLinkModel(BaseModel):
    id: int
    user_id: int
    chat_id: int
    invite_link: str
    created_at: str
    expires_at: str

    model_config = ConfigDict(from_attributes=True)

class InviteLinkIn(BaseModel):
    user_id: int
    chat_id: int
    invite_link: str
    created_at: str
    expires_at: str

class AlgorithmProgressModel(BaseModel):
    user_id: int
    current_step: int
    basic_completed: bool
    advanced_completed: bool
    updated_at: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class LinkVisitIn(BaseModel):
    link_key: str
