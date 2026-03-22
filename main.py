from nicegui import ui

from models import Expense, MitbewohnerDB, Session, Task, engine, Base


# Session-Factory (SQLAlchemy) wird in models.py initialisiert.
# Für jeden Request eine neue Session erstellen
def get_session():
    return Session()

# Dark Mode State
dark_mode = False

# 2. Logik-Klasse (Anwendungslogik / OOP)
def calculate_balances() -> dict[int, float]:
    """Berechnet den Saldo (Zahlung minus Anteil) pro Nutzer."""

    session = get_session()
    users = session.query(MitbewohnerDB).all()
    balances = {u.id: 0.0 for u in users}

    for expense in session.query(Expense).all():
        share = expense.calculate_share()
        for user in expense.participants:
            balances[user.id] -= share
        balances[expense.paid_by_id] += expense.amount

    session.close()
    return balances


def rotate_tasks() -> None:
    """Rotiert alle offenen Aufgaben zum nächsten Mitbewohner."""

    session = get_session()
    users = session.query(MitbewohnerDB).order_by(MitbewohnerDB.id).all()
    if not users:
        session.close()
        return

    tasks = session.query(Task).filter_by(is_done=False).all()
    for task in tasks:
        if not task.assigned_to:
            task.assigned_to = users[0]
        else:
            idx = next((i for i, u in enumerate(users) if u.id == task.assigned_to.id), 0)
            task.assigned_to = users[(idx + 1) % len(users)]

    session.commit()
    session.close()

# 3. Frontend (Präsentationsschicht mit NiceGUI)
users_container = None

def refresh_users_list():
    """Aktualisiert die Benutzerliste dynamisch ohne Seite neu zu laden."""
    global users_container
    if users_container:
        users_container.clear()
        session = get_session()
        users = session.query(MitbewohnerDB).order_by(MitbewohnerDB.name)
        card_class = 'dark:bg-gray-700 dark:border-blue-400 bg-gradient to-r from-blue-50 to-indigo-50 border-l-4 border-blue-500' if dark_mode else 'bg-gradient to-r from-blue-50 to-indigo-50 border-l-4 border-blue-500'
        if users.count() == 0:
            ui.label('Noch keine Bewohner*innen hinzugefügt.').classes('text-gray-500 italic')
        else:
            for user in users:
                with ui.card().classes(f'w-full {card_class} mb-2'):
                    with ui.row().classes('w-full items-center justify-between p-3'):
                        ui.label(f'{user.name}').classes('text-h6 font-bold')
                        with ui.row().classes('gap-2'):
                            ui.button('Bearbeiten', on_click=lambda u=user: edit_user(u)).classes('bg-indigo-500 text-white')
                            ui.button('Löschen', on_click=lambda u=user: delete_user(u)).classes('bg-red-500 text-white')
        session.close()

