from nicegui import app, ui

from auth_services import (
    authenticate_user,
    create_reset_token,
    register_user,
    reset_password_with_token,
    validate_password,
)
from models import MitbewohnerDB, Session

# ── shared style helpers ───────────────────────────────────────────────────────

_PAGE_STYLE = """
body {
  background-color: #eaecf5;
  background-image:
    linear-gradient(rgba(234,236,245,0.82),rgba(234,236,245,0.82)),
    url('https://images.unsplash.com/photo-1586023492125-27b2c045efd7?auto=format&fit=crop&w=1920&q=80');
  background-size: cover; background-attachment: fixed; background-position: center;
}
"""

_CARD_STYLE = (
    "border-radius: 18px; padding: 32px 36px; width: 100%; max-width: 420px; "
    "background: rgba(255,255,255,0.93); box-shadow: 0 8px 40px rgba(30,27,75,0.13);"
)


def _header_label(text: str):
    ui.label(text).classes("text-h5 font-bold").style(
        "color: #312e81; letter-spacing: -0.3px; margin-bottom: 6px"
    )


def _sub_label(text: str):
    ui.label(text).style("color: #6b7280; font-size: 0.9rem; margin-bottom: 18px")


def _input(label: str, type_: str = "text", placeholder: str = "") -> ui.input:
    is_pw = type_ == "password"
    i = ui.input(
        label=label,
        placeholder=placeholder,
        password=is_pw,
        password_toggle_button=is_pw,
    ).props(f'type={type_} outlined dense' if not is_pw else 'outlined dense').classes("w-full")
    return i


def _error_label() -> ui.label:
    lbl = ui.label("").style(
        "color: #dc2626; font-size: 0.82rem; margin-top: -6px; min-height: 18px"
    )
    return lbl


def _primary_btn(text: str, on_click) -> ui.button:
    return ui.button(text, on_click=on_click).classes("w-full").style(
        "background: linear-gradient(135deg,#312e81,#6366f1); color: white; "
        "border-radius: 10px; font-size: 1rem; padding: 10px; font-weight: 600; "
        "box-shadow: 0 4px 14px rgba(99,102,241,0.35);"
    ).props("no-caps unelevated")


def _link_btn(text: str, target: str):
    ui.button(text, on_click=lambda: ui.navigate.to(target)).props(
        "flat no-caps dense"
    ).style("color: #6366f1; font-size: 0.85rem; padding: 0")


# ── /login ─────────────────────────────────────────────────────────────────────

def register_login_page():
    @ui.page("/login")
    def login_page():
        ui.add_head_html(f"<style>{_PAGE_STYLE}</style>")
        with ui.column().classes("items-center justify-center w-full").style("min-height: 100vh; padding: 24px"):
            with ui.card().style(_CARD_STYLE):
                _header_label("Willkommen zurück")
                _sub_label("Melde dich bei deinem WG-Planner an")

                email_in = _input("E-Mail", "email", "name@beispiel.ch")
                email_err = _error_label()
                pw_in = _input("Passwort", "password")
                pw_err = _error_label()
                general_err = ui.label("").style(
                    "color: #dc2626; font-size: 0.85rem; background: #fef2f2; "
                    "border-radius: 8px; padding: 8px 12px; width: 100%; "
                    "display: none; text-align: center"
                )

                spinner = ui.spinner("dots", size="sm", color="indigo").style("display: none")

                def do_login():
                    email_err.set_text("")
                    pw_err.set_text("")
                    general_err.style("display: none")

                    ok = True
                    if not email_in.value.strip():
                        email_err.set_text("Pflichtfeld")
                        ok = False
                    if not pw_in.value:
                        pw_err.set_text("Pflichtfeld")
                        ok = False
                    if not ok:
                        return

                    spinner.style("display: inline-block")
                    try:
                        user_id = authenticate_user(email_in.value, pw_in.value)
                    except Exception:
                        user_id = None
                    finally:
                        spinner.style("display: none")

                    if user_id is None:
                        general_err.set_text("E-Mail oder Passwort falsch.")
                        general_err.style(
                            "color: #dc2626; font-size: 0.85rem; background: #fef2f2; "
                            "border-radius: 8px; padding: 8px 12px; width: 100%; "
                            "display: block; text-align: center"
                        )
                        return

                    app.storage.user["user_id"] = user_id
                    ui.navigate.to("/")

                _primary_btn("Anmelden", do_login)

                ui.separator().classes("my-3")
                with ui.row().classes("w-full justify-between items-center"):
                    _link_btn("Noch kein Konto? Registrieren", "/register")
                    _link_btn("Passwort vergessen?", "/forgot-password")


