from pydantic import BaseModel


class IdentificationDto(BaseModel):
    text: str
    date: str