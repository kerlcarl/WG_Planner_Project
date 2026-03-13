from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

# Das ist die Basis-Klasse, von der alle Tabellen erben
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    color = Column(String, default='#336699') # Kennfarbe für die UI
    
    # Beziehung: Ein User kann viele Aufgaben und Ausgaben haben
    tasks = relationship("Task", back_populates="assignee")
    expenses = relationship("Expense", back_populates="payer")

class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    is_done = Column(Boolean, default=False)
    is_urgent = Column(Boolean, default=False)
    
    # Fremdschlüssel: Verknüpft die Aufgabe mit einem User
    assignee_id = Column(Integer, ForeignKey('users.id'))
    assignee = relationship("User", back_populates="tasks")

class Expense(Base):
    __tablename__ = 'expenses'
    
    id = Column(Integer, primary_key=True)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String) # z.B. Lebensmittel, Miete
    
    # Wer hat gezahlt?
    payer_id = Column(Integer, ForeignKey('users.id'))
    payer = relationship("User", back_populates="expenses")