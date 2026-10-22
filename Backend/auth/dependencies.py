from fastapi import Depends,HTTPException
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
import jwt

from Backend.auth.config import SECRET_KEY,ALGORITHM

security=HTTPBearer()

def get_current_user(
        credentials:HTTPAuthorizationCredentials=Depends(security),
):
    token=credentials.credentials
    try:
        playload=jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        user_id=playload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )
        return {"user_id":user_id}
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )