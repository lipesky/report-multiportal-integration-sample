import hashlib
from functools import lru_cache
from sqlite3 import Cursor
from time import time
from typing import Annotated
import jwt
import logging

from fastapi import Depends
from src.model.settings import Settings, get_settings
from src.database.database import db

#TODO: separate persistence logic to a repository class
class UserService:

    def __init__(self, settings:Settings):
        self.settings = settings

    def create_user(self, name: str | None, username: str, password: str):
        if name is None or name == '':
            name = username
        name = name.strip()
        username = username.strip()
        password = password.strip()
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        db.execute('''
            INSERT INTO user(
                username,
                name,
                password
            ) VALUES (
                '{username}',
                '{name}',
                '{password}'
            )
        '''.format(username=username, name=name, password=password_hash))
        db.commit()

    def login(self, username: str, password: str) -> str | None:
        username = username.strip()
        password = password.strip()
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor: Cursor
        try:
            cursor = db.cursor()
            cursor.execute('''
                SELECT id, username, name 
                FROM user
                WHERE
                    username = '{username}' AND password = '{password}'
            '''.format(username=username, password=password_hash))
            user = cursor.fetchone()
            if user:
                return jwt.encode(
                    payload={
                        'user_id': user[0],
                        'expires_at': time() + self.settings.jwt_expiration_secs
                    },
                    key=self.settings.jwt_secret,
                )
        except Exception as e:
            logging.exception('login failed', e)
            logging.info('LOGIN FAILED - username: {username}'.format(username=username))
        finally:
            if cursor:
                cursor.close()

@lru_cache()
def get_user_service(settings: Annotated[Settings, Depends(get_settings)]):
    return UserService(settings)