# ── /register ──────────────────────────────────────────────────────────────────

def register_register_page():
    @ui.page("/register")
    def register_page():
        ui.add_head_html(f"<style>{_PAGE_STYLE}</style>")
        with ui.column().classes("items-center justify-center w-full").style("min-height: 100vh; padding: 24px"):
            with ui.card().style(_CARD_STYLE):
                _header_label("Konto erstellen")
                _sub_label("Registriere dich für deinen WG-Planner")

                with ui.row().classes("w-full gap-3"):
                    first_in = _input("Vorname").classes("flex-1")
                    last_in = _input("Nachname").classes("flex-1")
                name_err = _error_label()

                email_in = _input("E-Mail", "email", "name@beispiel.ch")
                email_err = _error_label()

                pw_vals = {"pw": "", "pw2": ""}

                pw_err = _error_label()

                def _on_pw(e):
                    pw_vals["pw"] = e.value
                    err = validate_password(e.value) if e.value else None
                    pw_err.set_text(err or "")

                pw_in = ui.input(
                    label="Passwort", password=True, password_toggle_button=True,
                    on_change=_on_pw,
                ).props("outlined dense").classes("w-full")

                pw2_err = _error_label()

                def _on_pw2(e):
                    pw_vals["pw2"] = e.value
                    if e.value and e.value != pw_vals["pw"]:
                        pw2_err.set_text("Passwörter stimmen nicht überein")
                    else:
                        pw2_err.set_text("")

                pw2_in = ui.input(
                    label="Passwort bestätigen", password=True, password_toggle_button=True,
                    on_change=_on_pw2,
                ).props("outlined dense").classes("w-full")

                general_err = ui.label("").style(
                    "color: #dc2626; font-size: 0.85rem; background: #fef2f2; "
                    "border-radius: 8px; padding: 8px 12px; width: 100%; display: none"
                )

                spinner = ui.spinner("dots", size="sm", color="indigo").style("display: none")

                def do_register():
                    name_err.set_text("")
                    email_err.set_text("")
                    pw_err.set_text("")
                    pw2_err.set_text("")
                    general_err.style("display: none")

                    pw = pw_vals["pw"]
                    pw2 = pw_vals["pw2"]

                    ok = True
                    if not first_in.value.strip() or not last_in.value.strip():
                        name_err.set_text("Vor- und Nachname sind Pflichtfelder")
                        ok = False
                    if not email_in.value.strip():
                        email_err.set_text("Pflichtfeld")
                        ok = False
                    pw_validation = validate_password(pw)
                    if pw_validation:
                        pw_err.set_text(pw_validation)
                        ok = False
                    if pw != pw2:
                        pw2_err.set_text("Passwörter stimmen nicht überein")
                        ok = False
                    if not ok:
                        return

                    spinner.style("display: inline-block")
                    try:
                        user_id, err = register_user(first_in.value, last_in.value, email_in.value, pw)
                    except Exception as ex:
                        err = f"Fehler: {ex}"
                        user_id = None
                    finally:
                        spinner.style("display: none")

                    if err:
                        general_err.set_text(err)
                        general_err.style(
                            "color: #dc2626; font-size: 0.85rem; background: #fef2f2; "
                            "border-radius: 8px; padding: 8px 12px; width: 100%; display: block"
                        )
                        return

                    app.storage.user["user_id"] = user_id
                    ui.notify("Willkommen! Konto erfolgreich erstellt.", color="positive")
                    ui.navigate.to("/")

                _primary_btn("Registrieren", do_register)
                ui.separator().classes("my-3")
                with ui.row().classes("w-full justify-center"):
                    _link_btn("Bereits registriert? Zum Login", "/login")


# ── /forgot-password ───────────────────────────────────────────────────────────

