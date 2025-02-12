from datetime import datetime
from pydantic import BaseModel

class User(BaseModel):
    id: int
    username: str
    name: str
    password: str
    active: int
    created_at: datetime