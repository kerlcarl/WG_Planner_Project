# Datenmodelle und SQLAlchemy-Konfiguration fuer den WG-Planner.
from datetime import datetime
from typing import List
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Table, create_engine, text
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
    color: str = Column(String, default='#336699') # Kennfarbe (Unit 9 NiceGUI)
    
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
DATABASE_URL = 'sqlite:///wg_planner.db'
# SQLite-Engine; check_same_thread=False ist fuer UI-Threads noetig.
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
# Session-Factory fuer DB-Zugriffe in services.py.
Session = sessionmaker(bind=engine)

def init_db():
    """Erstellt alle Tabellen basierend auf den Modellen."""
    Base.metadata.create_all(engine)
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN due_date DATETIME"))
            conn.commit()
        except Exception:
            pass  # Spalte existiert bereits
