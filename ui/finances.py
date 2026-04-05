# Darstellung des Tabs fuer Finanzen.
from nicegui import ui

from models import Expense, MitbewohnerDB
from services import calculate_balances, get_session, save_expense


def render_finances_tab(container):
    def refresh():
        container.clear()
        session = get_session()
        balances = calculate_balances()
        users = session.query(MitbewohnerDB).order_by(MitbewohnerDB.name).all()
        expenses = session.query(Expense).order_by(Expense.id.desc()).all()

        with container:
            with ui.expansion("Neue Ausgabe erfassen", icon="add_shopping_cart").classes(
                "w-full bg-green-50 mb-4 shadow-sm"
            ):
                desc = ui.input("Beschreibung")
                amt = ui.number("Betrag (CHF)", format="%.2f")
                cat = ui.input("Kategorie")
                ui.label("Bezahlt von").classes("text-sm text-gray-700")
                with ui.column().classes("gap-1 ml-1"):
                    payer = ui.radio({user.id: user.name for user in users})
                ui.label("Beteiligte Mitbewohner*innen").classes("text-sm text-gray-700")
                with ui.column().classes("gap-1 ml-1"):
                    selected_parts_checkboxes = {
                        user.id: ui.checkbox(user.name) for user in users
                    }

                class _PartsGroup:
                    def __init__(self, checkboxes):
                        self._checkboxes = checkboxes

                    @property
                    def value(self):
                        return [user_id for user_id, checkbox in self._checkboxes.items() if checkbox.value]

                parts = _PartsGroup(selected_parts_checkboxes)

                def handle_save():
                    save_expense(desc, amt, cat, payer, parts, refresh)

                desc.on("keydown.enter", handle_save)
                ui.button("Speichern", on_click=handle_save).classes("bg-green-600 text-white w-full mt-2")

            ui.label("Kontostaende").classes("text-h6 font-bold mb-2")
            for user in users:
                balance = balances.get(user.id, 0.0)
                color = "text-green-700" if balance >= 0 else "text-red-700"
                with ui.card().classes("w-full mb-2 shadow-sm border-l-4 border-green-500"):
                    with ui.row().classes("w-full justify-between items-center p-2"):
                        ui.label(user.name).classes("text-bold")
                        ui.label(f"CHF {balance:.2f}").classes(f"text-bold {color}")

            ui.label("Ausgabenverlauf").classes("text-h6 font-bold mt-6 mb-2")
            for expense in expenses:
                with ui.card().classes("w-full p-3 bg-white mb-2 shadow-sm"):
                    with ui.row().classes("w-full justify-between items-center"):
                        with ui.column():
                            ui.label(expense.description).classes("text-bold")
                            ui.label(
                                f"Kategorie: {expense.category or 'Allgemein'}"
                            ).classes("text-xs text-gray-500")
                        with ui.column().classes("items-end"):
                            ui.label(f"CHF {expense.amount:.2f}").classes("text-bold")
                            ui.label(
                                f"Bezahlt von {expense.paid_by.name if expense.paid_by else 'Unbekannt'}"
                            ).classes("text-xs")
                    ui.separator().classes("my-1")
                    ui.label(
                        f"Beteiligt: {', '.join(participant.name for participant in expense.participants)}"
                    ).classes("text-xs italic")

        session.close()

    refresh()
