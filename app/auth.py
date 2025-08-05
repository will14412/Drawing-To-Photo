import os, datetime as dt
from fastapi import Depends, Cookie, HTTPException
from jose import jwt, JWTError
from passlib.context import CryptContext

# ── config ────────────────────────────────────────────────
SECRET = os.getenv("JWT_SECRET", "CHANGE_ME")          # set in shell for prod
ALGO   = "HS256"
pwd    = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── helpers ───────────────────────────────────────────────
def hash_pw(raw: str) -> str:        return pwd.hash(raw)
def verify_pw(raw: str, hashed: str) -> bool: return pwd.verify(raw, hashed)

def create_token(user_id: int) -> str:
    exp = dt.datetime.utcnow() + dt.timedelta(days=7)
    return jwt.encode({"sub": user_id, "exp": exp}, SECRET, ALGO)

def get_current_user(token: str | None = Cookie(default=None)):
    if not token:
        return None               # anonymous
    try:
        data = jwt.decode(token, SECRET, ALGO)
        return int(data["sub"])
    except JWTError:
        raise HTTPException(401, "Invalid token")
