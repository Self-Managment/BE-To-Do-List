import datetime

import jwt
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import SECRET_KEY, ALGORITHM
from app.db.session import get_db
from app.models.user_models import User, get_user_model_by_username

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_TOKEN_EXPIRE_DAYS = 3000

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def create_access_token(user) -> str:
    """
    Функция создания токена
    """
    expire = datetime.datetime.utcnow() + datetime.timedelta(
        days=ACCESS_TOKEN_EXPIRE_DAYS
    )
    to_encode = {
        "sub": user.username,
        "id": user.id,
        "user_id": user.id,
        "exp": expire,
        "token_type": "access",
    }

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    authorization: str = Header(...), db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Вы не авторизованы",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise credentials_exception
    except (ValueError, jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        raise credentials_exception

    db_user: User = await get_user_model_by_username(username, db)

    if db_user is None:
        raise credentials_exception

    return db_user
