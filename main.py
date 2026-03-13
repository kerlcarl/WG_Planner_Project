from nicegui import ui

from models import Expense, MitbewohnerDB, Session, Task, engine, Base


# Session-Factory (SQLAlchemy) wird in models.py initialisiert.
# Für jeden Request eine neue Session erstellen
def get_session():
    return Session()

# 2. Logik-Klasse (Anwendungslogik / OOP)
def calculate_balances() -> dict[int, float]:
    """Berechnet den Saldo (Zahlung minus Anteil) pro Nutzer."""

    session = get_session()
    users = session.query(MitbewohnerDB).all()
    balances = {u.id: 0.0 for u in users}

    for expense in session.query(Expense).all():
        share = expense.split_per_person()
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
def render_users_tab():
    session = get_session()
    with ui.column().classes('w-full h-full overflow-auto'):
        with ui.row().classes('w-full gap-4 p-6'):
            # Form für neuen Mitbewohner
            with ui.card().classes('flex-grow bg-white shadow-md rounded-lg'):
                ui.label('➕ Neuen Mitbewohner hinzufügen').classes('text-h6 font-bold text-blue-700')
                ui.separator().classes('my-3')
                name_input = ui.input(label='Name', placeholder='z. B. Anna').classes('w-full')
                color_input = ui.input(label='Kennfarbe (Hex)', placeholder='#00aaff').classes('w-full')
                ui.button('Hinzufügen', on_click=lambda: add_user(name_input.value, color_input.value)).classes('w-full bg-blue-500 text-white font-bold py-2 rounded-lg hover:bg-blue-600')

            # Liste der Bewohner
            with ui.card().classes('flex-grow bg-white shadow-md rounded-lg'):
                ui.label('👥 Aktuelle Bewohner*innen').classes('text-h6 font-bold text-blue-700')
                ui.separator().classes('my-3')
                users = session.query(MitbewohnerDB).order_by(MitbewohnerDB.name)
                if users.count() == 0:
                    ui.label('Noch keine Bewohner*innen hinzugefügt.').classes('text-gray-500 italic')
                else:
                    for user in users:
                        with ui.card().classes('w-full bg-gradient to-r from-blue-50 to-indigo-50 border-l-4 border-blue-500 mb-2'):
                            with ui.row().classes('w-full items-center justify-between p-3'):
                                with ui.column():
                                    ui.label(f'👤 {user.name}').classes('text-h6 font-bold')
                                    if user.color:
                                        ui.label(f'🎨 Farbe: {user.color}').classes('text-caption text-gray-600')
                                with ui.row().classes('gap-2'):
                                    ui.button('✏️ Bearbeiten', on_click=lambda u=user: edit_user(u)).classes('bg-indigo-500 text-white')
                                    ui.button('🗑️ Löschen', on_click=lambda u=user: delete_user(u)).classes('bg-red-500 text-white')
    session.close()


def add_user(name: str, color: str | None = None) -> None:
    if not name:
        ui.notify('Bitte einen Namen eingeben.', color='warning')
        return

    session = get_session()
    new_user = MitbewohnerDB(name=name.strip(), color=color.strip() if color else None)
    session.add(new_user)
    session.commit()
    session.close()
    ui.notify(f'{name} wurde hinzugefügt!')
    ui.reload()


def edit_user(user: MitbewohnerDB):
    with ui.dialog() as dialog:
        ui.label(f'Bearbeite {user.name}').classes('text-h6')
        name_input = ui.input(label='Name', value=user.name)
        color_input = ui.input(label='Kennfarbe (Hex)', value=user.color or '')
        with ui.row():
            ui.button('Speichern', on_click=lambda: save_edit(user, name_input.value, color_input.value, dialog))
            ui.button('Abbrechen', on_click=dialog.close)
    dialog.open()


def save_edit(user: MitbewohnerDB, name: str, color: str, dialog):
    if not name:
        ui.notify('Name erforderlich.', color='warning')
        return
    session = get_session()
    user.name = name.strip()
    user.color = color.strip() if color else None
    session.merge(user)
    session.commit()
    session.close()
    ui.notify('Gespeichert!')
    dialog.close()
    ui.reload()


def delete_user(user: MitbewohnerDB):
    session = get_session()
    session.delete(user)
    session.commit()
    session.close()
    ui.notify(f'{user.name} wurde gelöscht!')
    ui.reload()