def render_users_tab():
    global users_container
    session = get_session()
    card_class = 'dark:bg-gray-800 dark:text-white bg-white' if dark_mode else 'bg-white'
    label_class = 'dark:text-blue-300 text-blue-700' if dark_mode else 'text-blue-700'
    input_class = 'dark:bg-gray-700 dark:text-white' if dark_mode else ''
    
    with ui.column().classes('w-full h-full overflow-auto'):
        with ui.row().classes('w-full gap-4 p-6'):
            # Form für neuen Mitbewohner
            with ui.card().classes(f'flex-grow {card_class} shadow-md rounded-lg'):
                ui.label('Neuen Mitbewohner hinzufügen').classes(f'text-h6 font-bold {label_class}')
                ui.separator().classes('my-3')
                name_input = ui.input(label='Name', placeholder='z. B. Anna').classes(f'w-full {input_class}')
                def on_add_click():
                    add_user(name_input.value)
                    name_input.value = ''  # Leere das Input-Feld
                ui.button('Hinzufügen', on_click=on_add_click).classes('w-full bg-blue-500 text-white font-bold py-2 rounded-lg hover:bg-blue-600')

            # Liste der Bewohner
            with ui.card().classes(f'flex-grow {card_class} shadow-md rounded-lg'):
                ui.label('Aktuelle Bewohner*innen').classes(f'text-h6 font-bold {label_class}')
                ui.separator().classes('my-3')
                users_container = ui.column().classes('w-full')
                with users_container:
                    users = session.query(MitbewohnerDB).order_by(MitbewohnerDB.name)
                    card_item_class = 'dark:bg-gray-700 dark:border-blue-400 bg-gradient to-r from-blue-50 to-indigo-50 border-l-4 border-blue-500' if dark_mode else 'bg-gradient to-r from-blue-50 to-indigo-50 border-l-4 border-blue-500'
                    if users.count() == 0:
                        ui.label('Noch keine Bewohner*innen hinzugefügt.').classes('text-gray-500 italic')
                    else:
                        for user in users:
                            with ui.card().classes(f'w-full {card_item_class} mb-2'):
                                with ui.row().classes('w-full items-center justify-between p-3'):
                                    ui.label(f'{user.name}').classes('text-h6 font-bold')
                                    with ui.row().classes('gap-2'):
                                        ui.button('Bearbeiten', on_click=lambda u=user: edit_user(u)).classes('bg-indigo-500 text-white')
                                        ui.button('Löschen', on_click=lambda u=user: delete_user(u)).classes('bg-red-500 text-white')
    session.close()


def add_user(name: str) -> None:
    if not name:
        ui.notify('Bitte einen Namen eingeben.', color='warning')
        return

    session = get_session()
    new_user = MitbewohnerDB(name=name.strip())
    session.add(new_user)
    session.commit()
    session.close()
    ui.notify(f'{name} wurde hinzugefügt!')
    refresh_users_list()


def edit_user(user: MitbewohnerDB):
    with ui.dialog() as dialog:
        ui.label(f'Bearbeite {user.name}').classes('text-h6')
        name_input = ui.input(label='Name', value=user.name)
        with ui.row():
            ui.button('Speichern', on_click=lambda: save_edit(user, name_input.value, dialog))
            ui.button('Abbrechen', on_click=dialog.close)
    dialog.open()


def save_edit(user: MitbewohnerDB, name: str, dialog):
    if not name:
        ui.notify('Name erforderlich.', color='warning')
        return
    session = get_session()
    user.name = name.strip()
    session.merge(user)
    session.commit()
    session.close()
    ui.notify('Gespeichert!')
    dialog.close()
    refresh_users_list()


def delete_user(user: MitbewohnerDB):
    session = get_session()
    session.delete(user)
    session.commit()
    session.close()
    ui.notify(f'{user.name} wurde gelöscht!')
    refresh_users_list()


