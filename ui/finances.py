# Darstellung des Tabs für Finanzen.
from nicegui import ui

from models import Expense, MitbewohnerDB
from services import (
    DEFAULT_EXPENSE_CATEGORIES,
    calculate_balances,
    calculate_category_totals,
    calculate_settlements,
    delete_expense,
    get_session,
    save_expense,
)


def render_finances_tab(container):
    def refresh():
        container.clear()
        session = get_session()
        balances = calculate_balances()
        category_totals = calculate_category_totals()
        settlements = calculate_settlements()
        users = session.query(MitbewohnerDB).order_by(MitbewohnerDB.name).all()
        expenses = session.query(Expense).order_by(Expense.id.desc()).all()
        user_names = {user.id: user.name for user in users}

        with container:
            with ui.card().classes("w-full mb-4 shadow-md rounded-xl bg-white"):
                with ui.row().classes("w-full items-center justify-between gap-4 p-5"):
                    with ui.column().classes("gap-0"):
                        ui.label("Ausgaben verwalten").classes("text-h6 font-bold text-green-900")
                        ui.label("Neue gemeinsame Ausgaben lassen sich über einen Dialog erfassen.").classes(
                            "text-sm text-green-800"
                        )
                    ui.button("Neue Ausgabe", icon="add", on_click=lambda: expense_dialog.open()).classes(
                        "bg-green-600 text-white px-4"
                    )

            with ui.dialog() as expense_dialog, ui.card().classes("w-[42rem] max-w-[95vw] rounded-2xl shadow-xl"):
                with ui.row().classes("w-full items-center justify-between p-5 pb-2"):
                    with ui.column().classes("gap-0"):
                        ui.label("Neue Ausgabe erfassen").classes("text-h6 font-bold text-slate-900")
                        ui.label("Betrag, zahlende Person und beteiligte Mitbewohner*innen festlegen.").classes(
                            "text-sm text-slate-500"
                        )
                    ui.button(icon="close", on_click=expense_dialog.close).props("flat round")

                with ui.column().classes("w-full gap-4 px-5 pb-5 pt-3"):
                    desc = ui.input("Beschreibung").classes("w-full")
                    with ui.row().classes("w-full gap-4"):
                        amt = ui.number("Betrag (CHF)", format="%.2f").classes("w-full")
                        cat_select = ui.select(
                            options=DEFAULT_EXPENSE_CATEGORIES + ["Andere..."],
                            label="Kategorie",
                            value="Lebensmittel",
                        ).classes("w-full")

                    custom_category = ui.input("Eigene Kategorie").classes("w-full")
                    custom_category.bind_visibility_from(cat_select, "value", lambda value: value == "Andere...")

                    with ui.card().classes("w-full bg-slate-50 border border-slate-200 rounded-xl shadow-none"):
                        with ui.column().classes("w-full gap-3 p-4"):
                            ui.label("Bezahlt von").classes("text-sm font-medium text-slate-700")
                            payer = ui.radio({user.id: user.name for user in users}).classes("w-full")

                    with ui.card().classes("w-full bg-slate-50 border border-slate-200 rounded-xl shadow-none"):
                        with ui.column().classes("w-full gap-3 p-4"):
                            ui.label("Beteiligte Mitbewohner*innen").classes("text-sm font-medium text-slate-700")
                            with ui.column().classes("gap-2"):
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

                    class _CategoryField:
                        @property
                        def value(self):
                            if cat_select.value == "Andere...":
                                return custom_category.value.strip()
                            return cat_select.value

                    category_field = _CategoryField()

                    def handle_save():
                        def refresh_and_close():
                            expense_dialog.close()
                            refresh()

                        save_expense(desc, amt, category_field, payer, parts, refresh_and_close)

                    desc.on("keydown.enter", handle_save)
                    with ui.row().classes("w-full justify-end gap-2 pt-2"):
                        ui.button("Abbrechen", on_click=expense_dialog.close).props("flat")
                        ui.button("Speichern", on_click=handle_save).classes("bg-green-600 text-white")

            with ui.row().classes("w-full items-stretch gap-4 mb-4 no-wrap").style("flex-wrap: nowrap; align-items: stretch;"):
                with ui.card().classes("shadow-md rounded-xl bg-white").style("flex: 1 1 0; min-width: 0;"):
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
                            with ui.row().classes("w-full items-center justify-between rounded-lg border border-gray-100 bg-white px-3 py-2 shadow-sm"):
                                with ui.column().classes("gap-0"):
                                    ui.label(user.name).classes("text-sm font-bold text-slate-900")
                                    ui.label(badge).classes(
                                        f"text-xs px-2 py-0.5 rounded-full w-fit font-medium {badge_classes}"
                                    )
                                ui.label(f"CHF {balance:.2f}").classes(f"text-lg font-bold {color}")

                with ui.card().classes("shadow-md rounded-xl bg-white").style("flex: 1 1 0; min-width: 0;"):
                    with ui.row().classes("w-full items-center justify-between gap-4 p-5"):
                        with ui.column().classes("gap-0"):
                            ui.label("Neue Ausgabe").classes("text-h6 font-bold text-green-900")
                            ui.label("Neue gemeinsame Ausgaben über den Dialog erfassen.").classes(
                                "text-sm text-green-800"
                            )
                        ui.button("Erfassen", icon="add", on_click=lambda: expense_dialog.open()).classes(
                            "bg-green-600 text-white px-4"
                        )

                    with ui.column().classes("px-5 pb-5 gap-3"):
                        ui.label("Verfügbare Kategorien").classes("text-sm font-medium text-slate-700")
                        with ui.row().classes("w-full gap-2"):
                            for category in DEFAULT_EXPENSE_CATEGORIES[:4]:
                                ui.label(category).classes("text-xs px-2 py-1 rounded-full bg-white text-slate-600 shadow-sm")
                        with ui.row().classes("w-full gap-2"):
                            for category in DEFAULT_EXPENSE_CATEGORIES[4:]:
                                ui.label(category).classes("text-xs px-2 py-1 rounded-full bg-white text-slate-600 shadow-sm")

                with ui.card().classes("shadow-md rounded-xl bg-white").style("flex: 1 1 0; min-width: 0;"):
                    with ui.row().classes("w-full items-center justify-between px-4 pt-4"):
                        with ui.column().classes("gap-0"):
                            ui.label("Ausgaben nach Kategorie").classes("text-h6 font-bold")
                            ui.label("So siehst du schnell, welche Bereiche am meisten kosten.").classes(
                                "text-sm text-gray-500"
                            )

                    with ui.column().classes("w-full gap-2 p-4 pt-3"):
                        if category_totals:
                            highest_total = category_totals[0]["amount"]
                            for item in category_totals:
                                width_percent = 100 if highest_total <= 0 else max(
                                    12, int((item["amount"] / highest_total) * 100)
                                )
                                with ui.card().classes("w-full border border-gray-100 shadow-sm rounded-lg"):
                                    with ui.row().classes("w-full items-center justify-between p-3 pb-2"):
                                        ui.label(item["category"]).classes("text-base font-bold text-slate-900")
                                        ui.label(f"CHF {item['amount']:.2f}").classes(
                                            "text-base font-bold text-emerald-700"
                                        )
                                    with ui.element("div").classes("w-full px-3 pb-3"):
                                        ui.element("div").classes("h-2.5 w-full rounded-full bg-slate-100")
                                        ui.element("div").classes(
                                            "h-2.5 -mt-2.5 rounded-full bg-emerald-500 transition-all"
                                        ).style(f"width: {width_percent}%")
                        else:
                            ui.label("Noch keine Kategorien vorhanden.").classes("text-gray-500 italic p-2")

            with ui.card().classes("w-full mb-4 shadow-md rounded-xl bg-white"):
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
                                ui.button(
                                    icon="delete",
                                    on_click=lambda current_expense=expense: delete_expense(current_expense, refresh),
                                ).props("flat round color=red")
                            ui.separator().classes("mx-3")
                            ui.label(
                                f"Beteiligt: {', '.join(participant.name for participant in expense.participants)}"
                            ).classes("px-3 pb-3 pt-2 text-xs italic text-gray-600")

        session.close()

    refresh()
    return refresh
