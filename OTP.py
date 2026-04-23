from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import redis
import random
import jwt
import time

# ----------------------------
# CONFIG
# ----------------------------
REDIS_HOST = "localhost"
REDIS_PORT = 6379
OTP_EXPIRY_SECONDS = 300   # 5 minutes
JWT_SECRET = "CHANGE_THIS_SECRET"
JWT_ALGO = "HS256"

# OTP character set: digits + symbols (excludes ambiguous 0/O/1/l)
OTP_DIGITS  = "23456789"
OTP_SYMBOLS = "!@#$%^&*"
OTP_CHARSET = OTP_DIGITS + OTP_SYMBOLS
OTP_LENGTH  = 8

# ----------------------------
# REDIS CLIENT
# ----------------------------
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# ----------------------------
# FASTAPI INIT
# ----------------------------
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ----------------------------
# MODELS
# ----------------------------
class OTPRequest(BaseModel):
    user_id: str

class OTPVerify(BaseModel):
    user_id: str
    otp: str

# ----------------------------
# UTIL: GENERATE OTP (digits + symbols, guaranteed >=1 of each)
# ----------------------------
def generate_otp(length: int = OTP_LENGTH) -> str:
    if length < 2:
        raise ValueError("OTP length must be at least 2")
    chars = [random.choice(OTP_DIGITS), random.choice(OTP_SYMBOLS)]
    chars += random.choices(OTP_CHARSET, k=length - 2)
    random.shuffle(chars)
    return "".join(chars)

# ----------------------------
# UTIL: CREATE JWT
# ----------------------------
def create_jwt(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

# ----------------------------
# API: REQUEST OTP
# ----------------------------
@app.post("/auth/request-otp")
def request_otp(data: OTPRequest):
    uid = data.user_id.strip().lower()
    if not uid:
        raise HTTPException(status_code=400, detail="user_id is required")

    rl_key = f"otp_rl:{uid}"
    if r.exists(rl_key):
        raise HTTPException(
            status_code=429,
            detail="OTP already sent. Try again in 60 seconds."
        )

    otp = generate_otp()

    otp_key = f"otp:{uid}"
    r.setex(otp_key, OTP_EXPIRY_SECONDS, otp)
    r.setex(rl_key, 60, "1")

    # In production: send OTP via SMS / push / any other channel
    print(f"[DEBUG] OTP for user_id={uid!r} -> {otp}")

    return {"status": "ok", "message": "OTP issued"}

# ----------------------------
# API: VERIFY OTP
# ----------------------------
@app.post("/auth/verify-otp")
def verify_otp(data: OTPVerify):
    uid = data.user_id.strip().lower()
    otp_key = f"otp:{uid}"

    stored_otp = r.get(otp_key)
    if stored_otp is None:
        raise HTTPException(status_code=401, detail="OTP expired or not found")

    if stored_otp != data.otp:
        raise HTTPException(status_code=401, detail="Invalid OTP")

    r.delete(otp_key)

    token = create_jwt(uid)
    return {"status": "ok", "token": token}

# ----------------------------
# PROTECTED ROUTE (test)
# ----------------------------
@app.get("/protected")
def protected_route(token: str = Depends(oauth2_scheme)):
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return {"status": "ok", "user_id": decoded["sub"]}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
