from nicegui import app, ui

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


def _primary_btn(text: str, on_click) -> ui.button:
    return ui.button(text, on_click=on_click).classes("w-full").style(
        "background: linear-gradient(135deg,#312e81,#6366f1); color: white; "
        "border-radius: 10px; font-size: 1rem; padding: 10px; font-weight: 600; "
        "box-shadow: 0 4px 14px rgba(99,102,241,0.35);"
    ).props("no-caps unelevated")


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
