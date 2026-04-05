# Gemeinsame Anwendungslogik und CRUD-Funktionen fuer die UI.
from nicegui import ui

from models import Expense, MitbewohnerDB, Session, Task


def get_session():
    return Session()


def calculate_balances() -> dict[int, float]:
    session = get_session()
    users = session.query(MitbewohnerDB).all()
    balances = {user.id: 0.0 for user in users}

    for expense in session.query(Expense).all():
        share = expense.calculate_share()
        for user in expense.participants:
            balances[user.id] -= share
        balances[expense.paid_by_id] += expense.amount

    session.close()
    return balances


def add_user(input_field, callback):
    session = get_session()
    session.add(MitbewohnerDB(name=input_field.value.strip()))
    session.commit()
    session.close()
    input_field.value = ""
    ui.notify("Mitbewohner*in hinzugefuegt", color="positive")
    callback()


def save_expense(desc, amt, cat, payer, parts, callback):
    if not desc.value or not amt.value or not payer.value:
        ui.notify("Bitte alle Pflichtfelder ausfuellen", color="warning")
        return

    session = get_session()
    expense = Expense(
        description=desc.value,
        amount=amt.value,
        category=cat.value,
        paid_by_id=payer.value,
    )

    if parts.value:
        for participant_id in parts.value:
            user = session.get(MitbewohnerDB, participant_id)
            if user:
                expense.participants.append(user)

    session.add(expense)
    session.commit()
    session.close()
    ui.notify("Ausgabe erfolgreich gespeichert", color="positive")
    callback()


def save_task(title, who, callback):
    if not title.value:
        return

    session = get_session()
    session.add(Task(title=title.value, assigned_to_id=who.value))
    session.commit()
    session.close()
    ui.notify("Neues Aemtli erstellt", color="positive")
    callback()


def update_task_status(task, value, callback):
    session = get_session()
    task.is_done = value
    session.merge(task)
    session.commit()
    session.close()
    callback()


def delete_user(user, callback):
    session = get_session()
    user_to_delete = session.get(MitbewohnerDB, user.id)
    if user_to_delete:
        session.delete(user_to_delete)
        session.commit()
    session.close()
    ui.notify("Eintrag geloescht", color="negative")
    callback()


def edit_user(user, callback):
    with ui.dialog() as dialog, ui.card():
        ui.label(f"Bearbeite {user.name}").classes("text-h6")
        name_input = ui.input(value=user.name)
        with ui.row():
            ui.button(
                "Speichern",
                on_click=lambda: (save_user_edit(user.id, name_input.value, dialog), callback()),
            )
            ui.button("Abbrechen", on_click=dialog.close).props("flat")
    dialog.open()


def save_user_edit(user_id, new_name, dialog):
    session = get_session()
    user = session.get(MitbewohnerDB, user_id)
    if user:
        user.name = new_name
    session.commit()
    session.close()
    dialog.close()
