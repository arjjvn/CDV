import os
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY=os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is missing from .env")
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30