import secrets
from datetime import datetime, timedelta

OTP_VALID_MINUTES = 5
SESSION_VALID_MINUTES = 30

USER_DB = {
    "admin": "password123"
}

otp_storage = {
    "code": None,
    "expires_at": None,
    "used": False
}

session_storage = {
    "session_id": None,
    "expires_at": None
}

def login(username, password):
    return USER_DB.get(username) == password

def generate_otp():
    code = secrets.randbelow(900000) + 100000
    expires_at = datetime.utcnow() + timedelta(minutes=OTP_VALID_MINUTES)
    otp_storage["code"] = code
    otp_storage["expires_at"] = expires_at
    otp_storage["used"] = False
    return code, expires_at

def verify_otp(input_code):
    if otp_storage["used"]:
        return False
    if datetime.utcnow() > otp_storage["expires_at"]:
        return False
    if input_code != otp_storage["code"]:
        return False
    otp_storage["used"] = True
    return True

def create_session():
    session_id = secrets.token_hex(32)
    expires_at = datetime.utcnow() + timedelta(minutes=SESSION_VALID_MINUTES)
    session_storage["session_id"] = session_id
    session_storage["expires_at"] = expires_at
    return session_id, expires_at

def validate_session(session_id):
    if session_storage["session_id"] != session_id:
        return False
    if datetime.utcnow() > session_storage["expires_at"]:
        return False
    return True

if __name__ == "__main__":
    print("AUTH SYSTEM")

    username = input("Username: ")
    password = input("Password: ")

    if not login(username, password):
        print("Invalid login")
        exit()

    otp, _ = generate_otp()
    print(otp)

    try:
        user_otp = int(input("OTP: "))
    except ValueError:
        print("Invalid OTP")
        exit()

    if not verify_otp(user_otp):
        print("OTP failed")
        exit()

    session_id, _ = create_session()
    print(session_id)

    if validate_session(session_id):
        print("Session valid")
    else:
        print("Session invalid")