def render_finances_tab():
    session = get_session()
    card_class = 'dark:bg-gray-800 dark:text-white bg-white' if dark_mode else 'bg-white'
    label_class = 'dark:text-green-300 text-green-700' if dark_mode else 'text-green-700'
    input_class = 'dark:bg-gray-700 dark:text-white' if dark_mode else ''
    
    with ui.column().classes('w-full h-full overflow-auto'):
        with ui.row().classes('w-full gap-4 p-6'):
            # Form für neue Ausgabe
            with ui.card().classes(f'flex-grow {card_class} shadow-md rounded-lg'):
                ui.label('Neue Ausgabe erfassen').classes(f'text-h6 font-bold {label_class}')
                ui.separator().classes('my-3')
                desc_input = ui.input(label='Beschreibung', placeholder='z. B. Lebensmittel').classes(f'w-full {input_class}')
                amount_input = ui.number(label='Betrag (CHF)').classes(f'w-full {input_class}')
                category_input = ui.input(label='Kategorie', placeholder='z. B. Lebensmittel').classes(f'w-full {input_class}')
                paid_by_select = ui.select({u.name: u.id for u in session.query(MitbewohnerDB)}, label='Bezahlt von').classes(f'w-full {input_class}')
                participants_multi = ui.select(
                    {u.name: u.id for u in session.query(MitbewohnerDB)},
                    label='Beteiligt',
                    multiple=True
                ).classes(f'w-full {input_class}')
                ui.button('Speichern', on_click=lambda: add_expense(desc_input.value, amount_input.value, category_input.value, paid_by_select.value, participants_multi.value)).classes('w-full bg-green-500 text-white font-bold py-2 rounded-lg hover:bg-green-600')

            # Saldo-Übersicht
            with ui.card().classes(f'flex-grow {card_class} shadow-md rounded-lg'):
                ui.label('Saldo pro Person').classes(f'text-h6 font-bold {label_class}')
                ui.separator().classes('my-3')
                balances = calculate_balances()
                users = session.query(MitbewohnerDB).order_by(MitbewohnerDB.name)
                card_item_class = 'dark:bg-gray-700 dark:border-green-400 bg-green-50 border-l-4 border-green-500' if dark_mode else 'bg-green-50 border-l-4 border-green-500'
                if users.count() == 0:
                    ui.label('Noch keine Mitbewohner*innen hinzugefügt.').classes('text-gray-500 italic')
                else:
                    # Sortiere nach Saldo (höchste zuerst)
                    sorted_users = sorted(users, key=lambda u: balances.get(u.id, 0.0), reverse=True)
                    for user in sorted_users:
                        amount = balances.get(user.id, 0.0)
                        with ui.card().classes(f'w-full {card_item_class} mb-2'):
                            with ui.row().classes('w-full items-center justify-between p-3'):
                                ui.label(f'{user.name}').classes('text-h6 font-bold')
                                ui.label(f'CHF {amount:0.2f}').classes(f'text-h6 font-bold {label_class}')
    session.close()


def add_expense(description: str, amount: float, category: str, paid_by_id: int, participant_ids: list[int]):
    amount_value = amount
    if not isinstance(amount_value, (int, float)) or amount_value <= 0:
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

    session = get_session()
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
    session.close()
    ui.notify('Ausgabe gespeichert.')
    ui.reload()


def render_tasks_tab():
    session = get_session()
    card_class = 'dark:bg-gray-800 dark:text-white bg-white' if dark_mode else 'bg-white'
    label_class = 'dark:text-orange-300 text-orange-700' if dark_mode else 'text-orange-700'
    input_class = 'dark:bg-gray-700 dark:text-white' if dark_mode else ''
    
    with ui.column().classes('w-full h-full overflow-auto'):
        with ui.row().classes('w-full gap-4 p-6'):
            # Form für neue Aufgabe
            with ui.card().classes(f'flex-grow {card_class} shadow-md rounded-lg'):
                ui.label('Neue Aufgabe erstellen').classes(f'text-h6 font-bold {label_class}')
                ui.separator().classes('my-3')
                title_input = ui.input(label='Titel', placeholder='z. B. Putzen').classes(f'w-full {input_class}')
                desc_input = ui.input(label='Beschreibung', placeholder='Optional').classes(f'w-full {input_class}')
                assigned_select = ui.select({u.name: u.id for u in session.query(MitbewohnerDB)}, label='Zugewiesen an').classes(f'w-full {input_class}')
                ui.button('Erstellen', on_click=lambda: add_task(title_input.value, desc_input.value, assigned_select.value)).classes('w-full bg-orange-500 text-white font-bold py-2 rounded-lg hover:bg-orange-600')

            # Aufgaben-Liste
            with ui.card().classes(f'flex-grow {card_class} shadow-md rounded-lg'):
                ui.label('Aktuelle Aufgaben').classes(f'text-h6 font-bold {label_class}')
                ui.separator().classes('my-3')
                tasks = session.query(Task).order_by(Task.id)
                card_item_class = 'dark:bg-gray-700 dark:border-orange-400 bg-yellow-100 border-l-4 border-orange-500' if dark_mode else 'bg-yellow-100 border-l-4 border-orange-500'
                if tasks.count() == 0:
                    ui.label('Noch keine Aufgaben hinzugefügt.').classes('text-gray-500 italic')
                else:
                    for task in tasks:
                        status_class = 'dark:bg-green-900 bg-green-100 line-through' if task.is_done else card_item_class
                        with ui.card().classes(f'w-full {status_class} mb-2'):
                            with ui.row().classes('w-full items-center justify-between p-3'):
                                ui.checkbox(value=task.is_done, on_change=lambda checked, t=task: toggle_task_done(t, checked))
                                with ui.column().classes('flex-grow'):
                                    ui.label(f'{task.title}').classes('text-h6 font-bold')
                                    ui.label(f'{task.assigned_to.name if task.assigned_to else "Niemand"}').classes('text-caption text-gray-600')
                with ui.row().classes('w-full p-3 border-t'):
                    ui.button('Aufgaben rotieren', on_click=lambda: (rotate_tasks(), ui.reload())).classes('bg-purple-500 text-white font-bold rounded-lg hover:bg-purple-600')
    session.close()


