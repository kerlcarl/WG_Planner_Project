import os

from nicegui import app, ui

from auth_services import get_user_by_id, save_avatar
from services import save_user_edit

_CARD_STYLE = (
    "border-radius: 16px; padding: 28px 32px; width: 100%; max-width: 520px; "
    "background: rgba(255,255,255,0.93); box-shadow: 0 4px 24px rgba(30,27,75,0.10); margin-bottom: 20px;"
)

_AVATAR_DIR = "static/avatars"


def _section(title: str):
    ui.label(title).classes("text-subtitle1 font-bold").style("color: #312e81; margin-bottom: 14px")


def _input(label: str, value: str = "") -> ui.input:
    return ui.input(label=label, value=value).props("outlined dense").classes("w-full")


def _err() -> ui.label:
    return ui.label("").style("color: #dc2626; font-size: 0.82rem; min-height: 16px; margin-top: -4px")


def _success() -> ui.label:
    return ui.label("").style("color: #16a34a; font-size: 0.82rem; min-height: 16px; margin-top: -4px")


def _avatar_html(user: dict, size: int = 56) -> str:
    if user.get("avatar_path") and os.path.exists(user["avatar_path"]):
        return (
            f'<img src="/{user["avatar_path"]}" '
            f'style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;" />'
        )
    initials = "".join(p[0].upper() for p in (user.get("name") or "?").split()[:2])
    color = user.get("color") or "#312e81"
    return (
        f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:{color};'
        f'display:flex;align-items:center;justify-content:center;'
        f'color:white;font-weight:700;font-size:{size//3}px;">{initials}</div>'
    )


def register_settings_page():
    @ui.page("/settings")
    def settings_page():
        user_id = app.storage.user.get("user_id")
        if not user_id:
            ui.navigate.to("/select-user")
            return

        ui.add_head_html("""<style>
body {
  background-color: #eaecf5;
  background-image:
    linear-gradient(rgba(234,236,245,0.80),rgba(234,236,245,0.80)),
    url('https://images.unsplash.com/photo-1586023492125-27b2c045efd7?auto=format&fit=crop&w=1920&q=80');
  background-size: cover; background-attachment: fixed; background-position: center;
}
</style>""")

        with ui.header().classes("p-4").style(
            "background: linear-gradient(135deg,#1e1b4b 0%,#312e81 40%,#4338ca 80%,#6366f1 100%); "
            "box-shadow: 0 4px 32px rgba(30,27,75,0.40);"
        ):
            with ui.row().classes("w-full max-w-[1700px] mx-auto items-center px-2 gap-3"):
                ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/")).props(
                    "flat round"
                ).style("color: white")
                ui.label("Einstellungen").classes("text-h5 text-white font-bold").style(
                    "text-shadow: 0 2px 12px rgba(0,0,0,0.25)"
                )

        with ui.column().classes("items-center w-full").style("padding: 32px 16px"):

            user = get_user_by_id(user_id)
            if not user:
                ui.label("Nutzer nicht gefunden.").style("color: #dc2626")
                return

            name_parts = (user["name"] or "").split(" ", 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""

            # ── Profildaten ────────────────────────────────────────────────────
            with ui.card().style(_CARD_STYLE):
                _section("Profildaten")

                avatar_html = ui.html(_avatar_html(user, 72)).style("margin-bottom: 16px")

                with ui.row().classes("w-full gap-3"):
                    first_in = _input("Vorname", first_name).classes("flex-1")
                    last_in = _input("Nachname", last_name).classes("flex-1")
                profile_err = _err()
                profile_ok = _success()

                def save_profile():
                    profile_err.set_text("")
                    profile_ok.set_text("")
                    first = first_in.value.strip()
                    last = last_in.value.strip()
                    if not first:
                        profile_err.set_text("Vorname ist ein Pflichtfeld")
                        return
                    new_name = f"{first} {last}".strip()
                    save_user_edit(user_id, new_name)
                    profile_ok.set_text("Gespeichert ✓")
                    avatar_html.set_content(_avatar_html(get_user_by_id(user_id), 72))
                    ui.notify("Profil aktualisiert", color="positive")

                ui.button("Speichern", on_click=save_profile).props("no-caps unelevated").style(
                    "background: #312e81; color: white; border-radius: 8px; margin-top: 6px"
                )

            # ── Profilbild ─────────────────────────────────────────────────────
            with ui.card().style(_CARD_STYLE):
                _section("Profilbild")
                ui.label("Lade ein Bild hoch (JPG/PNG, max. 2 MB).").style(
                    "color: #6b7280; font-size: 0.85rem; margin-bottom: 10px"
                )

                def handle_upload(e):
                    os.makedirs(_AVATAR_DIR, exist_ok=True)
                    path = os.path.join(_AVATAR_DIR, f"user_{user_id}.jpg")
                    with open(path, "wb") as f:
                        f.write(e.content.read())
                    save_avatar(user_id, path)
                    avatar_html.set_content(_avatar_html(get_user_by_id(user_id), 72))
                    ui.notify("Profilbild gespeichert", color="positive")

                ui.upload(
                    label="Bild auswählen",
                    on_upload=handle_upload,
                    auto_upload=True,
                    max_file_size=2_000_000,
                ).props("accept=image/*").classes("w-full")

            # ── Nutzer wechseln ────────────────────────────────────────────────
            ui.button("Nutzer wechseln", icon="swap_horiz", on_click=lambda: (
                app.storage.user.pop("user_id", None),
                ui.navigate.to("/select-user"),
            )).props("no-caps outline").style(
                "color: #6366f1; border-color: #6366f1; border-radius: 8px; margin-top: 8px"
            )
