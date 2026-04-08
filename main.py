# Einstiegspunkt der App und Aufbau der Hauptseite mit NiceGUI.
from typing import List
from nicegui import ui
from sqlalchemy.orm import Session as SQLSession
import random

# Importiere die Datenbank-Logik und Modelle aus deiner models.py
from models import Session, MitbewohnerDB, Task, Expense, init_db

class WGManager:
    """
    Diese Klasse ist der 'Manager' (Application Layer).
    Sie kapselt alle Datenbank-Zugriffe (Unit 3: Encapsulation).
    """
    def __init__(self) -> None:
        # Initialisiert die Datenbank-Tabellen (Unit 6/7)
        init_db()
        # Wir erstellen eine persistente Session für den Manager
        self.db: SQLSession = Session()
        self.titel: str = "FHNW WG-Planner"

    def get_all_users(self) -> List[MitbewohnerDB]:
        """Gibt alle Bewohner zurück (Unit 1: Type Hints)."""
        return self.db.query(MitbewohnerDB).all()

    def get_all_tasks(self) -> List[Task]:
        """Gibt alle Aufgaben zurück."""
        return self.db.query(Task).all()
    
    def get_all_expenses(self) -> List[Expense]:
        """Gibt alle Ausgaben zurück."""
        return self.db.query(Expense).all()

    def bewohner_hinzufuegen(self, name: str, color: str) -> None:
        """Erstellt einen neuen Bewohner und speichert ihn (Unit 3: SRP)."""
        if name.strip():
            neuer_user = MitbewohnerDB(name=name, color=color)
            self.db.add(neuer_user)
            self.db.commit() # Dank expire_on_commit=False in models.py bleibt das Objekt 'bound'
            ui.notify(f'{name} wurde hinzugefügt!', color=color)
            render_content.refresh()
        else:
            ui.notify('Bitte einen Namen eingeben!', type='negative')

    def aufgabe_erstellen(self, titel: str, prioritaet: str) -> None:
        """Weist eine neue Aufgabe einem zufälligen Bewohner zu."""
        bewohner = self.get_all_users()
        if not bewohner:
            ui.notify('Keine Bewohner vorhanden!', type='warning')
            return
        
        zuständiger = random.choice(bewohner)
        neue_aufgabe = Task(
            title=titel, 
            priority=prioritaet, 
            assigned_to=zuständiger
        )
        self.db.add(neue_aufgabe)
        self.db.commit()
        ui.notify(f'Aufgabe zugewiesen an {zuständiger.name}')
        render_content.refresh()

    def task_status_aendern(self, task: Task) -> None:
        """Ändert den Status einer Aufgabe (Unit 4: Object Interaction)."""
        task.is_done = not task.is_done
        self.db.commit()
        render_content.refresh()

    def ausgabe_hinzufuegen(self, beschreibung: str, betrag: float, bezahlt_von_id: int, teilnehmer_ids: List[int]) -> None:
        """Fügt eine neue Ausgabe hinzu."""
        if not beschreibung.strip() or betrag <= 0:
            ui.notify('Bitte gültige Beschreibung und Betrag eingeben!', type='negative')
            return
        
        bezahlt_von = self.db.query(MitbewohnerDB).get(bezahlt_von_id)
        if not bezahlt_von:
            ui.notify('Ungültiger Bezahler!', type='negative')
            return
        
        teilnehmer = self.db.query(MitbewohnerDB).filter(MitbewohnerDB.id.in_(teilnehmer_ids)).all()
        if not teilnehmer:
            ui.notify('Keine Teilnehmer ausgewählt!', type='negative')
            return
        
        neue_ausgabe = Expense(
            description=beschreibung,
            amount=betrag,
            paid_by=bezahlt_von,
            participants=teilnehmer
        )
        self.db.add(neue_ausgabe)
        self.db.commit()
        ui.notify('Ausgabe hinzugefügt!')
        render_content.refresh()

# Erstelle eine einzige Instanz des Managers
manager = WGManager()

# --- UI LAYER (NiceGUI Framework) ---

