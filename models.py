"""Datenmodell und Datenbank-Setup für den WG Planner.

Dieses Modul enthält die SQLAlchemy-Modelle und die Initialisierung
der SQLite-Datenbank. Andere Module importieren hieraus `Session`
und die Modellklassen.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker


# ------------------
# Datenbankkonfiguration
# ------------------
# Standardmäßig wird eine lokale SQLite-Datei verwendet.
DATABASE_URL = 'sqlite:///wg_planner.db'

engine = create_engine(DATABASE_URL, echo=False)
Base = declarative_base()


class MitbewohnerDB(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    color = Column(String, nullable=True)
    profile_image_url = Column(String, nullable=True)

    def __repr__(self) -> str:
        return f"<User id={self.id} name={self.name}>"


# Many-to-many link table: welche Nutzer an welcher Ausgabe beteiligt sind.
expense_participants = Table(
    'expense_participants',
    Base.metadata,
    Column('expense_id', ForeignKey('expenses.id'), primary_key=True),
    Column('user_id', ForeignKey('users.id'), primary_key=True),
)


class Expense(Base):
    """Eine gemeinsame Ausgabe, die von einem Nutzer angelegt wurde."""

    __tablename__ = 'expenses'
    id = Column(Integer, primary_key=True)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    paid_by = relationship('MitbewohnerDB', back_populates='expenses_paid')
    participants = relationship('MitbewohnerDB', secondary=expense_participants, back_populates='expenses')

    def split_per_person(self) -> float:
        """Berechnet den Anteil pro beteiligter Person."""
        if not self.participants:
            return 0.0
        return self.amount / len(self.participants)


class Task(Base):
    """Ein Haushaltsposten (Ämtli) mit Zuweisung und Status."""

    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    assigned_to_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    priority = Column(String, nullable=True)
    is_done = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    assigned_to = relationship('MitbewohnerDB', back_populates='tasks')

    def __repr__(self) -> str:
        return f"<Task id={self.id} title={self.title} done={self.is_done}>"


# Erweiterungen für User-Relationen
MitbewohnerDB.expenses_paid = relationship('Expense', back_populates='paid_by')
MitbewohnerDB.expenses = relationship('Expense', secondary=expense_participants, back_populates='participants')
MitbewohnerDB.tasks = relationship('Task', back_populates='assigned_to')


def init_db() -> sessionmaker:
    """Erstellt die Tabellen (falls nötig) und liefert eine Session-Klasse."""

    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


# Für einfache Skripte kann man mit `session = Session()` arbeiten.
Session = init_db()
