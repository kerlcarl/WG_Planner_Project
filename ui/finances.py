# Darstellung des Tabs für Finanzen.
from nicegui import ui

from models import Expense, MitbewohnerDB
from services import calculate_balances, calculate_settlements, get_session, save_expense


def render_finances_tab(container):
    def refresh():
        container.clear()
        session = get_session()
        balances = calculate_balances()
        settlements = calculate_settlements()
        users = session.query(MitbewohnerDB).order_by(MitbewohnerDB.name).all()
        expenses = session.query(Expense).order_by(Expense.id.desc()).all()
        user_names = {user.id: user.name for user in users}

        with container:
            with ui.expansion("Neue Ausgabe erfassen", icon="add_shopping_cart", value=True).classes(
                "w-full bg-green-50 mb-4 shadow-sm rounded-xl"
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
                ui.button("Speichern", on_click=handle_save).classes("bg-green-600 text-white w-full mt-3")

            with ui.card().classes("w-full mb-4 shadow-md rounded-xl bg-white"):
                with ui.row().classes("w-full items-center justify-between px-4 pt-4"):
                    with ui.column().classes("gap-0"):
                        ui.label("Kontostände").classes("text-h6 font-bold")
                        ui.label("Positive Werte bedeuten Guthaben, negative Werte offene Schulden.").classes(
                            "text-sm text-gray-500"
                        )

                with ui.column().classes("w-full gap-2 p-4 pt-3"):
                    for user in users:
                        balance = balances.get(user.id, 0.0)
                        is_positive = balance >= 0
                        color = "text-green-700" if is_positive else "text-red-700"
                        badge = "Guthaben" if is_positive else "Offen"
                        badge_classes = "bg-green-100 text-green-700" if is_positive else "bg-red-100 text-red-700"
                        with ui.card().classes("w-full border border-gray-100 shadow-sm rounded-lg"):
                            with ui.row().classes("w-full items-center justify-between p-3"):
                                with ui.column().classes("gap-0"):
                                    ui.label(user.name).classes("text-bold text-base")
                                    ui.label(badge).classes(
                                        f"text-xs px-2 py-1 rounded-full w-fit font-medium {badge_classes}"
                                    )
                                ui.label(f"CHF {balance:.2f}").classes(f"text-xl font-bold {color}")

            with ui.card().classes("w-full mb-4 shadow-md rounded-xl bg-gradient-to-br from-indigo-50 to-white"):
                with ui.row().classes("w-full items-center justify-between px-4 pt-4"):
                    with ui.column().classes("gap-0"):
                        ui.label("Ausgleichsvorschläge").classes("text-h6 font-bold text-indigo-900")
                        ui.label("Diese Überweisungen gleichen alle Kontostände wieder auf 0 aus.").classes(
                            "text-sm text-indigo-700"
                        )

                if settlements:
                    with ui.column().classes("w-full gap-3 p-4 pt-3"):
                        for settlement in settlements:
                            from_name = user_names.get(settlement["from_user_id"], "Unbekannt")
                            to_name = user_names.get(settlement["to_user_id"], "Unbekannt")
                            with ui.card().classes("w-full bg-white border border-indigo-100 shadow-sm rounded-lg"):
                                with ui.row().classes("w-full items-center justify-between p-4"):
                                    with ui.row().classes("items-center gap-3"):
                                        ui.icon("south_east").classes("text-red-500")
                                        with ui.column().classes("gap-0"):
                                            ui.label(from_name).classes("text-sm text-gray-500")
                                            ui.label("überweist").classes("text-xs uppercase tracking-wide text-gray-400")
                                    ui.icon("arrow_forward").classes("text-indigo-400")
                                    with ui.row().classes("items-center gap-3"):
                                        with ui.column().classes("items-end gap-0"):
                                            ui.label(to_name).classes("text-sm text-gray-500")
                                            ui.label("erhält").classes("text-xs uppercase tracking-wide text-gray-400")
                                        ui.icon("north_east").classes("text-green-600")
                                    ui.label(f"CHF {settlement['amount']:.2f}").classes(
                                        "text-lg font-bold text-indigo-700 min-w-[110px] text-right"
                                    )
                else:
                    with ui.card().classes("m-4 mt-3 bg-green-50 border border-green-200 shadow-sm rounded-lg"):
                        with ui.row().classes("items-center gap-3 p-4"):
                            ui.icon("check_circle").classes("text-2xl text-green-600")
                            with ui.column().classes("gap-0"):
                                ui.label("Alles ausgeglichen").classes("text-base font-bold text-green-800")
                                ui.label("Keine Ausgleichszahlungen nötig.").classes("text-sm text-green-700")

            with ui.card().classes("w-full shadow-md rounded-xl bg-white"):
                with ui.row().classes("w-full items-center justify-between px-4 pt-4"):
                    with ui.column().classes("gap-0"):
                        ui.label("Ausgabenverlauf").classes("text-h6 font-bold")
                        ui.label("Alle bisher erfassten gemeinsamen Ausgaben.").classes("text-sm text-gray-500")

                with ui.column().classes("w-full gap-2 p-4 pt-3"):
                    for expense in expenses:
                        with ui.card().classes("w-full border border-gray-100 shadow-sm rounded-lg"):
                            with ui.row().classes("w-full justify-between items-center p-3"):
                                with ui.column():
                                    ui.label(expense.description).classes("text-bold")
                                    ui.label(
                                        f"Kategorie: {expense.category or 'Allgemein'}"
                                    ).classes("text-xs text-gray-500")
                                with ui.column().classes("items-end"):
                                    ui.label(f"CHF {expense.amount:.2f}").classes("text-bold text-lg")
                                    ui.label(
                                        f"Bezahlt von {expense.paid_by.name if expense.paid_by else 'Unbekannt'}"
                                    ).classes("text-xs text-gray-500")
                            ui.separator().classes("mx-3")
                            ui.label(
                                f"Beteiligt: {', '.join(participant.name for participant in expense.participants)}"
                            ).classes("px-3 pb-3 pt-2 text-xs italic text-gray-600")

        session.close()

    refresh()
