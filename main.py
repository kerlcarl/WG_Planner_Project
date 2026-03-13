from nicegui import ui
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# Wichtig: Wir importieren alles aus deiner models.py
from models import Base, User, Task, Expense 

# 1. Datenbank-Setup
engine = create_engine('sqlite:///wg_planner.db', connect_args={'check_same_thread': False})
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# 2. Logik-Klasse (Dein WGManager)
class WGManager:
    def __init__(self):
        self.titel = "Unser WG-Planner"

    def bewohner_hinzufuegen(self, name, color):
        if name:
            # Wir nutzen jetzt die Klasse 'User' aus deinem neuen Modell
            neuer_user = User(name=name, color=color)
            session.add(neuer_user)
            session.commit()
            ui.notify(f'{name} wurde hinzugefügt!', color=color)
            render_bewohner_liste.refresh() # Aktualisiert nur diesen Teil der UI

manager = WGManager()

# 3. Frontend (Präsentationsschicht)

@ui.refreshable
def render_bewohner_liste():
    """Zeigt die aktuelle Liste der Bewohner an."""
    ui.label('Aktuelle Bewohner:').classes('text-h6 q-mt-md')
    bewohner = session.query(User).all()
    if not bewohner:
        ui.label('Noch keine Bewohner eingetragen.').classes('text-italic')
    for b in bewohner:
        with ui.row().classes('items-center q-mb-xs'):
            ui.icon('person').style(f'color: {b.color}')
            ui.label(b.name).classes('text-bold')

@ui.page('/')
def main_page():
    # Style-Anpassung
    ui.query('body').style('background-color: #f5f5f5')

    with ui.column().classes('w-full items-center'):
        ui.label(manager.titel).classes('text-h3 q-ma-lg text-primary')
        
        with ui.card().classes('w-full max-w-md q-pa-md'):
            ui.label('Neuen Mitbewohner hinzufügen').classes('text-h6')
            name_input = ui.input(label='Name')
            # Farbauswahl für das Profil
            color_input = ui.color_input(label='Kennfarbe', value='#336699')
            
            ui.button('Hinzufügen', on_click=lambda: manager.bewohner_hinzufuegen(
                name_input.value, color_input.value
            )).classes('w-full q-mt-md')

        # Die Liste wird in einem eigenen Bereich gerendert
        with ui.column().classes('w-full max-w-md q-ma-md'):
            render_bewohner_liste()

# Startet die Anwendung
ui.run(title='WG Planner', port=8080)