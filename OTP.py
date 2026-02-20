from fastapi import FastAPI, HTTPException, Request
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
import secrets
import time

# ======================
# CONFIG
# ======================
SECRET_KEY = "CHANGE_ME_IN_PROD"
ALGORITHM = "HS256"

ACCESS_TOKEN_MINUTES = 30
OTP_VALID_MINUTES = 5
MAX_ATTEMPTS = 5
BLOCK_TIME_SECONDS = 300  # 5 min

# ======================
# APP
# ======================
app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ======================
# MOCK DATABASES
# ======================
users_db = {
    "admin": {
        "password_hash": pwd_context.hash("password123")
    }
}

otp_db = {}
rate_limit_db = {}

# ======================
# UTILS
# ======================
def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def create_token(username):
    payload = {
        "sub": username,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_MINUTES)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def rate_limit(identifier: str):
    now = time.time()
    data = rate_limit_db.get(identifier, {"count": 0, "blocked_until": 0})

    if now < data["blocked_until"]:
        raise HTTPException(status_code=429, detail="Too many attempts. Try later.")

    data["count"] += 1

    if data["count"] >= MAX_ATTEMPTS:
        data["blocked_until"] = now + BLOCK_TIME_SECONDS
        data["count"] = 0

    rate_limit_db[identifier] = data

# ======================
# ROUTES
# ======================
@app.post("/login")
def login(username: str, password: str, request: Request):
    rate_limit(request.client.host)

    user = users_db.get(username)
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    otp = secrets.randbelow(900000) + 100000
    otp_db[username] = {
        "code": otp,
        "expires": datetime.utcnow() + timedelta(minutes=OTP_VALID_MINUTES),
        "used": False
    }

    # В реалност: SMS / Email
    return {"otp": otp}

@app.post("/verify-otp")
def verify_otp(username: str, otp: int):
    record = otp_db.get(username)

    if not record:
        raise HTTPException(status_code=400, detail="OTP not found")

    if record["used"]:
        raise HTTPException(status_code=400, detail="OTP already used")

    if datetime.utcnow() > record["expires"]:
        raise HTTPException(status_code=400, detail="OTP expired")

    if otp != record["code"]:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    record["used"] = True

    token = create_token(username)
    return {"access_token": token, "token_type": "bearer"}

@app.get("/protected")
def protected(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"message": f"Hello {payload['sub']}"}
    except:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


if __name__ == "__main__":
    # convenience runner for development. Run with: python OTP.py
    try:
        import uvicorn
    except Exception:
        raise RuntimeError("uvicorn is required to run the app. Install with: pip install uvicorn[standard]")
    uvicorn.run(app, host="127.0.0.1", port=8000)
