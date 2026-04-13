import os

from jose import JWTError, jwt
from passlib.context import CryptContext


ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _get_secret_key():
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY environment variable is required")
    return secret_key

def encrypt(key):
    """
    Create a new access token
    :param user_id:
    :return:
    """
    payload = {
        "sub": key,
    }
    return jwt.encode(payload, _get_secret_key(), algorithm=ALGORITHM)

def getKey(token):
    """
    Verify the token
    :param token:
    :return:
    """
    try:
        payload = jwt.decode(token, _get_secret_key(), algorithms=[ALGORITHM])
    except JWTError:
        return None
    return payload.get("sub")

# create access token for notion db and api key
# create a script to migrate existing database to encrypted one. 
# decryption at the time of storing stuff in guild_info is required
