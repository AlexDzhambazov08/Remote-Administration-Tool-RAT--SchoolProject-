from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import redis
import random
import string
import jwt
import time

# ------------------------------
# CONFIG
# ------------------------------
REDIS_HOST = "localhost"
REDIS_PORT = 6379
OTP_EXPIRY_SECONDS = 300      # 5 minutes
JWT_SECRET = "CHANGE_THIS_SECRET"
JWT_ALGO = "HS256"

# ------------------------------
# REDIS CLIENT
# ------------------------------
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# ------------------------------
# FASTAPI INIT
# ------------------------------
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ------------------------------
# MODELS
# ------------------------------
class OTPRequest(BaseModel):
    email: str

class OTPVerify(BaseModel):
    email: str
    otp: str


# ------------------------------
# UTIL: GENERATE OTP
# ------------------------------
def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

# ------------------------------
# UTIL: CREATE JWT
# ------------------------------
def create_jwt(email: str):
    payload = {
        "email": email,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600  # 1h expiry
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

# ------------------------------
# API: REQUEST OTP
# ------------------------------
@app.post("/auth/request-otp")
def request_otp(data: OTPRequest):
    email = data.email.lower()

    # Rate-limit: 1 OTP per minute
    rl_key = f"otp_rl:{email}"
    if r.exists(rl_key):
        raise HTTPException(status_code=429, detail="OTP already sent. Try again later.")

    otp = generate_otp()

    # Save OTP
    otp_key = f"otp:{email}"
    r.setex(otp_key, OTP_EXPIRY_SECONDS, otp)

    # Create rate limit key (TTL 60 seconds)
    r.setex(rl_key, 60, "1")

    # In a real environment send via email/SMS
    print(f"[DEBUG] OTP for {email} = {otp}")

    return {"status": "ok", "message": "OTP sent"}

# ------------------------------
# API: VERIFY OTP
# ------------------------------
@app.post("/auth/verify-otp")
def verify_otp(data: OTPVerify):
    email = data.email.lower()
    otp_key = f"otp:{email}"

    stored_otp = r.get(otp_key)
    if stored_otp is None:
        raise HTTPException(status_code=401, detail="OTP expired or not found")

    if stored_otp != data.otp:
        raise HTTPException(status_code=401, detail="Invalid OTP")

    # OTP is valid → delete it
    r.delete(otp_key)

    # Issue JWT
    token = create_jwt(email)

    return {"status": "ok", "token": token}


# ------------------------------
# PROTECTED ROUTE (for testing)
# ------------------------------
@app.get("/protected")
def protected_route(token: str = Depends(oauth2_scheme)):
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return {"status": "ok", "email": decoded["email"]}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")