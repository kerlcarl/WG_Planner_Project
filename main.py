# Einstiegspunkt der App und Aufbau der Hauptseite mit NiceGUI.
from nicegui import ui

from models import init_db
from ui import render_finances_tab, render_tasks_tab, render_users_tab


@ui.page("/")
def main_page():
    ui.query("body").style("background-color: #f0f2f5")

    with ui.header().classes("bg-indigo-700 p-4 shadow-lg"):
        with ui.row().classes("w-full max-w-[1700px] mx-auto items-center px-2"):
            ui.label("WG-Planner").classes("text-h4 text-white font-bold")

    with ui.tabs().classes("w-full bg-white shadow-sm") as tabs:
        users_tab = ui.tab("Mitbewohner*innen", icon="people")
        finances_tab = ui.tab("Finanzen", icon="payments")
        tasks_tab = ui.tab("Aemtli & Kalender", icon="event")

    with ui.tab_panels(tabs, value=users_tab).classes("w-full max-w-[1700px] mx-auto bg-transparent p-4"):
        with ui.tab_panel(users_tab).classes("px-0"):
            users_container = ui.column().classes("w-full")
        with ui.tab_panel(finances_tab).classes("px-0"):
            finances_container = ui.column().classes("w-full")
        with ui.tab_panel(tasks_tab).classes("px-0"):
            tasks_container = ui.column().classes("w-full")

    finances_refresh = render_finances_tab(finances_container)
    tasks_refresh = render_tasks_tab(tasks_container)
    render_users_tab(users_container, on_users_changed=lambda: (finances_refresh(), tasks_refresh()))


if __name__ in {"__main__", "__mp_main__"}:
    init_db()
    ui.run(title="WG-Planner", port=8081, show=False)
