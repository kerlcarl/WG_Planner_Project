# Darstellung des Tabs fuer Mitbewohner*innen.
from nicegui import ui

from models import MitbewohnerDB
from services import add_user, delete_user, edit_user, get_session


def render_users_tab(container, on_users_changed=None):
    def handle_users_changed():
        refresh_list()
        if on_users_changed:
            on_users_changed()

    with container:
        with ui.card().classes("w-full mb-4 p-4 shadow-md"):
            ui.label("Neue*n Mitbewohner*in hinzufuegen").classes("text-h6 text-blue-700 font-bold")
            name_input = ui.input("Name")

            def handle_add():
                if name_input.value:
                    add_user(name_input, handle_users_changed)

            name_input.on("keydown.enter", handle_add)
            ui.button("Hinzufuegen", on_click=handle_add).classes("w-full bg-blue-600 text-white mt-2")

        ui.label("Aktuelle Mitbewohner*innen").classes("text-h6 mt-4 mb-2 font-bold")
        list_items_container = ui.column().classes("w-full")

    def refresh_list():
        list_items_container.clear()
        session = get_session()
        users = session.query(MitbewohnerDB).order_by(MitbewohnerDB.name).all()

        with list_items_container:
            if not users:
                ui.label("Noch keine Mitbewohner*innen vorhanden.").classes("text-gray-500 italic p-4")
            for user in users:
                with ui.card().classes("w-full border-l-4 border-blue-500 shadow-sm mb-2"):
                    with ui.row().classes("w-full items-center justify-between p-2"):
                        ui.label(user.name).classes("text-bold text-lg")
                        with ui.row().classes("gap-1"):
                            ui.button(
                                icon="edit",
                                on_click=lambda current_user=user: edit_user(current_user, handle_users_changed),
                            ).props("flat round")
                            ui.button(
                                icon="delete",
                                on_click=lambda current_user=user: delete_user(current_user, handle_users_changed),
                            ).props("flat round color=red")

        session.close()

    refresh_list()
