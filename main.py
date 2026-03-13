from nicegui import ui
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Datenbank-Setup (Persistenzschicht)
engine = create_engine('sqlite:///wg_planner.db')
Base = declarative_base()

class MitbewohnerDB(Base):
    __tablename__ = 'mitbewohner'
    id = Column(Integer, primary_key=True)
    name = Column(String)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# 2. Logik-Klasse (Anwendungslogik / OOP)
class WGManager:
    def __init__(self):
        self.titel = "Unser WG-Planner"

    def bewohner_hinzufuegen(self, name):
        if name:
            neuer_bewohner = MitbewohnerDB(name=name)
            session.add(neuer_bewohner)
            session.commit()
            ui.notify(f'{name} wurde hinzugefügt!')
            self.liste_aktualisieren()

    def liste_aktualisieren(self):
        # Diese Funktion würde die UI-Liste neu laden
        pass

manager = WGManager()

# 3. Frontend (Präsentationsschicht mit NiceGUI)
@ui.page('/')
def main_page():
    ui.label(manager.titel).classes('text-h3 q-ma-md')
    
    with ui.card().classes('w-full max-w-md q-ma-md'):
        ui.label('Neuen Mitbewohner hinzufügen').classes('text-h6')
        name_input = ui.input(label='Name')
        ui.button('Hinzufügen', on_click=lambda: manager.bewohner_hinzufuegen(name_input.value))

    ui.label('Aktuelle Bewohner:').classes('text-h6 q-ma-md')
    # Hier werden die Bewohner aus der Datenbank angezeigt
    bewohner = session.query(MitbewohnerDB).all()
    for b in bewohner:
        ui.label(f'• {b.name}')

# Startet die Anwendung
# `show=False` verhindert, dass NiceGUI versucht, einen Browser zu öffnen.
ui.run(title='WG Planner', port=8080, show=False, show_welcome_message=False)