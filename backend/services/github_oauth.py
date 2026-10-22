import os

from cryptography.fernet import Fernet, InvalidToken
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


SESSION_COOKIE = "aicar_github_session"
OAUTH_STATE_MAX_AGE = 600


def oauth_configuration() -> dict[str, str]:
    values = {
        "client_id": os.getenv("GITHUB_CLIENT_ID", ""),
        "client_secret": os.getenv("GITHUB_CLIENT_SECRET", ""),
        "redirect_uri": os.getenv(
            "GITHUB_REDIRECT_URI",
            "http://localhost:5173/api/github/callback",
        ),
        "frontend_url": os.getenv("FRONTEND_URL", "http://localhost:5173"),
        "session_secret": os.getenv("GITHUB_SESSION_SECRET", ""),
        "encryption_key": os.getenv("GITHUB_TOKEN_ENCRYPTION_KEY", ""),
    }
    return values


def oauth_is_configured() -> bool:
    config = oauth_configuration()
    if not all(config[key] for key in ("client_id", "client_secret", "session_secret", "encryption_key")):
        return False
    if len(config["session_secret"]) < 32:
        return False
    if os.getenv("APP_ENV", "development").lower() == "production" and not config["redirect_uri"].startswith("https://"):
        return False
    try:
        Fernet(config["encryption_key"].encode("ascii"))
    except (ValueError, UnicodeEncodeError):
        return False
    return True


def state_serializer() -> URLSafeTimedSerializer:
    secret = oauth_configuration()["session_secret"]
    if not secret:
        raise ValueError("GitHub OAuth session signing is not configured")
    return URLSafeTimedSerializer(secret, salt="aicar-github-oauth")


def encrypt_token(token: str) -> str:
    key = oauth_configuration()["encryption_key"]
    if not key:
        raise ValueError("GitHub OAuth token encryption is not configured")
    return Fernet(key.encode("ascii")).encrypt(token.encode("utf-8")).decode("ascii")


def decrypt_token(encrypted_token: str) -> str:
    key = oauth_configuration()["encryption_key"]
    if not key:
        raise ValueError("GitHub OAuth token encryption is not configured")
    try:
        return Fernet(key.encode("ascii")).decrypt(encrypted_token.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError, UnicodeEncodeError) as error:
        raise ValueError("Stored GitHub authorization is invalid; please reconnect GitHub") from error