@ui.refreshable
def render_content() -> None:
    """Rendert den Inhalt der Tabs (Unit 9/10)."""
    with ui.tabs().classes('w-full shadow-2') as tabs:
        ui.tab('Mitglieder', icon='group')
        ui.tab('Ämtli', icon='checklist')
        ui.tab('Finanzen', icon='payments')

    with ui.tab_panels(tabs, value='Mitglieder').classes('w-full max-w-2xl mx-auto'):
        
        # TAB 1: MITGLIEDER
        with ui.tab_panel('Mitglieder'):
            with ui.card().classes('q-pa-md shadow-lg'):
                ui.label('Neuer Mitbewohner').classes('text-h6 text-primary')
                name_in = ui.input(label='Name')
                color_in = ui.color_input(label='Kennfarbe', value='#336699')
                ui.button('Hinzufügen', on_click=lambda: manager.bewohner_hinzufuegen(
                    name_in.value, color_in.value
                )).classes('w-full q-mt-md')
            
            ui.label('Aktuelle WG').classes('text-h5 q-mt-lg')
            with ui.row().classes('w-full'):
                for b in manager.get_all_users():
                    ui.chip(b.name, icon='person').style(f'background-color: {b.color}; color: white')

        # TAB 2: ÄMTLI (Task Scheduler)
        with ui.tab_panel('Ämtli'):
            with ui.card().classes('q-pa-md shadow-lg'):
                ui.label('Neue Aufgabe').classes('text-h6')
                titel_in = ui.input('Was ist zu tun?')
                prio_in = ui.select(['Normal', 'Dringend'], value='Normal')
                ui.button('Zuweisen', on_click=lambda: manager.aufgabe_erstellen(
                    titel_in.value, prio_in.value
                )).classes('w-full q-mt-sm')

            ui.label('Aufgabenliste').classes('text-h5 q-mt-lg')
            for t in manager.get_all_tasks():
                with ui.row().classes('items-center border-b w-full p-2 justify-between'):
                    # Unit 7: Zugriff auf verknüpftes Objekt (assigned_to)
                    with ui.row().classes('items-center'):
                        label_style = 'text-decoration: line-through; opacity: 0.5' if t.is_done else ''
                        ui.label(f"{t.title} ({t.assigned_to.name})").style(label_style)
                        if t.priority == 'Dringend' and not t.is_done:
                            ui.badge('!', color='red')
                    
                    ui.checkbox(value=t.is_done, on_change=lambda _, t=t: manager.task_status_aendern(t))

        # TAB 3: FINANZEN (Platzhalter)
        with ui.tab_panel('Finanzen'):
            with ui.card().classes('q-pa-md shadow-lg'):
                ui.label('Neue Ausgabe').classes('text-h6')

        beschreibung_in = ui.input('Beschreibung')
        betrag_in = ui.number('Betrag', value=0)

        users = manager.get_all_users()
        user_options = {str(u.id): u.name for u in users}

        bezahlt_von = ui.select(user_options, label='Bezahlt von')
        teilnehmer = ui.select(user_options, label='Teilnehmer', multiple=True)

        ui.button('Speichern', on_click=lambda: manager.ausgabe_hinzufuegen(
            beschreibung_in.value,
            betrag_in.value,
            int(bezahlt_von.value) if bezahlt_von.value else None,
            [int(t) for t in teilnehmer.value] if teilnehmer.value else []
        )).classes('w-full q-mt-sm')

    ui.label('Ausgabenliste').classes('text-h5 q-mt-lg')

    for e in manager.get_all_expenses():
        with ui.card().classes('w-full q-mb-sm'):
            ui.label(f"{e.description} - {e.amount:.2f} CHF")
            ui.label(f"Bezahlt von: {e.paid_by.name if e.paid_by else 'Unbekannt'}")

            anteil = e.calculate_share()
            ui.label(f"Pro Person: {anteil:.2f} CHF")

            teilnehmer_namen = ', '.join([p.name for p in e.participants])
            ui.label(f"Teilnehmer: {teilnehmer_namen}")

@ui.page('/')
def main_page() -> None:
    ui.query('body').style('background-color: #f0f2f5')
    with ui.header().classes('bg-primary q-pa-md items-center justify-between'):
        ui.label(manager.titel).classes('text-h4 text-white')
    render_content()

# Startet die App
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(port=8080, title="WG-Planner")
