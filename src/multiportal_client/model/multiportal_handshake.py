from pydantic import BaseModel


class MultiportalHandShake(BaseModel):
    username: str
    password: str
    appid: int
    token: str | None
    expiration: int | None