def add_task(title: str, description: str, assigned_to_id: int):
    if not title:
        ui.notify('Titel erforderlich.', color='warning')
        return

    session = get_session()
    task = Task(title=title.strip(), description=description.strip() if description else None)
    if assigned_to_id:
        user = session.get(MitbewohnerDB, assigned_to_id)
        if user:
            task.assigned_to = user

    session.add(task)
    session.commit()
    session.close()
    ui.notify('Aufgabe erstellt.')
    ui.reload()


def toggle_task_done(task: Task, done: bool):
    session = get_session()
    task.is_done = done
    session.merge(task)
    session.commit()
    session.close()
    ui.reload()


@ui.page('/')
def main_page():
    global dark_mode
    
    # Container für die Hauptseite, damit wir sie neu zeichnen können
    main_container = ui.column().classes('w-full h-screen')
    
    def toggle_dark_mode():
        global dark_mode
        dark_mode = not dark_mode
        main_container.clear()
        render_main_content(main_container)
    
    def render_main_content(container):
        with container:
            # Background basierend auf Dark Mode
            bg_class = 'dark:bg-gray-900 dark:text-white bg-gradient to-r from-blue-50 to-indigo-50' if dark_mode else 'bg-gradient to-r from-blue-50 to-indigo-50'
            
            # Header
            header_class = 'dark:bg-gray-800 bg-gradient to-r from-blue-500 to-indigo-600 text-white' if dark_mode else 'bg-gradient to-r from-blue-500 to-indigo-600 text-white'
            with ui.row().classes(f'w-full {header_class} shadow-lg p-6 items-center'):
                ui.label('WG Planner - Verwaltung für gemeinsames Wohnen').classes('text-h4 font-bold flex-grow')
                ui.button('Dunkel' if not dark_mode else 'Hell', on_click=toggle_dark_mode).classes('bg-blue-700 text-white px-4 py-2 rounded-lg hover:bg-blue-800')
            
            # Tabs
            with ui.row().classes('w-full'):
                with ui.column().classes('w-full'):
                    with ui.tabs().classes('w-full') as tabs:
                        ui.tab('Mitbewohner*innen', icon='group')
                        ui.tab('Finanzen', icon='attach_money')
                        ui.tab('Aufgaben', icon='checklist')

                    with ui.tab_panels(tabs, value='Mitbewohner*innen').classes('w-full'):
                        with ui.tab_panel('Mitbewohner*innen').classes('w-full'):
                            render_users_tab()
                        with ui.tab_panel('Finanzen').classes('w-full'):
                            render_finances_tab()
                        with ui.tab_panel('Aufgaben').classes('w-full'):
                            render_tasks_tab()
    
    # Initial render
    render_main_content(main_container)

# Startet die Anwendung
# `show=False` verhindert, dass NiceGUI versucht, einen Browser zu öffnen.
ui.run(title='WG Planner - Verwaltung für gemeinsames Wohnen', port=8080, show=False, show_welcome_message=False)