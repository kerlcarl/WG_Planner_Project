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
def render_users_tab():
    with ui.card().classes('w-full max-w-md q-ma-md'):
        ui.label('Mitbewohner*innen verwalten').classes('text-h6')
        name_input = ui.input(label='Name', placeholder='z. B. Anna')
        color_input = ui.input(label='Kennfarbe (Hex)', placeholder='#00aaff')
        ui.button('Hinzufügen', on_click=lambda: add_user(name_input.value, color_input.value))

    with ui.card().classes('w-full max-w-md q-ma-md'):
        ui.label('Aktuelle Bewohner*innen').classes('text-h6')
        for user in session.query(MitbewohnerDB).order_by(MitbewohnerDB.name):
            ui.row([
                ui.markdown(f'**{user.name}**'),
                ui.label(user.color or '').classes('text-caption'),
            ])


def add_user(name: str, color: str | None = None) -> None:
    if not name:
        ui.notify('Bitte einen Namen eingeben.', color='warning')
        return

    new_user = MitbewohnerDB(name=name.strip(), color=color.strip() if color else None)
    session.add(new_user)
    session.commit()
    ui.notify(f'{name} wurde hinzugefügt!')
    ui.reload()


def render_finances_tab():
    ui.label('Shared Expenses').classes('text-h5 q-mt-md')

    with ui.card().classes('w-full max-w-2xl q-ma-md'):
        ui.label('Neue Ausgabe erfassen').classes('text-h6')
        desc_input = ui.input(label='Beschreibung')
        amount_input = ui.input(label='Betrag (CHF)', type='number')
        category_input = ui.input(label='Kategorie (z. B. Lebensmittel)')
        paid_by_select = ui.select({u.name: u.id for u in session.query(MitbewohnerDB)}, label='Bezahlt von')
        participants_multi = ui.multiselect(
            {u.name: u.id for u in session.query(MitbewohnerDB)},
            label='Beteiligt'
        )
        ui.button('Speichern', on_click=lambda: add_expense(desc_input.value, amount_input.value, category_input.value, paid_by_select.value, participants_multi.value))

    with ui.card().classes('w-full max-w-2xl q-ma-md'):
        ui.label('Saldo (pro Kopf)').classes('text-h6')
        balances = calculate_balances()
        for user in session.query(MitbewohnerDB).order_by(MitbewohnerDB.name):
            amount = balances.get(user.id, 0.0)
            ui.row([
                ui.markdown(f'**{user.name}**'),
                ui.label(f'{amount:0.2f} CHF').classes('text-caption'),
            ])


def add_expense(description: str, amount: str, category: str, paid_by_id: int, participant_ids: list[int]):
    try:
        amount_value = float(amount)
    except Exception:
        ui.notify('Ungültiger Betrag.', color='negative')
        return

    if not description or amount_value <= 0:
        ui.notify('Beschreibung und Betrag sind erforderlich.', color='warning')
        return

    if not paid_by_id:
        ui.notify('Bitte wähle aus, wer bezahlt hat.', color='warning')
        return

    if not participant_ids:
        ui.notify('Bitte mindestens einen Teilnehmer wählen.', color='warning')
        return

    expense = Expense(
        description=description.strip(),
        amount=amount_value,
        category=category.strip() if category else None,
        paid_by_id=paid_by_id,
    )
    # Teilnehmer hinzufügen
    for uid in participant_ids:
        user = session.get(MitbewohnerDB, uid)
        if user:
            expense.participants.append(user)

    session.add(expense)
    session.commit()
    ui.notify('Ausgabe gespeichert.')
    ui.reload()


def render_tasks_tab():
    ui.label('Ämtli & Tasks').classes('text-h5 q-mt-md')

    with ui.card().classes('w-full max-w-2xl q-ma-md'):
        ui.label('Neue Aufgabe').classes('text-h6')
        title_input = ui.input(label='Titel')
        desc_input = ui.input(label='Beschreibung')
        assigned_select = ui.select({u.name: u.id for u in session.query(MitbewohnerDB)}, label='Zugewiesen an')
        ui.button('Erstellen', on_click=lambda: add_task(title_input.value, desc_input.value, assigned_select.value))

    with ui.card().classes('w-full max-w-2xl q-ma-md'):
        ui.label('Aktuelle Aufgaben').classes('text-h6')
        for task in session.query(Task).order_by(Task.id):
            ui.row([
                ui.checkbox(value=task.is_done, on_change=lambda checked, t=task: toggle_task_done(t, checked)),
                ui.label(task.title),
                ui.label(task.assigned_to.name if task.assigned_to else '—').classes('text-caption'),
            ])
        ui.button('Aufgaben rotieren', on_click=lambda: (rotate_tasks(), ui.reload())).classes('q-mt-md')


def add_task(title: str, description: str, assigned_to_id: int):
    if not title:
        ui.notify('Titel erforderlich.', color='warning')
        return

    task = Task(title=title.strip(), description=description.strip() if description else None)
    if assigned_to_id:
        user = session.get(MitbewohnerDB, assigned_to_id)
        if user:
            task.assigned_to = user

    session.add(task)
    session.commit()
    ui.notify('Aufgabe erstellt.')
    ui.reload()


def toggle_task_done(task: Task, done: bool):
    task.is_done = done
    session.commit()
    ui.reload()


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