def register_forgot_password_page():
    @ui.page("/forgot-password")
    def forgot_page():
        ui.add_head_html(f"<style>{_PAGE_STYLE}</style>")
        with ui.column().classes("items-center justify-center w-full").style("min-height: 100vh; padding: 24px"):
            with ui.card().style(_CARD_STYLE):
                _header_label("Passwort zurücksetzen")
                _sub_label("Gib deine E-Mail-Adresse ein. Du erhältst einen Reset-Link.")

                email_in = _input("E-Mail", "email")
                msg = ui.label("").style("font-size: 0.85rem; min-height: 18px")
                spinner = ui.spinner("dots", size="sm", color="indigo").style("display: none")

                def do_reset():
                    msg.set_text("")
                    if not email_in.value.strip():
                        msg.style("color: #dc2626")
                        msg.set_text("Pflichtfeld")
                        return
                    spinner.style("display: inline-block")
                    token = create_reset_token(email_in.value)
                    spinner.style("display: none")
                    if token:
                        # In a real deployment, send this via email.
                        # For dev: show the link directly.
                        ui.notify(
                            f"Reset-Link (nur für Entwicklung): /reset-password?token={token}",
                            type="info", timeout=0, close_button=True,
                        )
                    # Always show the same message to prevent user enumeration
                    msg.style("color: #16a34a")
                    msg.set_text("Falls die E-Mail bekannt ist, wurde ein Link versendet.")

                _primary_btn("Link anfordern", do_reset)
                ui.separator().classes("my-3")
                with ui.row().classes("w-full justify-center"):
                    _link_btn("Zurück zum Login", "/login")


# ── /reset-password ────────────────────────────────────────────────────────────

def register_reset_password_page():
    @ui.page("/reset-password")
    def reset_page(token: str = ""):
        ui.add_head_html(f"<style>{_PAGE_STYLE}</style>")
        with ui.column().classes("items-center justify-center w-full").style("min-height: 100vh; padding: 24px"):
            with ui.card().style(_CARD_STYLE):
                _header_label("Neues Passwort")
                _sub_label("Wähle ein neues Passwort für dein Konto.")

                pw_in = _input("Neues Passwort", "password")
                pw_err = _error_label()
                pw2_in = _input("Passwort bestätigen", "password")
                pw2_err = _error_label()
                msg = ui.label("").style("font-size: 0.85rem; min-height: 18px")

                def _live(*_):
                    e = validate_password(pw_in.value) if pw_in.value else None
                    pw_err.set_text(e or "")

                pw_in.on("update:model-value", _live)

                def do_reset():
                    pw_err.set_text("")
                    pw2_err.set_text("")
                    ok = True
                    e = validate_password(pw_in.value)
                    if e:
                        pw_err.set_text(e)
                        ok = False
                    if pw_in.value != pw2_in.value:
                        pw2_err.set_text("Passwörter stimmen nicht überein")
                        ok = False
                    if not ok:
                        return
                    err = reset_password_with_token(token, pw_in.value)
                    if err:
                        msg.style("color: #dc2626")
                        msg.set_text(err)
                    else:
                        ui.notify("Passwort erfolgreich geändert.", color="positive")
                        ui.navigate.to("/login")

                _primary_btn("Passwort speichern", do_reset)


# ── /select-user ───────────────────────────────────────────────────────────────

def register_select_user_page():
    @ui.page("/select-user")
    def select_user_page():
        ui.add_head_html(f"<style>{_PAGE_STYLE}</style>")
        with ui.column().classes("items-center justify-center w-full").style("min-height: 100vh; padding: 24px"):
            with ui.card().style(_CARD_STYLE):
                with ui.column().classes("items-center mb-4"):
                    with ui.element("div").style(
                        "background: linear-gradient(135deg,#312e81,#6366f1); border-radius: 20px; "
                        "width: 64px; height: 64px; display: flex; align-items: center; justify-content: center; "
                        "box-shadow: 0 4px 20px rgba(99,102,241,0.35); margin-bottom: 12px"
                    ):
                        ui.icon("home").style("color: white; font-size: 2rem")
                    _header_label("WG-Planner")
                _sub_label("Wer bist du? Wähle deinen Namen aus.")

                with Session() as session:
                    users = session.query(MitbewohnerDB).order_by(MitbewohnerDB.name).all()
                    user_options = {u.name: u.id for u in users}

                if not user_options:
                    ui.label("Keine Mitbewohner*innen gefunden.").style("color: #dc2626; font-size: 0.9rem")
                    return

                select = ui.select(
                    options=list(user_options.keys()),
                    value=next(iter(user_options.keys())),
                ).props("outlined dense").classes("w-full")

                def do_enter():
                    app.storage.user["user_id"] = user_options[select.value]
                    ui.navigate.to("/")

                ui.element("div").style("margin-top: 8px")
                _primary_btn("Los geht's!", do_enter)
