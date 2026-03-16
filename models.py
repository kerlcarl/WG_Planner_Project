from datetime import datetime
from typing import List
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Table, create_engine
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

    # Foreign Key zu Mitbewohner (Unit 7)
    assigned_to_id = Column(Integer, ForeignKey('users.id'))
    assigned_to = relationship("MitbewohnerDB", back_populates="tasks")


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
        return self.amount / len(self.participants)


# --- Datenbank Initialisierung (Unit 6) ---
DATABASE_URL = 'sqlite:///wg_planner.db'
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
Session = sessionmaker(bind=engine)

def init_db():
    """Erstellt alle Tabellen basierend auf den Modellen."""
    Base.metadata.create_all(engine)