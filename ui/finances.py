from nicegui import ui

from models import Expense, ManualDebt, MitbewohnerDB
from services import (
    DEFAULT_EXPENSE_CATEGORIES,
    calculate_balances,
    calculate_category_totals,
    calculate_settlements,
    create_manual_debt,
    delete_expense,
    delete_manual_debts_by_pair,
    get_session,
    save_expense,
    save_settlement,
)

_PAYMENT_METHODS = ["Twint", "Bargeld", "Banküberweisung"]


# Rendert den Finanz-Tab und liefert eine Refresh-Funktion fuer Neuaufbau.
def render_finances_tab(container, current_user_id: int = None):
    # Liest aktuelle Daten, berechnet Kennzahlen und baut alle UI-Karten neu.
    def refresh():
        container.clear()
        session = get_session()
        # Abgeleitete Werte werden zur Laufzeit berechnet (nicht separat gespeichert).
        balances = calculate_balances()
        category_totals = calculate_category_totals()
        settlements = calculate_settlements()
        users = session.query(MitbewohnerDB).order_by(MitbewohnerDB.name).all()
        expenses = session.query(Expense).order_by(Expense.id.desc()).all()
        user_names = {user.id: user.name for user in users}
        manual_debts = session.query(ManualDebt).order_by(ManualDebt.created_at.desc()).all()
        total_spent = sum(e.amount for e in expenses)
        expense_count = len(expenses)

        with container:
            # ── Hero-Banner ───────────────────────────────────────────────────
            with ui.element("div").style(
                "background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 60%, #6ee7b7 100%); "
                "border-radius: 20px; padding: 28px 32px; margin-bottom: 20px; "
                "box-shadow: 0 4px 20px rgba(16,185,129,0.18)"
            ):
                with ui.row().classes("w-full items-center justify-between flex-wrap gap-4"):
                    with ui.row().classes("items-center gap-4"):
                        with ui.element("div").style(
                            "background: #059669; border-radius: 16px; width: 56px; height: 56px; "
                            "display: flex; align-items: center; justify-content: center; flex-shrink: 0"
                        ):
                            ui.icon("payments").style("color: white; font-size: 2rem")
                        with ui.column().classes("gap-0"):
                            ui.label("Finanzen & Ausgaben").style(
                                "font-size: 1.4rem; font-weight: 800; color: #065f46; line-height: 1.2"
                            )
                            ui.label("Gemeinsame Kosten transparent verwalten").style(
                                "color: #059669; font-size: 0.85rem; margin-top: 4px"
                            )
                    with ui.row().classes("gap-8"):
                        with ui.column().classes("items-end gap-0"):
                            ui.label(f"CHF {total_spent:.2f}").style(
                                "font-size: 1.9rem; font-weight: 900; color: #065f46; line-height: 1"
                            )
                            ui.label("Gesamt ausgegeben").style(
                                "color: #059669; font-size: 0.78rem; margin-top: 2px"
                            )
                        with ui.column().classes("items-end gap-0"):
                            ui.label(str(expense_count)).style(
                                "font-size: 1.9rem; font-weight: 900; color: #065f46; line-height: 1"
                            )
                            ui.label("Ausgaben erfasst").style(
                                "color: #059669; font-size: 0.78rem; margin-top: 2px"
                            )
                ui.button(
                    "+ Neue Ausgabe erfassen",
                    on_click=lambda: expense_dialog.open(),
                ).style(
                    "background: #059669; color: white; border-radius: 12px; "
                    "font-weight: 700; margin-top: 16px; padding: 10px 20px; width: 100%"
                )

            # ── Ausgabe-Erfassen-Dialog ───────────────────────────────────────
            with ui.dialog() as expense_dialog, ui.card().classes(
                "w-[42rem] max-w-[95vw] rounded-2xl shadow-xl"
            ):
                with ui.row().classes("w-full items-center justify-between p-5 pb-2"):
                    with ui.column().classes("gap-0"):
                        ui.label("Neue Ausgabe erfassen").classes("text-h6 font-bold text-slate-900")
                        ui.label(
                            "Betrag, zahlende Person und beteiligte Mitbewohner*innen festlegen."
                        ).classes("text-sm text-slate-500")
                    ui.button(icon="close", on_click=expense_dialog.close).props("flat round")

                with ui.column().classes("w-full gap-4 px-5 pb-5 pt-3"):
                    # Formfelder fuer neue Ausgabe.
                    desc = ui.input("Beschreibung").classes("w-full")
                    with ui.row().classes("w-full gap-4"):
                        amt = ui.number("Betrag (CHF)", format="%.2f").classes("w-full")
                        cat_select = ui.select(
                            options=DEFAULT_EXPENSE_CATEGORIES + ["Andere..."],
                            label="Kategorie",
                            value="Lebensmittel",
                        ).classes("w-full")

                    custom_category = ui.input("Eigene Kategorie").classes("w-full")
                    custom_category.bind_visibility_from(
                        cat_select, "value", lambda value: value == "Andere..."
                    )

                    with ui.card().classes(
                        "w-full bg-slate-50 border border-slate-200 rounded-xl shadow-none"
                    ):
                        with ui.column().classes("w-full gap-3 p-4"):
                            ui.label("Bezahlt von").classes("text-sm font-medium text-slate-700")
                            payer = ui.radio({user.id: user.name for user in users}, value=current_user_id).classes("w-full")

                    with ui.card().classes(
                        "w-full bg-slate-50 border border-slate-200 rounded-xl shadow-none"
                    ):
                        with ui.column().classes("w-full gap-3 p-4"):
                            ui.label("Beteiligte Mitbewohner*innen").classes(
                                "text-sm font-medium text-slate-700"
                            )
                            with ui.column().classes("gap-2"):
                                selected_parts_checkboxes = {
                                    user.id: ui.checkbox(user.name) for user in users
                                }

                    class _PartsGroup:
                        def __init__(self, checkboxes):
                            self._checkboxes = checkboxes

                        @property
                        def value(self):
                            return [uid for uid, cb in self._checkboxes.items() if cb.value]

                    parts = _PartsGroup(selected_parts_checkboxes)

                    class _CategoryField:
                        @property
                        def value(self):
                            # Nutzt freie Eingabe nur bei "Andere...".
                            if cat_select.value == "Andere...":
                                return custom_category.value.strip()
                            return cat_select.value

                    category_field = _CategoryField()

                    def handle_save():
                        if not desc.value or not amt.value or not payer.value or not category_field.value:
                            ui.notify("Bitte alle Pflichtfelder ausfüllen", color="warning")
                            return
                        save_expense(desc.value, amt.value, category_field.value, payer.value, parts.value)
                        ui.notify("Ausgabe erfolgreich gespeichert", color="positive")
                        expense_dialog.close()
                        refresh()

                    desc.on("keydown.enter", handle_save)
                    with ui.row().classes("w-full justify-end gap-2 pt-2"):
                        ui.button("Abbrechen", on_click=expense_dialog.close).props("flat")
                        ui.button("Speichern", on_click=handle_save).classes("bg-green-600 text-white")

            # ── 3-Spalten-Layout ──────────────────────────────────────────────
            with ui.element("div").classes("wg-grid-3"):

                # ── Spalte 1: Kontostände ─────────────────────────────────────
                with ui.element("div"):
                    with ui.card().classes("w-full shadow-md rounded-xl bg-white"):
                        with ui.row().classes("w-full items-center gap-2 px-4 pt-4 pb-2"):
                            ui.icon("account_balance_wallet").style("color: #6366f1; font-size: 1.3rem")
                            with ui.column().classes("gap-0"):
                                ui.label("Kontostände").classes("text-h6 font-bold")
                                ui.label("Positiv = Guthaben · Negativ = Schulden").classes(
                                    "text-xs text-gray-400"
                                )
                        with ui.column().classes("w-full gap-2 p-4 pt-1"):
                            for user in users:
                                balance = balances.get(user.id, 0.0)
                                is_positive = balance >= 0
                                color = "text-green-700" if is_positive else "text-red-700"
                                badge = "Guthaben" if is_positive else "Offen"
                                badge_cls = (
                                    "bg-green-100 text-green-700"
                                    if is_positive
                                    else "bg-red-100 text-red-700"
                                )
                                with ui.row().classes(
                                    "w-full items-center justify-between rounded-xl border "
                                    "border-gray-100 bg-white px-3 py-2 shadow-sm"
                                ):
                                    with ui.column().classes("gap-0"):
                                        ui.label(user.name).classes("text-sm font-bold text-slate-900")
                                        ui.label(badge).classes(
                                            f"text-xs px-2 py-0.5 rounded-full w-fit font-medium {badge_cls}"
                                        )
                                    ui.label(f"CHF {balance:.2f}").classes(f"text-lg font-bold {color}")

                # ── Spalte 2: Ausgleichsvorschläge ────────────────────────────
                with ui.element("div"):
                    with ui.card().classes("w-full shadow-md rounded-xl bg-white"):
                        with ui.row().classes("w-full items-center gap-2 px-4 pt-4 pb-1"):
                            ui.icon("swap_horiz").style("color: #6366f1; font-size: 1.3rem")
                            with ui.column().classes("gap-0"):
                                ui.label("Ausgleichsvorschläge").classes("text-h6 font-bold text-indigo-900")
                                ui.label(
                                    "Offene Beträge ausgleichen oder eigene Zahlung erfassen."
                                ).classes("text-sm text-indigo-500")

                        _pay_state: dict = {"from_id": None, "to_id": None, "amount": 0.0}

                        with ui.dialog() as pay_dialog, ui.card().classes(
                            "w-[36rem] max-w-[95vw] rounded-2xl shadow-xl"
                        ):
                            with ui.row().classes("w-full items-center justify-between p-5 pb-2"):
                                with ui.column().classes("gap-0"):
                                    ui.label("Ausgleich bestätigen").classes("text-h6 font-bold text-slate-900")
                                    ui.label("Zahlungsdetails prüfen und Methode wählen.").classes(
                                        "text-sm text-slate-500"
                                    )
                                ui.button(icon="close", on_click=pay_dialog.close).props("flat round")
                            with ui.column().classes("w-full gap-4 px-5 pb-5 pt-2"):
                                with ui.element("div").style(
                                    "background: #eef2ff; border-radius: 14px; padding: 16px 20px"
                                ):
                                    with ui.row().classes("w-full items-center justify-between"):
                                        with ui.column().classes("gap-0"):
                                            ui.label("VON").style(
                                                "font-size: 0.7rem; color: #94a3b8; font-weight: 700; letter-spacing: 0.05em"
                                            )
                                            pay_from_label = ui.label("–").style(
                                                "font-weight: 800; font-size: 1rem; color: #1e1b4b"
                                            )
                                        ui.icon("arrow_forward").style("color: #a5b4fc; font-size: 1.4rem")
                                        with ui.column().classes("items-end gap-0"):
                                            ui.label("AN").style(
                                                "font-size: 0.7rem; color: #94a3b8; font-weight: 700; letter-spacing: 0.05em"
                                            )
                                            pay_to_label = ui.label("–").style(
                                                "font-weight: 800; font-size: 1rem; color: #1e1b4b"
                                            )
                                    pay_amount_label = ui.label("CHF 0.00").style(
                                        "font-size: 2rem; font-weight: 900; color: #4f46e5; "
                                        "margin-top: 10px; text-align: center; width: 100%"
                                    )
                                pay_method_sel = ui.select(
                                    _PAYMENT_METHODS, label="Zahlungsmethode", value=_PAYMENT_METHODS[0],
                                ).classes("w-full")
                                pay_note_input = ui.input(
                                    "Notiz (optional)", placeholder="z.B. bereits überwiesen"
                                ).classes("w-full")

                                def confirm_auto_pay():
                                    s = _pay_state
                                    if s["from_id"] is None:
                                        return
                                    note = pay_note_input.value.strip()
                                    _save_settlement(s["from_id"], s["to_id"], s["amount"], pay_method_sel.value, note)
                                    pay_note_input.value = ""
                                    pay_dialog.close()

                                with ui.row().classes("w-full justify-end gap-2"):
                                    ui.button("Abbrechen", on_click=pay_dialog.close).props("flat")
                                    ui.button("Zahlung bestätigen", on_click=confirm_auto_pay).style(
                                        "background: #4f46e5; color: white; border-radius: 10px; font-weight: 600"
                                    )

                        def _open_pay_dialog(s: dict) -> None:
                            _pay_state["from_id"] = s["from_user_id"]
                            _pay_state["to_id"] = s["to_user_id"]
                            _pay_state["amount"] = s["amount"]
                            pay_from_label.set_text(user_names.get(s["from_user_id"], "?"))
                            pay_to_label.set_text(user_names.get(s["to_user_id"], "?"))
                            pay_amount_label.set_text(f"CHF {s['amount']:.2f}")
                            pay_dialog.open()

                        def _save_settlement(
                            from_id: int, to_id: int, amount: float, method: str, note: str = ""
                        ) -> None:
                            save_settlement(from_id, to_id, amount, method, note)
                            ui.notify(f"Ausgleich CHF {amount:.2f} via {method} erfasst", color="positive")
                            refresh()

                        with ui.dialog() as manual_dialog, ui.card().classes(
                            "w-[38rem] max-w-[95vw] rounded-2xl shadow-xl"
                        ):
                            with ui.row().classes("w-full items-center justify-between p-5 pb-2"):
                                with ui.column().classes("gap-0"):
                                    ui.label("Manuellen Ausgleich erfassen").classes("text-h6 font-bold text-slate-900")
                                    ui.label(
                                        "Eigene Zahlung hinzufügen, die nicht automatisch berechnet wurde."
                                    ).classes("text-sm text-slate-500")
                                ui.button(icon="close", on_click=manual_dialog.close).props("flat round")
                            with ui.column().classes("w-full gap-4 px-5 pb-5 pt-2"):
                                with ui.row().classes("w-full gap-4"):
                                    man_from = ui.select(
                                        {u.id: u.name for u in users}, label="Wer bezahlt?", value=current_user_id,
                                    ).classes("w-full")
                                    man_to = ui.select(
                                        {u.id: u.name for u in users}, label="Wer erhält?",
                                    ).classes("w-full")
                                man_amt = ui.number("Betrag (CHF)", format="%.2f").classes("w-full")
                                man_method = ui.select(
                                    _PAYMENT_METHODS, label="Zahlungsmethode", value=_PAYMENT_METHODS[0],
                                ).classes("w-full")
                                man_note = ui.input("Notiz (optional)", placeholder="z.B. Stromrechnung April").classes("w-full")

                                def confirm_manual():
                                    if not man_from.value or not man_to.value or not man_amt.value:
                                        ui.notify("Bitte alle Pflichtfelder ausfüllen.", color="warning")
                                        return
                                    if man_from.value == man_to.value:
                                        ui.notify("'Von' und 'An' dürfen nicht dieselbe Person sein.", color="warning")
                                        return
                                    msg = create_manual_debt(
                                        man_from.value, man_to.value, man_amt.value, man_method.value, man_note.value,
                                    )
                                    ui.notify(msg, color="positive")
                                    man_from.value = None
                                    man_to.value = None
                                    man_amt.value = None
                                    man_note.value = ""
                                    manual_dialog.close()
                                    refresh()

                                with ui.row().classes("w-full justify-end gap-2"):
                                    ui.button("Abbrechen", on_click=manual_dialog.close).props("flat")
                                    ui.button("Erfassen", on_click=confirm_manual).style(
                                        "background: #6366f1; color: white; border-radius: 10px; font-weight: 600"
                                    )

                        def _render_transfer_row(from_name: str, to_name: str) -> None:
                            with ui.row().classes("items-center gap-3"):
                                ui.html(
                                    f'<div style="background:#ef4444;border-radius:50%;width:38px;height:38px;'
                                    f'display:flex;align-items:center;justify-content:center;color:white;'
                                    f'font-weight:800;font-size:1rem;flex-shrink:0">{from_name[0].upper()}</div>'
                                )
                                with ui.column().classes("gap-0"):
                                    ui.label(from_name).classes("text-sm font-bold text-slate-800")
                                    ui.label("überweist").classes("text-xs text-slate-400 uppercase tracking-wide")
                                ui.icon("arrow_forward").classes("text-indigo-300 text-xl")
                                with ui.column().classes("gap-0"):
                                    ui.label(to_name).classes("text-sm font-bold text-slate-800")
                                    ui.label("erhält").classes("text-xs text-slate-400 uppercase tracking-wide")
                                ui.html(
                                    f'<div style="background:#10b981;border-radius:50%;width:38px;height:38px;'
                                    f'display:flex;align-items:center;justify-content:center;color:white;'
                                    f'font-weight:800;font-size:1rem;flex-shrink:0">{to_name[0].upper()}</div>'
                                )

                        with ui.column().classes("w-full gap-3 px-4 pt-2 pb-1"):
                            if settlements:
                                ui.label("Automatisch berechnet").style(
                                    "font-size: 0.78rem; font-weight: 700; color: #6366f1; "
                                    "text-transform: uppercase; letter-spacing: 0.05em"
                                )
                                for s in settlements:
                                    from_name = user_names.get(s["from_user_id"], "Unbekannt")
                                    to_name = user_names.get(s["to_user_id"], "Unbekannt")
                                    with ui.element("div").style(
                                        "background: linear-gradient(90deg, #eef2ff 0%, #f5f3ff 100%); "
                                        "border-radius: 14px; border: 1px solid #e0e7ff; padding: 16px 20px"
                                    ):
                                        with ui.row().classes("w-full items-center justify-between flex-wrap gap-3"):
                                            _render_transfer_row(from_name, to_name)
                                            with ui.row().classes("items-center gap-3 flex-wrap"):
                                                ui.label(f"CHF {s['amount']:.2f}").style(
                                                    "font-size: 1.25rem; font-weight: 900; color: #4f46e5"
                                                )
                                                ui.button(
                                                    "Bezahlen",
                                                    on_click=lambda s=s: _open_pay_dialog(s),
                                                ).style(
                                                    "background: #4f46e5; color: white; border-radius: 10px; "
                                                    "font-weight: 600; font-size: 0.82rem; padding: 6px 16px"
                                                )

                            if manual_debts:
                                ui.label("Offene Rechnungen").style(
                                    "font-size: 0.78rem; font-weight: 700; color: #f97316; "
                                    "text-transform: uppercase; letter-spacing: 0.05em; margin-top: 4px"
                                )
                                debt_groups: dict[tuple, list] = {}
                                for debt in manual_debts:
                                    key = (debt.from_user_id, debt.to_user_id)
                                    debt_groups.setdefault(key, []).append(debt)
                                for (from_id, to_id), debts in debt_groups.items():
                                    d_from = debts[0].from_user.name if debts[0].from_user else "Unbekannt"
                                    d_to = debts[0].to_user.name if debts[0].to_user else "Unbekannt"
                                    total = sum(d.amount for d in debts)
                                    descriptions = [d.description for d in debts if d.description]
                                    methods = sorted(set(d.payment_method for d in debts))
                                    with ui.element("div").style(
                                        "background: linear-gradient(90deg, #fff7ed 0%, #ffedd5 100%); "
                                        "border-radius: 14px; border: 1px solid #fed7aa; padding: 16px 20px"
                                    ):
                                        with ui.row().classes("w-full items-center justify-between flex-wrap gap-3"):
                                            with ui.column().classes("gap-1"):
                                                _render_transfer_row(d_from, d_to)
                                                for d_desc in descriptions:
                                                    ui.label(f"• {d_desc}").classes("text-xs text-slate-500 italic")
                                            with ui.row().classes("items-center gap-3 flex-wrap"):
                                                ui.label(f"CHF {total:.2f}").style(
                                                    "font-size: 1.25rem; font-weight: 900; color: #c2410c"
                                                )
                                                for method in methods:
                                                    ui.label(method).classes(
                                                        "text-xs px-2 py-0.5 rounded-full "
                                                        "bg-orange-50 text-orange-600 border border-orange-200"
                                                    )
                                                ui.button(
                                                    "Als bezahlt markieren", icon="check",
                                                    on_click=lambda fi=from_id, ti=to_id: (
                                                        delete_manual_debts_by_pair(fi, ti),
                                                        ui.notify("Ausgleich als bezahlt markiert", color="positive"),
                                                        refresh(),
                                                    ),
                                                ).style(
                                                    "background: #f97316; color: white; border-radius: 10px; "
                                                    "font-weight: 600; font-size: 0.82rem; padding: 6px 14px"
                                                )

                            if not settlements and not manual_debts:
                                with ui.element("div").style(
                                    "background: #f0fdf4; border-radius: 14px; border: 1px solid #bbf7d0; padding: 20px"
                                ):
                                    with ui.row().classes("items-center gap-3"):
                                        ui.icon("check_circle").classes("text-2xl text-green-600")
                                        with ui.column().classes("gap-0"):
                                            ui.label("Alles ausgeglichen").classes("text-base font-bold text-green-800")
                                            ui.label("Keine offenen Ausgleichszahlungen.").classes("text-sm text-green-600")

                        with ui.row().classes("w-full justify-end px-4 pb-4 pt-2"):
                            ui.button("Weiteren Ausgleich erfassen", icon="add", on_click=manual_dialog.open).style(
                                "background: #6366f1; color: white; border-radius: 10px; font-weight: 600"
                            )

                # ── Spalte 3: Kategorien + Ausgabenverlauf ────────────────────
                with ui.element("div"):
                    with ui.card().classes("w-full shadow-md rounded-xl bg-white mb-4"):
                        with ui.row().classes("w-full items-center gap-2 px-4 pt-4 pb-2"):
                            ui.icon("pie_chart").style("color: #10b981; font-size: 1.3rem")
                            with ui.column().classes("gap-0"):
                                ui.label("Ausgaben nach Kategorie").classes("text-h6 font-bold")
                                ui.label("Kostenverteilung auf einen Blick").classes("text-xs text-gray-400")
                        with ui.column().classes("w-full gap-2 p-4 pt-1"):
                            if category_totals:
                                highest_total = category_totals[0]["amount"]
                                for item in category_totals:
                                    width_percent = 100 if highest_total <= 0 else max(
                                        12, int((item["amount"] / highest_total) * 100)
                                    )
                                    with ui.card().classes("w-full border border-gray-100 shadow-sm rounded-xl"):
                                        with ui.row().classes("w-full items-center justify-between p-3 pb-2"):
                                            ui.label(item["category"]).classes("text-sm font-bold text-slate-900")
                                            ui.label(f"CHF {item['amount']:.2f}").classes("text-sm font-bold text-emerald-700")
                                        with ui.element("div").classes("w-full px-3 pb-3"):
                                            ui.element("div").classes("h-2 w-full rounded-full bg-slate-100")
                                            ui.element("div").classes(
                                                "h-2 -mt-2 rounded-full bg-emerald-500 transition-all"
                                            ).style(f"width: {width_percent}%")
                            else:
                                ui.label("Noch keine Kategorien vorhanden.").classes("text-gray-500 italic p-2")

                    with ui.card().classes("w-full shadow-md rounded-xl bg-white"):
                        with ui.row().classes("w-full items-center gap-2 px-4 pt-4 pb-2"):
                            ui.icon("receipt_long").style("color: #64748b; font-size: 1.3rem")
                            with ui.column().classes("gap-0"):
                                ui.label("Ausgabenverlauf").classes("text-h6 font-bold")
                                ui.label("Alle bisher erfassten gemeinsamen Ausgaben.").classes("text-sm text-gray-400")
                        with ui.column().classes("w-full gap-2 p-4 pt-2"):
                            if not expenses:
                                with ui.element("div").style(
                                    "text-align: center; padding: 32px 20px; background: #f8faff; "
                                    "border-radius: 14px; border: 2px dashed #e2e8f0"
                                ):
                                    ui.icon("receipt").style("color: #cbd5e1; font-size: 3rem")
                                    ui.label("Noch keine Ausgaben erfasst.").style(
                                        "color: #94a3b8; margin-top: 8px; font-weight: 600"
                                    )
                            for expense in expenses:
                                with ui.card().classes("w-full border border-gray-100 shadow-sm rounded-xl"):
                                    with ui.row().classes("w-full justify-between items-center p-3"):
                                        with ui.row().classes("items-center gap-3"):
                                            with ui.element("div").style(
                                                "background: #f0fdf4; border-radius: 10px; width: 40px; "
                                                "height: 40px; display: flex; align-items: center; "
                                                "justify-content: center; flex-shrink: 0"
                                            ):
                                                ui.icon("receipt").style("color: #059669; font-size: 1.2rem")
                                            with ui.column().classes("gap-0"):
                                                ui.label(expense.description).classes("font-bold text-slate-800")
                                                ui.label(expense.category or "Allgemein").classes(
                                                    "text-xs px-2 py-0.5 rounded-full bg-emerald-50 "
                                                    "text-emerald-700 border border-emerald-100 w-fit"
                                                )
                                        with ui.column().classes("items-end gap-0"):
                                            ui.label(f"CHF {expense.amount:.2f}").style(
                                                "font-size: 1.1rem; font-weight: 800; color: #065f46"
                                            )
                                            ui.label(
                                                f"von {expense.paid_by.name if expense.paid_by else 'Unbekannt'}"
                                            ).classes("text-xs text-gray-400")
                                        ui.button(
                                            icon="delete",
                                            on_click=lambda e=expense: (
                                                delete_expense(e.id),
                                                ui.notify("Ausgabe gelöscht", color="negative"),
                                                refresh(),
                                            ),
                                        ).props("flat round color=red")
                                    ui.separator().classes("mx-3")
                                    ui.label(
                                        f"Beteiligt: {', '.join(p.name for p in expense.participants)}"
                                    ).classes("px-3 pb-3 pt-2 text-xs italic text-gray-500")

        session.close()

    refresh()
    return refresh
