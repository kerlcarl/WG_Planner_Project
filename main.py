from nicegui import ui

from models import init_db
from ui import render_finances_tab, render_tasks_tab, render_users_tab


# Baut die Startseite mit Header, Tabs und den drei Inhaltsbereichen.
@ui.page("/")
def main_page():
    ui.query("body").style("background-color: #f0f2f5")

    with ui.header().classes("bg-indigo-700 p-4 shadow-lg"):
        with ui.row().classes("w-full max-w-[1700px] mx-auto items-center px-2"):
            ui.label("WG-Planner").classes("text-h4 text-white font-bold")

    with ui.tabs().classes("w-full bg-white shadow-sm") as tabs:
        users_tab = ui.tab("Mitbewohner*innen", icon="people")
        finances_tab = ui.tab("Finanzen", icon="payments")
        tasks_tab = ui.tab("Ämtli & Kalender", icon="event")

    # Tab-Inhalte werden in eigenen Containern gerendert.
    with ui.tab_panels(tabs, value=users_tab).classes("w-full max-w-[1700px] mx-auto bg-transparent p-4"):
        with ui.tab_panel(users_tab).classes("px-0"):
            users_container = ui.column().classes("w-full")
        with ui.tab_panel(finances_tab).classes("px-0"):
            finances_container = ui.column().classes("w-full")
        with ui.tab_panel(tasks_tab).classes("px-0"):
            tasks_container = ui.column().classes("w-full")

    # Renderer liefern Refresh-Funktionen zurueck, damit Daten neu geladen werden koennen.
    finances_refresh = render_finances_tab(finances_container)
    tasks_refresh = render_tasks_tab(tasks_container)
    render_users_tab(users_container, on_users_changed=lambda: (finances_refresh(), tasks_refresh()))

    def _on_tab_change(e):
        # Finanzen-Tab bei jedem Wechsel neu aufbauen, damit das Layout
        # korrekt gerendert wird (NiceGUI/Quasar Tab-Panel Initialisierungsproblem).
        val = e.args[0] if isinstance(e.args, list) else e.args
        if val == "Finanzen":
            finances_refresh()

    tabs.on("update:model-value", _on_tab_change)


if __name__ in {"__main__", "__mp_main__"}:
    # Erst Datenbanktabellen sicherstellen, dann Webserver starten.
    init_db()
    ui.run(title="WG-Planner", port=8080, show=False)
