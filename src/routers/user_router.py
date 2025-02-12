from asyncio import sleep
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.routers.validators import validate_master_pass
from src.service.user_service import UserService, get_user_service

router = APIRouter()

class RegisterPayload(BaseModel):
    name: str
    username: str
    password: str

class LoginPayload(BaseModel):
    username: str
    password: str

@router.post('/login')
async def login(data: LoginPayload, user_service: Annotated[UserService, Depends(get_user_service)]):
    token = user_service.login(data.username, data.password)
    if token:
        return token
    else:
        await sleep(3)
        raise HTTPException(403)
    
@router.post('/register', dependencies=[Depends(validate_master_pass)])
async def register(data: RegisterPayload, user_service: Annotated[UserService, Depends(get_user_service)]):
    user_service.create_user(data.name, data.username, data.password)