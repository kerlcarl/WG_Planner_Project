# Gemeinsame Anwendungslogik und CRUD-Funktionen fuer die UI.
from nicegui import ui

from models import Expense, MitbewohnerDB, Session, Task

DEFAULT_EXPENSE_CATEGORIES = [
    "Lebensmittel",
    "Haushalt",
    "Miete",
    "Internet",
    "Strom",
    "Putzmittel",
    "Freizeit",
    "Sonstiges",
]


# Liefert fuer jeden Aufruf eine frische SQLAlchemy-Session.
def get_session():
    return Session()


# Berechnet den Kontostand pro Benutzer aus allen Ausgaben.
def calculate_balances() -> dict[int, float]:
    session = get_session()
    users = session.query(MitbewohnerDB).all()
    balances = {user.id: 0.0 for user in users}

    for expense in session.query(Expense).all():
        # Anteil fuer jeden Teilnehmer abziehen, Gesamtbetrag beim Zahler gutschreiben.
        share = expense.calculate_share()
        for user in expense.participants:
            balances[user.id] -= share
        balances[expense.paid_by_id] += expense.amount

    session.close()
    return balances


# Erstellt konkrete Ausgleichszahlungen aus den berechneten Salden.
def calculate_settlements() -> list[dict[str, float | int]]:
    balances = calculate_balances()
    settlements: list[dict[str, float | int]] = []

    creditors = [
        {"user_id": user_id, "amount": round(amount, 2)}
        for user_id, amount in balances.items()
        if amount > 0.01
    ]
    debtors = [
        {"user_id": user_id, "amount": round(-amount, 2)}
        for user_id, amount in balances.items()
        if amount < -0.01
    ]

    creditor_index = 0
    debtor_index = 0

    while creditor_index < len(creditors) and debtor_index < len(debtors):
        creditor = creditors[creditor_index]
        debtor = debtors[debtor_index]
        transfer_amount = round(min(creditor["amount"], debtor["amount"]), 2)

        # Nur sinnvolle (nicht triviale) Transfers speichern.
        if transfer_amount > 0.01:
            settlements.append(
                {
                    "from_user_id": debtor["user_id"],
                    "to_user_id": creditor["user_id"],
                    "amount": transfer_amount,
                }
            )

        creditor["amount"] = round(creditor["amount"] - transfer_amount, 2)
        debtor["amount"] = round(debtor["amount"] - transfer_amount, 2)

        if creditor["amount"] <= 0.01:
            creditor_index += 1
        if debtor["amount"] <= 0.01:
            debtor_index += 1

    return settlements


# Summiert Ausgaben je Kategorie fuer die Statistik-Kacheln.
def calculate_category_totals() -> list[dict[str, float]]:
    session = get_session()
    totals: dict[str, float] = {}

    for expense in session.query(Expense).all():
        category = expense.category or "Sonstiges"
        totals[category] = totals.get(category, 0.0) + expense.amount

    session.close()

    return [
        {"category": category, "amount": round(amount, 2)}
        for category, amount in sorted(totals.items(), key=lambda item: item[1], reverse=True)
    ]


# Legt einen neuen Benutzer an und informiert die UI.
def add_user(input_field, callback):
    session = get_session()
    session.add(MitbewohnerDB(name=input_field.value.strip()))
    session.commit()
    session.close()
    input_field.value = ""
    ui.notify("Mitbewohner*in hinzugefuegt", color="positive")
    callback()


# Legt eine neue Ausgabe mit Teilnehmern an.
def save_expense(desc, amt, cat, payer, parts, callback):
    if not desc.value or not amt.value or not payer.value or not cat.value:
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
        # Viele-zu-viele Verknuepfung ueber expense.participants.
        for participant_id in parts.value:
            user = session.get(MitbewohnerDB, participant_id)
            if user:
                expense.participants.append(user)

    session.add(expense)
    session.commit()
    session.close()
    ui.notify("Ausgabe erfolgreich gespeichert", color="positive")
    callback()


# Entfernt eine Ausgabe dauerhaft aus der Datenbank.
def delete_expense(expense, callback):
    session = get_session()
    expense_to_delete = session.get(Expense, expense.id)
    if expense_to_delete:
        session.delete(expense_to_delete)
        session.commit()
    session.close()
    ui.notify("Ausgabe geloescht", color="negative")
    callback()


# Legt ein neues Aemtli an.
def save_task(title, who, callback):
    if not title.value:
        return

    session = get_session()
    session.add(Task(title=title.value, assigned_to_id=who.value))
    session.commit()
    session.close()
    ui.notify("Neues Aemtli erstellt", color="positive")
    callback()


# Markiert eine Aufgabe als erledigt/nicht erledigt.
def update_task_status(task, value, callback):
    session = get_session()
    task.is_done = value
    session.merge(task)
    session.commit()
    session.close()
    callback()


# Loescht einen Benutzer.
def delete_user(user, callback):
    session = get_session()
    user_to_delete = session.get(MitbewohnerDB, user.id)
    if user_to_delete:
        session.delete(user_to_delete)
        session.commit()
    session.close()
    ui.notify("Eintrag geloescht", color="negative")
    callback()


# Oeffnet den Bearbeiten-Dialog fuer einen Benutzer.
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


# Speichert den geaenderten Benutzernamen.
def save_user_edit(user_id, new_name, dialog):
    session = get_session()
    user = session.get(MitbewohnerDB, user_id)
    if user:
        user.name = new_name
    session.commit()
    session.close()
    dialog.close()
