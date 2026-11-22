import os
import jwt
from datetime import datetime, timedelta, timezone

monitorerd_server_secret_key = "EPLACE_WITH_YOUR_OWN_SECRET_KEY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_TIME_IN_MINUTES = 30

def create_Access_token(username: str):

    expire = datetime.now(timezone.utc) + timedelta(minutes = ACCESS_TOKEN_EXPIRE_TIME_IN_MINUTES)

    payload ={
        "sub": username,
        "exp": expire
    }

    token = jwt.encode(
        payload,
        monitorerd_server_secret_key,
        ALGORITHM
    )

    return token

def verify_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            monitorerd_server_secret_key,
            algorithms = [ALGORITHM]
        )

        return payload
        
    except jwt.ExpiredSignatureError:
        return False
    
    except jwt.InvalidTokenError:
        return False
