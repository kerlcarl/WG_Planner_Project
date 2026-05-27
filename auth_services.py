from models import MitbewohnerDB, Session


def get_user_by_id(user_id: int) -> dict | None:
    with Session() as session:
        u = session.get(MitbewohnerDB, user_id)
        if not u:
            return None
        return {
            "id": u.id,
            "name": u.name,
            "avatar_path": u.avatar_path,
            "color": u.color,
        }


def save_avatar(user_id: int, path: str) -> None:
    with Session() as session:
        user = session.get(MitbewohnerDB, user_id)
        if user:
            user.avatar_path = path
            session.commit()
