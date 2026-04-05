# Darstellung des Tabs fuer Aemtli und Kalender.
from nicegui import ui

from models import MitbewohnerDB, Task
from services import get_session, save_task, update_task_status


def render_tasks_tab(container):
    def refresh():
        container.clear()
        session = get_session()
        tasks = session.query(Task).all()
        users = session.query(MitbewohnerDB).all()
        event_days = [task.created_at.strftime("%Y-%m-%d") for task in tasks if task.created_at]

        with container:
            with ui.expansion("Neues Aemtli erstellen", icon="playlist_add").classes(
                "w-full bg-orange-50 mb-4 shadow-sm"
            ):
                title = ui.input("Titel")
                who = ui.select({user.id: user.name for user in users}, label="Zustaendige*r Mitbewohner*in")

                def handle_task():
                    save_task(title, who, refresh)

                title.on("keydown.enter", handle_task)
                ui.button("Erstellen", on_click=handle_task).classes("bg-orange-500 text-white w-full mt-2")

            ui.label("Aemtli-Kalender").classes("text-h6 font-bold mb-2")
            ui.date().props(f'events={event_days} event-color="orange"').classes("w-full mb-4")

            ui.label("Offene Aufgaben").classes("text-h6 font-bold mb-2")
            for task in tasks:
                status_class = "bg-green-100 line-through text-gray-400" if task.is_done else "bg-yellow-50"
                with ui.card().classes(f"w-full mb-2 border-l-4 border-orange-400 {status_class} shadow-sm"):
                    with ui.row().classes("w-full items-center p-2"):
                        ui.checkbox(
                            value=task.is_done,
                            on_change=lambda event, current_task=task: update_task_status(
                                current_task, event.value, refresh
                            ),
                        )
                        with ui.column().classes("flex-grow"):
                            ui.label(task.title).classes("text-bold")
                            ui.label(
                                f"Zustaendig: {task.assigned_to.name if task.assigned_to else 'Niemand'}"
                            ).classes("text-xs")

        session.close()

    refresh()
    return refresh
