import re
import secrets
from datetime import datetime, timedelta

import bcrypt

from models import MitbewohnerDB, Session


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def validate_password(pw: str) -> str | None:
    """Gibt eine Fehlermeldung zurück oder None bei gültigem Passwort."""
    if len(pw) < 8:
        return "Mindestens 8 Zeichen"
    if not re.search(r'[A-Z]', pw):
        return "Mindestens ein Großbuchstabe"
    if not re.search(r'\d', pw):
        return "Mindestens eine Zahl"
    return None


def register_user(first: str, last: str, email: str, password: str) -> tuple:
    """Gibt (user_id, None) bei Erfolg oder (None, Fehlermeldung) zurück."""
    with Session() as session:
        email = email.strip().lower()
        existing = session.query(MitbewohnerDB).filter(MitbewohnerDB.email == email).first()
        if existing:
            return None, "Diese E-Mail-Adresse ist bereits registriert."
        err = validate_password(password)
        if err:
            return None, err
        user = MitbewohnerDB(
            name=f"{first.strip()} {last.strip()}",
            email=email,
            password_hash=_hash(password),
        )
        session.add(user)
        session.commit()
        return user.id, None


def authenticate_user(email: str, password: str) -> int | None:
    """Gibt die user_id bei Erfolg zurück, sonst None."""
    with Session() as session:
        user = session.query(MitbewohnerDB).filter(
            MitbewohnerDB.email == email.strip().lower()
        ).first()
        if not user or not user.password_hash:
            return None
        return user.id if _verify(password, user.password_hash) else None


def get_user_by_id(user_id: int) -> dict | None:
    with Session() as session:
        u = session.get(MitbewohnerDB, user_id)
        if not u:
            return None
        return {
            "id": u.id,
            "name": u.name,
            "email": u.email or "",
            "avatar_path": u.avatar_path,
            "color": u.color,
        }


def update_profile(user_id: int, first: str, last: str, email: str) -> str | None:
    """Gibt None bei Erfolg oder eine Fehlermeldung zurück."""
    with Session() as session:
        email = email.strip().lower()
        clash = session.query(MitbewohnerDB).filter(
            MitbewohnerDB.email == email,
            MitbewohnerDB.id != user_id,
        ).first()
        if clash:
            return "Diese E-Mail-Adresse wird bereits verwendet."
        user = session.get(MitbewohnerDB, user_id)
        if user:
            user.name = f"{first.strip()} {last.strip()}"
            user.email = email
            session.commit()
    return None


def change_password(user_id: int, current_pw: str, new_pw: str) -> str | None:
    """Gibt None bei Erfolg oder eine Fehlermeldung zurück."""
    with Session() as session:
        user = session.get(MitbewohnerDB, user_id)
        if not user or not user.password_hash:
            return "Nutzer nicht gefunden."
        if not _verify(current_pw, user.password_hash):
            return "Aktuelles Passwort ist falsch."
        err = validate_password(new_pw)
        if err:
            return err
        user.password_hash = _hash(new_pw)
        session.commit()
    return None


def create_reset_token(email: str) -> str | None:
    """Erstellt ein Reset-Token für die E-Mail-Adresse. Gibt das Token oder None zurück."""
    with Session() as session:
        user = session.query(MitbewohnerDB).filter(
            MitbewohnerDB.email == email.strip().lower()
        ).first()
        if not user:
            return None
        token = secrets.token_urlsafe(32)
        user.reset_token = token
        user.reset_token_expires = datetime.now() + timedelta(hours=1)
        session.commit()
    return token


def reset_password_with_token(token: str, new_pw: str) -> str | None:
    """Gibt None bei Erfolg oder eine Fehlermeldung zurück."""
    with Session() as session:
        user = session.query(MitbewohnerDB).filter(MitbewohnerDB.reset_token == token).first()
        if not user:
            return "Ungültiger oder abgelaufener Link."
        if not user.reset_token_expires or datetime.now() > user.reset_token_expires:
            return "Dieser Link ist abgelaufen. Bitte neu anfordern."
        err = validate_password(new_pw)
        if err:
            return err
        user.password_hash = _hash(new_pw)
        user.reset_token = None
        user.reset_token_expires = None
        session.commit()
    return None


def save_avatar(user_id: int, path: str) -> None:
    with Session() as session:
        user = session.get(MitbewohnerDB, user_id)
        if user:
            user.avatar_path = path
            session.commit()
