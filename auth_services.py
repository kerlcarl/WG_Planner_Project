import re
import secrets
from datetime import datetime, timedelta

from passlib.context import CryptContext

from models import MitbewohnerDB, Session

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

_PASSWORD_RE = re.compile(r'^(?=.*[A-Z])(?=.*\d).{8,}$')


def _get_session():
    return Session()


def validate_password(pw: str) -> str | None:
    """Returns an error string or None if valid."""
    if len(pw) < 8:
        return "Mindestens 8 Zeichen"
    if not re.search(r'[A-Z]', pw):
        return "Mindestens ein Großbuchstabe"
    if not re.search(r'\d', pw):
        return "Mindestens eine Zahl"
    return None


def register_user(first: str, last: str, email: str, password: str) -> tuple:
    """Returns (user_id, error_str). One of the two is always None."""
    session = _get_session()
    email = email.strip().lower()
    existing = session.query(MitbewohnerDB).filter(MitbewohnerDB.email == email).first()
    if existing:
        session.close()
        return None, "Diese E-Mail-Adresse ist bereits registriert."
    err = validate_password(password)
    if err:
        session.close()
        return None, err
    user = MitbewohnerDB(
        name=f"{first.strip()} {last.strip()}",
        email=email,
        password_hash=_pwd.hash(password),
    )
    session.add(user)
    session.commit()
    user_id = user.id
    session.close()
    return user_id, None


def authenticate_user(email: str, password: str) -> int | None:
    """Returns user_id on success, None on failure."""
    session = _get_session()
    user = session.query(MitbewohnerDB).filter(
        MitbewohnerDB.email == email.strip().lower()
    ).first()
    if not user or not user.password_hash:
        session.close()
        return None
    ok = _pwd.verify(password, user.password_hash)
    user_id = user.id if ok else None
    session.close()
    return user_id


def get_user_by_id(user_id: int) -> dict | None:
    session = _get_session()
    u = session.get(MitbewohnerDB, user_id)
    if not u:
        session.close()
        return None
    data = {"id": u.id, "name": u.name, "email": u.email or "", "avatar_path": u.avatar_path, "color": u.color}
    session.close()
    return data


def update_profile(user_id: int, first: str, last: str, email: str) -> str | None:
    """Returns error string or None on success."""
    session = _get_session()
    email = email.strip().lower()
    clash = session.query(MitbewohnerDB).filter(
        MitbewohnerDB.email == email,
        MitbewohnerDB.id != user_id,
    ).first()
    if clash:
        session.close()
        return "Diese E-Mail-Adresse wird bereits verwendet."
    user = session.get(MitbewohnerDB, user_id)
    if user:
        user.name = f"{first.strip()} {last.strip()}"
        user.email = email
        session.commit()
    session.close()
    return None


def change_password(user_id: int, current_pw: str, new_pw: str) -> str | None:
    """Returns error string or None on success."""
    session = _get_session()
    user = session.get(MitbewohnerDB, user_id)
    if not user or not user.password_hash:
        session.close()
        return "Nutzer nicht gefunden."
    if not _pwd.verify(current_pw, user.password_hash):
        session.close()
        return "Aktuelles Passwort ist falsch."
    err = validate_password(new_pw)
    if err:
        session.close()
        return err
    user.password_hash = _pwd.hash(new_pw)
    session.commit()
    session.close()
    return None


def create_reset_token(email: str) -> str | None:
    """Creates a reset token for the given email. Returns the token or None if not found."""
    session = _get_session()
    user = session.query(MitbewohnerDB).filter(
        MitbewohnerDB.email == email.strip().lower()
    ).first()
    if not user:
        session.close()
        return None
    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_token_expires = datetime.now() + timedelta(hours=1)
    session.commit()
    session.close()
    return token


def reset_password_with_token(token: str, new_pw: str) -> str | None:
    """Returns error string or None on success."""
    session = _get_session()
    user = session.query(MitbewohnerDB).filter(MitbewohnerDB.reset_token == token).first()
    if not user:
        session.close()
        return "Ungültiger oder abgelaufener Link."
    if not user.reset_token_expires or datetime.now() > user.reset_token_expires:
        session.close()
        return "Dieser Link ist abgelaufen. Bitte neu anfordern."
    err = validate_password(new_pw)
    if err:
        session.close()
        return err
    user.password_hash = _pwd.hash(new_pw)
    user.reset_token = None
    user.reset_token_expires = None
    session.commit()
    session.close()
    return None


def save_avatar(user_id: int, path: str) -> None:
    session = _get_session()
    user = session.get(MitbewohnerDB, user_id)
    if user:
        user.avatar_path = path
        session.commit()
    session.close()
