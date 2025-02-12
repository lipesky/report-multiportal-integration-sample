import jwt
import hashlib
import logging
from time import time
from typing import Annotated
from fastapi import Depends, HTTPException, Header
from src.model.settings import Settings, get_settings

def validate_valid_jwt(settings: Annotated[Settings, Depends(get_settings)], authentication: Annotated[str | None, Header()] = None):
    try:
        payload = jwt.decode(authentication, settings.jwt_secret, algorithms=['HS256'])
        logging.info(payload)
        if payload['expires_at'] < time():
            raise Exception()
    except Exception as e:
        print(e)
        raise HTTPException(403)
    
def validate_master_pass(settings: Annotated[Settings, Depends(get_settings)], authentication: Annotated[str | None, Header()] = None):
    try:
       print(authentication, settings.master_pass)
       token_hash = hashlib.sha256(authentication.encode())
       desired_hash = hashlib.sha256(settings.master_pass.encode())
       if token_hash.hexdigest() != desired_hash.hexdigest():
           raise Exception()
    except Exception as ex:
        print(ex)
        raise HTTPException(403)