def render_finances_tab():
    session = get_session()
    with ui.column().classes('w-full h-full overflow-auto'):
        with ui.row().classes('w-full gap-4 p-6'):
            # Form für neue Ausgabe
            with ui.card().classes('flex-grow bg-white shadow-md rounded-lg'):
                ui.label('➕ Neue Ausgabe erfassen').classes('text-h6 font-bold text-green-700')
                ui.separator().classes('my-3')
                desc_input = ui.input(label='Beschreibung', placeholder='z. B. Lebensmittel').classes('w-full')
                amount_input = ui.number(label='Betrag (CHF)').classes('w-full')
                category_input = ui.input(label='Kategorie', placeholder='z. B. Lebensmittel').classes('w-full')
                paid_by_select = ui.select({u.name: u.id for u in session.query(MitbewohnerDB)}, label='Bezahlt von').classes('w-full')
                participants_multi = ui.select(
                    {u.name: u.id for u in session.query(MitbewohnerDB)},
                    label='Beteiligt',
                    multiple=True
                ).classes('w-full')
                ui.button('💾 Speichern', on_click=lambda: add_expense(desc_input.value, amount_input.value, category_input.value, paid_by_select.value, participants_multi.value)).classes('w-full bg-green-500 text-white font-bold py-2 rounded-lg hover:bg-green-600')

            # Saldo-Übersicht
            with ui.card().classes('flex-grow bg-white shadow-md rounded-lg'):
                ui.label('💵 Saldo pro Person').classes('text-h6 font-bold text-green-700')
                ui.separator().classes('my-3')
                balances = calculate_balances()
                users = session.query(MitbewohnerDB).order_by(MitbewohnerDB.name)
                if users.count() == 0:
                    ui.label('Noch keine Mitbewohner*innen hinzugefügt.').classes('text-gray-500 italic')
                else:
                    for user in users:
                        amount = balances.get(user.id, 0.0)
                        color_class = 'bg-green-50' if amount > 0 else 'bg-red-50'
                        with ui.card().classes(f'w-full {color_class} border-l-4 border-green-500 mb-2'):
                            with ui.row().classes('w-full items-center justify-between p-3'):
                                ui.label(f'👤 {user.name}').classes('text-h6 font-bold')
                                ui.label(f'CHF {amount:0.2f}').classes('text-h6 font-bold text-green-700')
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
    with ui.column().classes('w-full h-full overflow-auto'):
        with ui.row().classes('w-full gap-4 p-6'):
            # Form für neue Aufgabe
            with ui.card().classes('flex-grow bg-white shadow-md rounded-lg'):
                ui.label('➕ Neue Aufgabe erstellen').classes('text-h6 font-bold text-orange-700')
                ui.separator().classes('my-3')
                title_input = ui.input(label='Titel', placeholder='z. B. Putzen').classes('w-full')
                desc_input = ui.input(label='Beschreibung', placeholder='Optional').classes('w-full')
                assigned_select = ui.select({u.name: u.id for u in session.query(MitbewohnerDB)}, label='Zugewiesen an').classes('w-full')
                ui.button('✅ Erstellen', on_click=lambda: add_task(title_input.value, desc_input.value, assigned_select.value)).classes('w-full bg-orange-500 text-white font-bold py-2 rounded-lg hover:bg-orange-600')

            # Aufgaben-Liste
            with ui.card().classes('flex-grow bg-white shadow-md rounded-lg'):
                ui.label('📋 Aktuelle Aufgaben').classes('text-h6 font-bold text-orange-700')
                ui.separator().classes('my-3')
                tasks = session.query(Task).order_by(Task.id)
                if tasks.count() == 0:
                    ui.label('Noch keine Aufgaben hinzugefügt.').classes('text-gray-500 italic')
                else:
                    for task in tasks:
                        status_class = 'bg-green-100 line-through' if task.is_done else 'bg-yellow-100'
                        with ui.card().classes(f'w-full {status_class} border-l-4 border-orange-500 mb-2'):
                            with ui.row().classes('w-full items-center justify-between p-3'):
                                ui.checkbox(value=task.is_done, on_change=lambda checked, t=task: toggle_task_done(t, checked))
                                with ui.column().classes('flex-grow'):
                                    ui.label(f'📝 {task.title}').classes('text-h6 font-bold')
                                    ui.label(f'👤 {task.assigned_to.name if task.assigned_to else "Niemand"}').classes('text-caption text-gray-600')
                with ui.row().classes('w-full p-3 border-t'):
                    ui.button('🔄 Aufgaben rotieren', on_click=lambda: (rotate_tasks(), ui.reload())).classes('bg-purple-500 text-white font-bold rounded-lg hover:bg-purple-600')
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
    with ui.column().classes('w-full h-screen bg-gradient to-r from-blue-50 to-indigo-50'):
        # Header
        with ui.row().classes('w-full bg-gradient to-r from-blue-500 to-indigo-600 text-white shadow-lg p-6 items-center'):
            ui.label('🏠 WG‑Planner').classes('text-h4 font-bold flex-grow')
            ui.label('Finanzen & Aufgaben verwalten').classes('text-caption')
        
        # Tabs
        with ui.row().classes('w-full'):
            with ui.column().classes('w-full'):
                with ui.tabs().classes('w-full') as tabs:
                    ui.tab('👥 Mitbewohner*innen', icon='group')
                    ui.tab('💰 Finanzen', icon='attach_money')
                    ui.tab('✅ Ämtli', icon='checklist')

                with ui.tab_panels(tabs, value='👥 Mitbewohner*innen').classes('w-full'):
                    with ui.tab_panel('👥 Mitbewohner*innen').classes('w-full'):
                        render_users_tab()
                    with ui.tab_panel('💰 Finanzen').classes('w-full'):
                        render_finances_tab()
                    with ui.tab_panel('✅ Ämtli').classes('w-full'):
                        render_tasks_tab()

# Startet die Anwendung
# `show=False` verhindert, dass NiceGUI versucht, einen Browser zu öffnen.
ui.run(title='WG Planner', port=8080, show=False, show_welcome_message=False)