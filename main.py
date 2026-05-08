from nicegui import ui

from models import init_db
from ui import render_finances_tab, render_tasks_tab, render_users_tab


@ui.page("/")
def main_page():
    ui.add_head_html("""<style>
        body { background: #eef0f8 !important; }
        .q-tab--active .q-tab__label { color: #4f46e5 !important; font-weight: 700; }
        .q-tab--active .q-tab__indicator { background: #4f46e5 !important; }
        .q-tab .q-tab__label { font-size: 0.88rem; font-weight: 500; }
        .q-tab:hover .q-tab__label { color: #4f46e5; }
    </style>""")

    with ui.header().classes("p-0").style(
        "box-shadow: 0 4px 24px rgba(79, 70, 229, 0.28)"
    ):
        with ui.element("div").style(
            "background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); width: 100%"
        ):
            with ui.row().classes("w-full max-w-[1700px] mx-auto items-center px-6 py-4 gap-4"):
                with ui.element("div").style(
                    "background: rgba(255,255,255,0.18); border-radius: 14px; "
                    "padding: 10px 12px; display: flex; align-items: center; justify-content: center"
                ):
                    ui.icon("apartment").style("color: white; font-size: 2rem")
                with ui.column().classes("gap-0"):
                    ui.label("WG-Planner").style(
                        "color: white; font-size: 1.6rem; font-weight: 800; "
                        "line-height: 1.2; letter-spacing: -0.02em"
                    )
                    ui.label("Gemeinsam organisiert – einfach gemacht").style(
                        "color: #c4b5fd; font-size: 0.82rem; margin-top: 3px"
                    )

    with ui.tabs().classes("w-full bg-white").style(
        "box-shadow: 0 2px 10px rgba(0,0,0,0.07)"
    ) as tabs:
        users_tab = ui.tab("Mitbewohner*innen", icon="people")
        finances_tab = ui.tab("Finanzen", icon="payments")
        tasks_tab = ui.tab("Ämtli & Kalender", icon="event")

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

    def _on_tab_change(e):
        # Finanzen-Tab bei jedem Wechsel neu aufbauen, damit das Layout
        # korrekt gerendert wird (NiceGUI/Quasar Tab-Panel Initialisierungsproblem).
        val = e.args[0] if isinstance(e.args, list) else e.args
        if val == "Finanzen":
            finances_refresh()

    tabs.on("update:model-value", _on_tab_change)


if __name__ in {"__main__", "__mp_main__"}:
    init_db()
    ui.run(title="WG-Planner", port=8080, show=False)
