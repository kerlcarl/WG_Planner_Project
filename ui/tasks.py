import json

from nicegui import ui

from models import MitbewohnerDB, Task
from services import get_session, save_task, update_task_status


# Rendert den Aufgaben-Tab und liefert eine Refresh-Funktion zurueck.
def render_tasks_tab(container, current_user_id: int = None):
    # Baut den kompletten Tab aus aktuellen DB-Daten neu auf.
    def refresh():
        container.clear()
        session = get_session()
        tasks = session.query(Task).all()
        users = session.query(MitbewohnerDB).all()
        # Nur Aufgaben mit Deadline im Kalender markieren.
        event_days = [task.due_date.strftime("%Y/%m/%d") for task in tasks if task.due_date]
        open_tasks = [t for t in tasks if not t.is_done]
        done_tasks = [t for t in tasks if t.is_done]
        tasks_with_deadline = sorted(
            [t for t in tasks if t.due_date and not t.is_done],
            key=lambda t: t.due_date,
        )

        with container:
            # Hero-Banner
            with ui.element("div").style(
                "background: linear-gradient(135deg, #fff7ed 0%, #fed7aa 60%, #fdba74 100%); "
                "border-radius: 20px; padding: 28px 32px; margin-bottom: 20px; "
                "box-shadow: 0 4px 20px rgba(249,115,22,0.16)"
            ):
                with ui.row().classes("w-full items-center justify-between flex-wrap gap-4"):
                    with ui.row().classes("items-center gap-4"):
                        with ui.element("div").style(
                            "background: #f97316; border-radius: 16px; width: 56px; height: 56px; "
                            "display: flex; align-items: center; justify-content: center; flex-shrink: 0"
                        ):
                            ui.icon("task_alt").style("color: white; font-size: 2rem")
                        with ui.column().classes("gap-0"):
                            ui.label("Ämtli & Kalender").style(
                                "font-size: 1.4rem; font-weight: 800; color: #9a3412; line-height: 1.2"
                            )
                            ui.label("Aufgaben verwalten und den Überblick behalten").style(
                                "color: #f97316; font-size: 0.85rem; margin-top: 4px"
                            )
                    with ui.row().classes("gap-6"):
                        with ui.column().classes("items-end gap-0"):
                            ui.label(str(len(open_tasks))).style(
                                "font-size: 1.9rem; font-weight: 900; color: #9a3412; line-height: 1"
                            )
                            ui.label("Offen").style("color: #f97316; font-size: 0.78rem; margin-top: 2px")
                        with ui.column().classes("items-end gap-0"):
                            ui.label(str(len(done_tasks))).style(
                                "font-size: 1.9rem; font-weight: 900; color: #9a3412; line-height: 1"
                            )
                            ui.label("Erledigt").style("color: #f97316; font-size: 0.78rem; margin-top: 2px")

            # Ämtli erstellen – Karte
            with ui.card().classes("w-full mb-5").style(
                "border-radius: 18px; box-shadow: 0 4px 20px rgba(249,115,22,0.10); "
                "border: 1.5px solid #fed7aa; padding: 22px"
            ):
                with ui.row().classes("items-center gap-3 mb-3"):
                    ui.icon("add_task").style("color: #f97316; font-size: 1.4rem")
                    ui.label("Neues Ämtli erstellen").style(
                        "font-size: 1rem; font-weight: 700; color: #9a3412"
                    )

                title = ui.input("Titel", placeholder="z.B. Küche putzen").classes("w-full")
                who = ui.select(
                    {user.id: user.name for user in users},
                    label="Zuständige*r Mitbewohner*in",
                    value=current_user_id,
                ).classes("w-full mt-2")

                # Deadline-Eingabe mit Datepicker-Popup
                with ui.input("Deadline (optional)", placeholder="TT.MM.JJJJ") as deadline:
                    with ui.menu().props("no-parent-event") as deadline_menu:
                        with ui.date().props('mask="DD.MM.YYYY"').bind_value(deadline):
                            with ui.row().classes("justify-end"):
                                ui.button("OK", on_click=deadline_menu.close).props("flat dense")
                    with deadline.add_slot("append"):
                        ui.icon("calendar_month").classes("cursor-pointer").on(
                            "click", deadline_menu.open
                        )
                deadline.classes("w-full mt-2")

                def handle_task():
                    save_task(title, who, deadline.value, refresh)

                title.on("keydown.enter", handle_task)
                ui.button("Ämtli erstellen", icon="add", on_click=handle_task).classes(
                    "w-full bg-orange-500 text-white mt-3"
                ).style("border-radius: 10px; font-weight: 600")

            # Kalender
            with ui.card().classes("w-full mb-5 shadow-md rounded-xl bg-white"):
                with ui.row().classes("items-center gap-2 px-4 pt-4 pb-2"):
                    ui.icon("calendar_month").style("color: #f97316; font-size: 1.3rem")
                    with ui.column().classes("gap-0"):
                        ui.label("Ämtli-Kalender").style(
                            "font-size: 1.05rem; font-weight: 700; color: #1e1b4b"
                        )
                        ui.label("Orange markierte Tage haben eine Deadline").style(
                            "font-size: 0.78rem; color: #94a3b8"
                        )
                with ui.element("div").classes("px-4 pb-2"):
                    ui.date().props(f':events=\'{json.dumps(event_days)}\' event-color="orange"').classes("w-full")

                # Deadline-Liste unterhalb des Kalenders
                if tasks_with_deadline:
                    with ui.element("div").classes("px-4 pb-4"):
                        ui.separator().classes("my-2")
                        with ui.row().classes("items-center gap-2 mb-2"):
                            ui.icon("schedule").style("color: #f97316; font-size: 1rem")
                            ui.label("Anstehende Deadlines").style(
                                "font-size: 0.9rem; font-weight: 700; color: #9a3412"
                            )
                        for t in tasks_with_deadline:
                            assigned = t.assigned_to.name if t.assigned_to else "–"
                            deadline_str = t.due_date.strftime("%d.%m.%Y")
                            with ui.row().classes("items-center gap-2 py-1 flex-wrap"):
                                ui.icon("event").style(
                                    "color: #f97316; font-size: 1rem; flex-shrink: 0"
                                )
                                ui.label(deadline_str).style(
                                    "font-weight: 700; color: #9a3412; font-size: 0.85rem; "
                                    "min-width: 80px"
                                )
                                ui.label("·").style("color: #fdba74")
                                ui.label(assigned).style(
                                    "font-weight: 600; color: #1e1b4b; font-size: 0.85rem"
                                )
                                ui.label("–").style("color: #94a3b8")
                                ui.label(t.title).style(
                                    "color: #374151; font-size: 0.85rem"
                                )
                else:
                    with ui.element("div").classes("px-4 pb-4"):
                        ui.label("Keine offenen Deadlines").style(
                            "color: #94a3b8; font-size: 0.8rem; font-style: italic"
                        )

            # Offene Aufgaben
            with ui.row().classes("items-center gap-2 mb-3"):
                ui.icon("pending_actions").style("color: #f97316; font-size: 1.2rem")
                ui.label("Offene Aufgaben").style(
                    "font-size: 1.05rem; font-weight: 700; color: #1e1b4b"
                )
                ui.label(str(len(open_tasks))).style(
                    "background: #f97316; color: white; border-radius: 999px; "
                    "font-size: 0.78rem; font-weight: 700; padding: 2px 9px"
                )

            if not tasks:
                with ui.element("div").style(
                    "text-align: center; padding: 48px 20px; background: #fff7ed; "
                    "border-radius: 18px; border: 2px dashed #fed7aa"
                ):
                    ui.icon("task_alt").style("color: #fdba74; font-size: 3.5rem")
                    ui.label("Noch keine Ämtli vorhanden.").style(
                        "color: #fb923c; margin-top: 10px; font-weight: 600"
                    )
                    ui.label("Erstelle oben dein erstes Ämtli!").style(
                        "color: #fdba74; font-size: 0.85rem; margin-top: 4px"
                    )
            else:
                for task in tasks:
                    is_done = task.is_done
                    card_style = (
                        "border-radius: 16px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); "
                        "border-left: 5px solid #86efac; background: #f0fdf4; padding: 0; overflow: hidden; margin-bottom: 10px"
                        if is_done else
                        "border-radius: 16px; box-shadow: 0 2px 10px rgba(249,115,22,0.10); "
                        "border-left: 5px solid #f97316; background: white; padding: 0; overflow: hidden; margin-bottom: 10px"
                    )
                    with ui.card().classes("w-full").style(card_style):
                        with ui.row().classes("w-full items-center p-3 gap-3"):
                            ui.checkbox(
                                value=is_done,
                                on_change=lambda event, t=task: update_task_status(t, event.value, refresh),
                            ).style("flex-shrink: 0")
                            with ui.column().classes("flex-grow gap-0"):
                                label_style = (
                                    "font-weight: 600; color: #6b7280; text-decoration: line-through"
                                    if is_done else
                                    "font-weight: 700; color: #1e1b4b"
                                )
                                ui.label(task.title).style(label_style)
                                assigned_name = task.assigned_to.name if task.assigned_to else "Niemand"
                                meta_parts = [f"Zuständig: {assigned_name}"]
                                if task.due_date:
                                    meta_parts.append(f"Deadline: {task.due_date.strftime('%d.%m.%Y')}")
                                ui.label("  ·  ".join(meta_parts)).style(
                                    "font-size: 0.78rem; color: #94a3b8; margin-top: 2px"
                                )
                            status_text = "Erledigt" if is_done else "Offen"
                            status_style = (
                                "background: #dcfce7; color: #16a34a; border-radius: 999px; "
                                "font-size: 0.75rem; font-weight: 700; padding: 3px 10px; flex-shrink: 0"
                                if is_done else
                                "background: #fff7ed; color: #ea580c; border-radius: 999px; "
                                "font-size: 0.75rem; font-weight: 700; padding: 3px 10px; flex-shrink: 0"
                            )
                            ui.label(status_text).style(status_style)

        session.close()

    refresh()
    return refresh
