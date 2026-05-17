# Datenmodelle und SQLAlchemy-Konfiguration fuer den WG-Planner.
import os
from datetime import datetime
from typing import List
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Table, UniqueConstraint, create_engine, inspect, text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# Basis-Klasse für SQLAlchemy (Unit 6/7 Thema)
Base = declarative_base()

# Many-to-Many Verknüpfungstabelle für Ausgaben (Unit 7)
# Ermöglicht es, dass eine Ausgabe auf bestimmte Mitbewohner aufgeteilt wird
expense_participants = Table(
    'expense_participants',
    Base.metadata,
    Column('expense_id', Integer, ForeignKey('expenses.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True)
)


# Tabelle fuer Mitbewohner inklusive Relationen zu Aufgaben und Ausgaben.
class MitbewohnerDB(Base):
    """
    Repräsentiert einen WG-Bewohner.
    Verantwortung (SRP): Speicherung von Nutzerdaten und Relationen.
    """
    __tablename__ = 'users'

    id: int = Column(Integer, primary_key=True)
    name: str = Column(String, nullable=False)
    color: str = Column(String, default='#336699')
    email: str = Column(String, unique=True, nullable=True)
    password_hash: str = Column(String, nullable=True)
    avatar_path: str = Column(String, nullable=True)
    reset_token: str = Column(String, nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    
    # Relationships (Unit 7)
    # Ein User hat viele Aufgaben und viele bezahlte Ausgaben
    tasks = relationship("Task", back_populates="assigned_to")
    expenses_paid = relationship("Expense", back_populates="paid_by")
    
    # Many-to-Many: Ausgaben, an denen der User beteiligt ist
    expenses_involved = relationship("Expense", secondary=expense_participants, back_populates="participants")

    def __repr__(self) -> str: # Magic Method (Unit 3, Slide 30)
        return f"<Mitbewohner(name='{self.name}')>"


class Task(Base):
    """
    Repräsentiert ein 'Ämtli'.
    """
    __tablename__ = 'tasks'

    id: int = Column(Integer, primary_key=True)
    title: str = Column(String, nullable=False)
    priority: str = Column(String, default='Normal') # z.B. 'Dringend' (User Story)
    is_done: bool = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    due_date = Column(DateTime, nullable=True)  # Fälligkeitsdatum

    # Foreign Key zu Mitbewohner (Unit 7)
    assigned_to_id = Column(Integer, ForeignKey('users.id'))
    assigned_to = relationship("MitbewohnerDB", back_populates="tasks")


class Post(Base):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True)
    content = Column(String, nullable=False)
    is_important = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    author_id = Column(Integer, ForeignKey('users.id'))
    author = relationship("MitbewohnerDB", foreign_keys=[author_id])
    reactions = relationship("Reaction", back_populates="post", cascade="all, delete-orphan")


class Reaction(Base):
    __tablename__ = 'reactions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=False)
    emoji = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("MitbewohnerDB", foreign_keys=[user_id])
    post = relationship("Post", foreign_keys=[post_id], back_populates="reactions")

    __table_args__ = (
        UniqueConstraint('user_id', 'post_id', 'emoji', name='uq_reaction_user_post_emoji'),
    )


class EinkaufsItem(Base):
    __tablename__ = 'shopping_items'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    menge = Column(String, nullable=True)
    einheit = Column(String, nullable=True)
    is_bought = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    author_id = Column(Integer, ForeignKey('users.id'))
    author = relationship("MitbewohnerDB", foreign_keys=[author_id])


class ManualDebt(Base):
    """Manuell erfasste offene Schuld, die in den Ausgleichsvorschlägen erscheint."""
    __tablename__ = 'manual_debts'

    id: int = Column(Integer, primary_key=True)
    description: str = Column(String, nullable=False)
    amount: float = Column(Float, nullable=False)
    payment_method: str = Column(String, default='Twint')
    created_at = Column(DateTime, default=datetime.now)

    from_user_id = Column(Integer, ForeignKey('users.id'))
    to_user_id = Column(Integer, ForeignKey('users.id'))

    from_user = relationship("MitbewohnerDB", foreign_keys=[from_user_id])
    to_user = relationship("MitbewohnerDB", foreign_keys=[to_user_id])


class Expense(Base):
    """
    Repräsentiert eine finanzielle Ausgabe.
    Beinhaltet Logik zur Kostenaufteilung (Encapsulation).
    """
    __tablename__ = 'expenses'

    id: int = Column(Integer, primary_key=True)
    description: str = Column(String, nullable=False)
    amount: float = Column(Float, nullable=False)
    category: str = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    
    # Wer hat es bezahlt?
    paid_by_id = Column(Integer, ForeignKey('users.id'))
    paid_by = relationship("MitbewohnerDB", back_populates="expenses_paid")

    # Wer ist beteiligt? (Many-to-Many)
    participants = relationship("MitbewohnerDB", secondary=expense_participants, back_populates="expenses_involved")

    def calculate_share(self) -> float:
        """
        Berechnet den Anteil pro Person.
        Beispiel für eine Methode, die auf dem internen State operiert (Unit 3).
        """
        if not self.participants:
            return 0.0
        # Gleichmaessige Aufteilung auf alle Teilnehmer.
        return self.amount / len(self.participants)


# --- Datenbank Initialisierung (Unit 6) ---
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///wg_planner.db')
# Render liefert postgres://, SQLAlchemy braucht postgresql://
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

_is_sqlite = DATABASE_URL.startswith('sqlite')
_connect_args = {'check_same_thread': False} if _is_sqlite else {}
_engine_kwargs: dict = dict(connect_args=_connect_args)
if not _is_sqlite:
    # Prüft Verbindung vor Wiederverwendung; recycelt nach 4 Minuten (< Render-Timeout).
    _engine_kwargs.update(pool_pre_ping=True, pool_recycle=240)
engine = create_engine(DATABASE_URL, **_engine_kwargs)
# Session-Factory fuer DB-Zugriffe in services.py.
Session = sessionmaker(bind=engine)

_SEED_USERS = ["Luca Martin", "Carl Klein"]


def _migrate_sqlite() -> None:
    """Ergänzt fehlende Spalten in bestehenden SQLite-Datenbanken via ORM-Inspektion."""
    inspector = inspect(engine)
    pending: list[tuple[str, str, str]] = [
        ('tasks', 'due_date', 'DATETIME'),
        ('users', 'email', 'TEXT'),
        ('users', 'password_hash', 'TEXT'),
        ('users', 'avatar_path', 'TEXT'),
        ('users', 'reset_token', 'TEXT'),
        ('users', 'reset_token_expires', 'DATETIME'),
    ]
    with engine.connect() as conn:
        for table, col, col_type in pending:
            existing = {c['name'] for c in inspector.get_columns(table)}
            if col not in existing:
                conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {col} {col_type}'))
        conn.commit()


def init_db():
    """Erstellt alle Tabellen basierend auf den Modellen."""
    Base.metadata.create_all(engine)
    # Migration nur fuer bestehende SQLite-DBs noetig; PostgreSQL bekommt das Schema frisch.
    if _is_sqlite:
        _migrate_sqlite()


def seed_db():
    """Legt Standard-Mitbewohner an, falls die Tabelle noch leer ist."""
    session = Session()
    if session.query(MitbewohnerDB).count() == 0:
        for name in _SEED_USERS:
            session.add(MitbewohnerDB(name=name))
        session.commit()
    session.close()
