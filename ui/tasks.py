from datetime import datetime, timedelta

from nicegui import ui
from sqlalchemy.orm import joinedload

from models import MitbewohnerDB, Task
from services import delete_task, get_session, save_task, update_task, update_task_status

_WOCHENTAGE_KURZ = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
_WOCHENTAGE_LANG = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]


def render_tasks_tab(container, current_user_id: int = None):
    _form_active = {"value": False}
    _dialog_open = {"value": False}

    def refresh():
        if _form_active["value"] or _dialog_open["value"]:
            return
        container.clear()
        with get_session() as session:
            tasks = session.query(Task).options(joinedload(Task.assigned_to)).all()
            users = session.query(MitbewohnerDB).all()

        now = datetime.now()
        today_str = now.strftime("%Y/%m/%d")
        cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
        soon_cutoff = now + timedelta(hours=24)
        datum_label = f"{_WOCHENTAGE_LANG[now.weekday()]}, {now.strftime('%d.%m.%Y')}"

        overdue_tasks = sorted(
            [t for t in tasks if not t.is_done and t.due_date and t.due_date < cutoff],
            key=lambda t: t.due_date,
        )
        soon_tasks = sorted(
            [t for t in tasks if not t.is_done and t.due_date and cutoff <= t.due_date <= soon_cutoff],
            key=lambda t: t.due_date,
        )
        upcoming_tasks = sorted(
            [t for t in tasks if not t.is_done
             and not (t.due_date and t.due_date < cutoff)
             and not (t.due_date and t.due_date <= soon_cutoff)],
            key=lambda t: (t.due_date is None, t.due_date),
        )
        open_tasks = overdue_tasks + soon_tasks + upcoming_tasks
        done_tasks = sorted(
            [t for t in tasks if t.is_done],
            key=lambda t: (t.due_date is None, t.due_date),
        )

        with container:
            # ── Hero-Banner ───────────────────────────────────────────────────
            with ui.element("div").style(
                "background: linear-gradient(135deg, #fff7ed 0%, #fed7aa 60%, #fdba74 100%); "
                "border-radius: 20px; padding: 24px 32px; margin-bottom: 20px; "
                "box-shadow: 0 4px 20px rgba(249,115,22,0.16)"
            ):
                with ui.row().classes("w-full items-center justify-between flex-wrap gap-4"):
                    with ui.row().classes("items-center gap-4"):
                        with ui.element("div").style(
                            "background: #f97316; border-radius: 16px; width: 52px; height: 52px; "
                            "display: flex; align-items: center; justify-content: center; flex-shrink: 0"
                        ):
                            ui.icon("task_alt").style("color: white; font-size: 1.9rem")
                        with ui.column().classes("gap-0"):
                            ui.label("Ämtli").style(
                                "font-size: 1.4rem; font-weight: 800; color: #9a3412; line-height: 1.2"
                            )
                            ui.label("Aufgaben verwalten und den Überblick behalten").style(
                                "color: #f97316; font-size: 0.85rem; margin-top: 4px"
                            )
                    with ui.row().classes("items-center gap-4 flex-wrap"):
                        for count, label, color in [
                            (len(overdue_tasks), "Abgelaufen", "#ef4444"),
                            (len(soon_tasks),    "Bald fällig", "#f97316"),
                            (len(upcoming_tasks),"Zu erledigen", "#ca8a04"),
                            (len(done_tasks),    "Erledigt",    "#16a34a"),
                        ]:
                            with ui.column().classes("items-center gap-0"):
                                ui.label(str(count)).style(
                                    f"font-size: 1.7rem; font-weight: 900; color: {color}; line-height: 1"
                                )
                                ui.label(label).style(
                                    f"color: {color}; font-size: 0.72rem; font-weight: 600; margin-top: 2px"
                                )
                        # Aktuelles Datum oben rechts
                        with ui.element("div").style(
                            "background: white; border-radius: 14px; padding: 8px 16px; "
                            "box-shadow: 0 2px 10px rgba(249,115,22,0.15); text-align: right"
                        ):
                            ui.label(datum_label).style(
                                "font-size: 0.95rem; font-weight: 700; color: #9a3412"
                            )

            # ── Bearbeiten-Dialog ─────────────────────────────────────────────
            _edit_task_id = {"value": None}

            with ui.dialog().props("persistent") as edit_task_dialog, ui.card().classes(
                "w-[38rem] max-w-[95vw] rounded-2xl shadow-xl"
            ):
                with ui.row().classes("w-full items-center justify-between p-5 pb-2"):
                    with ui.column().classes("gap-0"):
                        ui.label("Ämtli bearbeiten").classes("text-h6 font-bold text-slate-900")
                        ui.label("Titel, Zuständigkeit und Deadline anpassen.").classes("text-sm text-slate-500")
                    ui.button(
                        icon="close",
                        on_click=lambda: (_dialog_open.update(value=False), edit_task_dialog.close()),
                    ).props("flat round")

                with ui.column().classes("w-full gap-4 px-5 pb-5 pt-3"):
                    edit_title = ui.input("Titel").classes("w-full")
                    edit_who = ui.select(
                        {user.id: user.name for user in users},
                        label="Zuständige*r Mitbewohner*in",
                    ).classes("w-full")

                    with ui.input("Deadline (optional)", placeholder="TT.MM.JJJJ") as edit_deadline:
                        with ui.menu().props("no-parent-event") as edit_deadline_menu:
                            with ui.date().props(
                                f'mask="DD.MM.YYYY" :options="d => d >= \'{today_str}\'"'
                            ).bind_value(edit_deadline):
                                with ui.row().classes("justify-end"):
                                    ui.button("OK", on_click=edit_deadline_menu.close).props("flat dense")
                        with edit_deadline.add_slot("append"):
                            ui.icon("calendar_month").classes("cursor-pointer").on(
                                "click", edit_deadline_menu.open
                            )
                    edit_deadline.classes("w-full")

                    def handle_edit_task_save():
                        err = update_task(_edit_task_id["value"], edit_title.value, edit_who.value, edit_deadline.value)
                        if err:
                            ui.notify(err, color="warning")
                            return
                        ui.notify("Ämtli aktualisiert", color="positive")
                        _dialog_open["value"] = False
                        edit_task_dialog.close()
                        refresh()

                    with ui.row().classes("w-full justify-end gap-2 pt-2"):
                        ui.button(
                            "Abbrechen",
                            on_click=lambda: (_dialog_open.update(value=False), edit_task_dialog.close()),
                        ).props("flat")
                        ui.button("Speichern", on_click=handle_edit_task_save).style(
                            "background: #f97316; color: white; border-radius: 10px; font-weight: 600"
                        )

            def _open_edit_task_dialog(task):
                _edit_task_id["value"] = task.id
                edit_title.value = task.title
                edit_who.value = task.assigned_to_id
                edit_deadline.value = task.due_date.strftime("%d.%m.%Y") if task.due_date else ""
                _dialog_open["value"] = True
                edit_task_dialog.open()

            def _deadline_badge(task, badge_bg, badge_text_color):
                if not task.due_date:
                    return
                tag = _WOCHENTAGE_KURZ[task.due_date.weekday()]
                date_str = task.due_date.strftime("%d.%m.%Y")
                with ui.element("div").style(
                    f"background: {badge_bg}; border-radius: 10px; padding: 5px 10px; "
                    f"text-align: center; flex-shrink: 0; min-width: 68px"
                ):
                    ui.label(tag).style(
                        f"font-size: 0.7rem; font-weight: 700; color: {badge_text_color}; "
                        f"text-transform: uppercase; line-height: 1.2"
                    )
                    ui.label(date_str).style(
                        f"font-size: 0.75rem; font-weight: 800; color: {badge_text_color}; line-height: 1.3"
                    )

            def _render_task_card(task, is_done, is_overdue=False, is_soon=False, is_upcoming=False):
                if is_done:
                    card_style = (
                        "border-radius: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); "
                        "border-left: 5px solid #86efac; background: #f0fdf4; "
                        "padding: 0; overflow: hidden; margin-bottom: 8px"
                    )
                    badge_bg, badge_tc = "#dcfce7", "#16a34a"
                elif is_overdue:
                    card_style = (
                        "border-radius: 14px; box-shadow: 0 2px 8px rgba(239,68,68,0.12); "
                        "border-left: 5px solid #ef4444; background: #fff5f5; "
                        "padding: 0; overflow: hidden; margin-bottom: 8px"
                    )
                    badge_bg, badge_tc = "#fee2e2", "#ef4444"
                elif is_soon:
                    card_style = (
                        "border-radius: 14px; box-shadow: 0 2px 8px rgba(249,115,22,0.15); "
                        "border-left: 5px solid #f97316; background: #fff7ed; "
                        "padding: 0; overflow: hidden; margin-bottom: 8px"
                    )
                    badge_bg, badge_tc = "#fed7aa", "#c2410c"
                elif is_upcoming:
                    card_style = (
                        "border-radius: 14px; box-shadow: 0 2px 8px rgba(234,179,8,0.15); "
                        "border-left: 5px solid #eab308; background: #fefce8; "
                        "padding: 0; overflow: hidden; margin-bottom: 8px"
                    )
                    badge_bg, badge_tc = "#fef08a", "#854d0e"
                else:
                    card_style = (
                        "border-radius: 14px; box-shadow: 0 2px 8px rgba(234,179,8,0.10); "
                        "border-left: 5px solid #eab308; background: #fefce8; "
                        "padding: 0; overflow: hidden; margin-bottom: 8px"
                    )
                    badge_bg, badge_tc = "#fef08a", "#854d0e"

                with ui.card().classes("w-full").style(card_style):
                    with ui.row().classes("w-full items-center p-3 gap-3"):
                        ui.checkbox(
                            value=is_done,
                            on_change=lambda event, t=task: (
                                update_task_status(t.id, event.value), refresh()
                            ),
                        ).style("flex-shrink: 0")
                        with ui.column().classes("flex-grow gap-0"):
                            label_style = (
                                "font-weight: 600; color: #6b7280; text-decoration: line-through"
                                if is_done else
                                "font-weight: 700; color: #7f1d1d" if is_overdue else
                                "font-weight: 700; color: #9a3412" if is_soon else
                                "font-weight: 700; color: #713f12"
                            )
                            ui.label(task.title).style(label_style)
                            assigned_name = task.assigned_to.name if task.assigned_to else "Niemand"
                            ui.label(f"Zuständig: {assigned_name}").style(
                                "font-size: 0.78rem; margin-top: 2px; "
                                + ("color: #fca5a5" if is_overdue else
                                   "color: #fdba74" if is_soon else
                                   "color: #a16207" if (is_upcoming or not is_done) else
                                   "color: #94a3b8")
                            )
                        if is_done and task.completed_at:
                            with ui.element("div").style(
                                "background: #dcfce7; border-radius: 10px; padding: 5px 10px; "
                                "text-align: center; flex-shrink: 0; min-width: 68px"
                            ):
                                ui.label("Erledigt").style(
                                    "font-size: 0.7rem; font-weight: 700; color: #16a34a; "
                                    "text-transform: uppercase; line-height: 1.2"
                                )
                                ui.label(task.completed_at.strftime("%d.%m.%Y")).style(
                                    "font-size: 0.75rem; font-weight: 800; color: #16a34a; line-height: 1.3"
                                )
                        elif task.due_date and not is_done:
                            _deadline_badge(task, badge_bg, badge_tc)
                        if not is_done:
                            with ui.row().classes("gap-0 flex-shrink-0"):
                                ui.button(
                                    icon="edit",
                                    on_click=lambda t=task: _open_edit_task_dialog(t),
                                ).props("flat round color=orange").style("width: 32px; height: 32px")
                                ui.button(
                                    icon="delete",
                                    on_click=lambda t=task: (
                                        delete_task(t.id),
                                        ui.notify("Ämtli gelöscht", color="negative"),
                                        refresh(),
                                    ),
                                ).props("flat round color=red").style("width: 32px; height: 32px")

            def _section_header(icon_name, label, count, color):
                with ui.row().classes("items-center gap-2 mb-3"):
                    ui.icon(icon_name).style(f"color: {color}; font-size: 1.15rem")
                    ui.label(label).style(f"font-size: 1rem; font-weight: 700; color: {color}")
                    ui.label(str(count)).style(
                        f"background: {color}; color: white; border-radius: 999px; "
                        f"font-size: 0.75rem; font-weight: 700; padding: 2px 8px"
                    )

            # ── 3-Spalten-Layout ──────────────────────────────────────────────
            with ui.element("div").classes("wg-grid-3"):

                # ── Spalte 1: Neues Ämtli ─────────────────────────────────────
                with ui.element("div"):
                    with ui.card().classes("w-full").style(
                        "border-radius: 18px; box-shadow: 0 4px 20px rgba(249,115,22,0.10); "
                        "border: 1.5px solid #fed7aa; padding: 22px"
                    ):
                        with ui.row().classes("items-center gap-3 mb-4"):
                            ui.icon("add_task").style("color: #f97316; font-size: 1.4rem")
                            ui.label("Neues Ämtli erstellen").style(
                                "font-size: 1rem; font-weight: 700; color: #9a3412"
                            )

                        title = ui.input(
                            "Titel", placeholder="z.B. Küche putzen",
                            on_change=lambda e: _form_active.update(value=bool(e.value.strip())),
                        ).classes("w-full")
                        who = ui.select(
                            {user.id: user.name for user in users},
                            label="Zuständige*r Mitbewohner*in",
                            value=current_user_id,
                        ).classes("w-full mt-2")

                        with ui.input("Deadline (optional)", placeholder="TT.MM.JJJJ") as deadline:
                            with ui.menu().props("no-parent-event") as deadline_menu:
                                with ui.date().props(
                                    f'mask="DD.MM.YYYY" :options="d => d >= \'{today_str}\'"'
                                ).bind_value(deadline):
                                    with ui.row().classes("justify-end"):
                                        ui.button("OK", on_click=deadline_menu.close).props("flat dense")
                            with deadline.add_slot("append"):
                                ui.icon("calendar_month").classes("cursor-pointer").on(
                                    "click", deadline_menu.open
                                )
                        deadline.classes("w-full mt-2")

                        def handle_task():
                            err = save_task(title.value, who.value, deadline.value)
                            if err:
                                ui.notify(err, color="warning")
                                return
                            ui.notify("Neues Ämtli erstellt", color="positive")
                            _form_active["value"] = False
                            refresh()

                        title.on("keydown.enter", handle_task)
                        ui.button("Ämtli erstellen", icon="add", on_click=handle_task).classes(
                            "w-full bg-orange-500 text-white mt-4"
                        ).style("border-radius: 10px; font-weight: 600")

                # ── Spalte 2: Abgelaufen + Bald fällig ───────────────────────
                with ui.element("div"):
                    if overdue_tasks:
                        _section_header("warning", "Abgelaufen", len(overdue_tasks), "#ef4444")
                        for task in overdue_tasks:
                            _render_task_card(task, False, is_overdue=True)
                        if soon_tasks:
                            ui.separator().classes("my-4")

                    if soon_tasks:
                        _section_header("schedule", "Bald fällig", len(soon_tasks), "#f97316")
                        for task in soon_tasks:
                            _render_task_card(task, False, is_soon=True)

                    if not overdue_tasks and not soon_tasks:
                        with ui.element("div").style(
                            "text-align: center; padding: 40px 16px; background: #fff7ed; "
                            "border-radius: 16px; border: 2px dashed #fed7aa"
                        ):
                            ui.icon("check_circle_outline").style("color: #fdba74; font-size: 3rem")
                            ui.label("Alles im grünen Bereich!").style(
                                "color: #f97316; margin-top: 8px; font-weight: 600; font-size: 0.95rem"
                            )
                            ui.label("Keine abgelaufenen oder dringenden Ämtli.").style(
                                "color: #fdba74; font-size: 0.82rem; margin-top: 4px"
                            )

                # ── Spalte 3: Offen + Erledigt ────────────────────────────────
                with ui.element("div"):
                    if upcoming_tasks:
                        _section_header("pending_actions", "Zu erledigen", len(upcoming_tasks), "#ca8a04")
                        for task in upcoming_tasks:
                            _render_task_card(task, False, is_upcoming=True)
                    elif not overdue_tasks and not soon_tasks:
                        with ui.element("div").style(
                            "text-align: center; padding: 40px 16px; background: #fefce8; "
                            "border-radius: 16px; border: 2px dashed #fde047"
                        ):
                            ui.icon("task_alt").style("color: #eab308; font-size: 3rem")
                            ui.label("Keine offenen Ämtli.").style(
                                "color: #ca8a04; margin-top: 8px; font-weight: 600"
                            )
                            ui.label("Erstelle links dein erstes Ämtli!").style(
                                "color: #eab308; font-size: 0.82rem; margin-top: 4px"
                            )

                    if done_tasks:
                        if upcoming_tasks:
                            ui.separator().classes("my-4")
                        _section_header("check_circle", "Erledigt", len(done_tasks), "#16a34a")
                        for task in done_tasks:
                            _render_task_card(task, True)

    refresh()
    return refresh
