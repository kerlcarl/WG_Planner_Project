from nicegui import ui

from models import MitbewohnerDB
from services import add_user, delete_user, get_session, save_user_edit


def _open_edit_dialog(user, on_done) -> None:
    """Öffnet einen Dialog zum Bearbeiten des Mitbewohner-Namens (UI-Schicht)."""
    with ui.dialog() as dialog, ui.card():
        ui.label(f"Bearbeite {user.name}").classes("text-h6")
        name_input = ui.input(value=user.name)

        def handle_save():
            save_user_edit(user.id, name_input.value.strip())
            ui.notify("Name aktualisiert", color="positive")
            dialog.close()
            on_done()

        with ui.row():
            ui.button("Speichern", on_click=handle_save)
            ui.button("Abbrechen", on_click=dialog.close).props("flat")
    dialog.open()


# Rendert den Benutzer-Tab inklusive Formular und Liste.
def render_users_tab(container, on_users_changed=None):
    def handle_users_changed():
        refresh_list()
        if on_users_changed:
            on_users_changed()

    with container:
        # Hero-Banner
        with ui.element("div").style(
            "background: linear-gradient(135deg, #ede9fe 0%, #dbeafe 100%); "
            "border-radius: 20px; padding: 28px 32px; margin-bottom: 20px; "
            "box-shadow: 0 2px 16px rgba(99,102,241,0.12)"
        ):
            with ui.row().classes("items-center gap-4"):
                with ui.element("div").style(
                    "background: #6366f1; border-radius: 16px; width: 56px; height: 56px; "
                    "display: flex; align-items: center; justify-content: center; flex-shrink: 0"
                ):
                    ui.icon("people").style("color: white; font-size: 2rem")
                with ui.column().classes("gap-0"):
                    ui.label("Mitbewohner*innen").style(
                        "font-size: 1.4rem; font-weight: 800; color: #3730a3; line-height: 1.2"
                    )
                    ui.label("Verwalte alle Personen in deiner WG").style(
                        "color: #6366f1; font-size: 0.85rem; margin-top: 4px"
                    )

        # 2-Spalten-Layout: Formular links, Liste rechts
        with ui.element("div").classes("wg-grid-2"):

            # ── Spalte 1: Formular ────────────────────────────────────────
            with ui.element("div"):
                with ui.card().classes("w-full").style(
                    "border-radius: 18px; box-shadow: 0 4px 20px rgba(99,102,241,0.10); "
                    "border: 1.5px solid #e0e7ff; padding: 22px"
                ):
                    with ui.row().classes("items-center gap-3 mb-3"):
                        ui.icon("person_add").style("color: #6366f1; font-size: 1.4rem")
                        ui.label("Neue*n Mitbewohner*in hinzufügen").style(
                            "font-size: 1rem; font-weight: 700; color: #3730a3"
                        )

                    name_input = ui.input("Name", placeholder="z.B. Anna Müller").classes("w-full")

                    def handle_add():
                        name = name_input.value.strip()
                        if not name:
                            return
                        add_user(name)
                        name_input.value = ""
                        ui.notify("Mitbewohner*in hinzugefügt", color="positive")
                        handle_users_changed()

                    name_input.on("keydown.enter", handle_add)
                    ui.button("Hinzufügen", icon="add", on_click=handle_add).classes(
                        "w-full bg-indigo-600 text-white mt-3"
                    ).style("border-radius: 10px; font-weight: 600")

            # ── Spalte 2: Mitbewohner-Liste ───────────────────────────────
            with ui.element("div"):
                with ui.row().classes("items-center gap-2 mb-3"):
                    ui.icon("group").style("color: #6366f1; font-size: 1.2rem")
                    ui.label("Aktuelle Mitbewohner*innen").style(
                        "font-size: 1.05rem; font-weight: 700; color: #1e1b4b"
                    )
                list_items_container = ui.element("div").classes("wg-cards-2")

    def refresh_list():
        list_items_container.clear()
        with get_session() as session:
            users = session.query(MitbewohnerDB).order_by(MitbewohnerDB.name).all()
            user_data = [{"id": u.id, "name": u.name, "color": u.color or "#6366f1"} for u in users]

        with list_items_container:
            if not user_data:
                with ui.element("div").style(
                    "grid-column: 1 / -1; text-align: center; padding: 48px 20px; "
                    "background: #f8f8ff; border-radius: 18px; border: 2px dashed #c7d2fe"
                ):
                    ui.icon("group_add").style("color: #a5b4fc; font-size: 3.5rem")
                    ui.label("Noch keine Mitbewohner*innen vorhanden.").style(
                        "color: #818cf8; margin-top: 10px; font-weight: 600"
                    )
                    ui.label("Füge oben deine erste Person hinzu!").style(
                        "color: #a5b4fc; font-size: 0.85rem; margin-top: 4px"
                    )
            else:
                for data in user_data:
                    color = data["color"]
                    with ui.card().classes("w-full").style(
                        f"border-radius: 16px; box-shadow: 0 2px 14px rgba(0,0,0,0.07); "
                        f"border-left: 5px solid {color}; padding: 0; overflow: hidden"
                    ):
                        with ui.row().classes("w-full items-center justify-between").style(
                            "padding: 14px 18px"
                        ):
                            with ui.row().classes("items-center gap-3"):
                                ui.html(
                                    f'<div style="background:{color}; border-radius:50%; '
                                    f'width:44px; height:44px; display:flex; align-items:center; '
                                    f'justify-content:center; color:white; font-size:1.15rem; '
                                    f'font-weight:800; flex-shrink:0">'
                                    f'{data["name"][0].upper()}</div>'
                                )
                                with ui.column().classes("gap-0"):
                                    ui.label(data["name"]).style(
                                        "font-weight: 700; font-size: 1rem; color: #1e1b4b"
                                    )
                                    ui.label("Mitbewohner*in").style(
                                        "font-size: 0.73rem; color: #94a3b8; margin-top: 2px"
                                    )
                            with ui.row().classes("gap-1"):
                                # Für den Edit-Dialog brauchen wir ein ORM-Objekt → kurze Re-Abfrage
                                ui.button(
                                    icon="edit",
                                    on_click=lambda uid=data["id"], uname=data["name"]: _open_edit_dialog(
                                        type("_User", (), {"id": uid, "name": uname})(),
                                        handle_users_changed,
                                    ),
                                ).props("flat round").style("color: #6366f1")
                                ui.button(
                                    icon="delete",
                                    on_click=lambda uid=data["id"]: (
                                        delete_user(uid),
                                        ui.notify("Eintrag gelöscht", color="negative"),
                                        handle_users_changed(),
                                    ),
                                ).props("flat round color=red")

    refresh_list()
    return refresh_list
