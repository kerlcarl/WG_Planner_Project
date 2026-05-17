import os

from nicegui import app, ui
from pydantic import BaseModel

from auth_services import get_user_by_id
from models import Task, init_db, seed_db
from services import get_session
from ui import (
    register_forgot_password_page,
    register_login_page,
    register_register_page,
    register_reset_password_page,
    register_select_user_page,
    register_settings_page,
    render_collab_tab,
    render_finances_tab,
    render_tasks_tab,
    render_users_tab,
)


class _ReactPayload(BaseModel):
    emoji: str
    user_id: int


@app.post("/posts/{post_id}/react")
async def _react_to_post(post_id: int, payload: _ReactPayload):
    from services import toggle_reaction
    reactions, user_reactions = toggle_reaction(payload.user_id, post_id, payload.emoji)
    return {"reactions": reactions, "user_reactions": user_reactions}


def _page_style() -> str:
    return """
body {
  background-color: #eaecf5;
  background-image:
    linear-gradient(rgba(234, 236, 245, 0.80), rgba(234, 236, 245, 0.80)),
    url('https://images.unsplash.com/photo-1586023492125-27b2c045efd7?auto=format&fit=crop&w=1920&q=80');
  background-size: cover;
  background-attachment: fixed;
  background-position: center center;
}
.q-tab-panels, .q-tab-panel { background: transparent !important; }
.q-tabs {
  background: rgba(255, 255, 255, 0.86) !important;
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  box-shadow: 0 2px 24px rgba(0, 0, 0, 0.08) !important;
}
.q-card:not([style*="background"]) { background: rgba(255, 255, 255, 0.88) !important; }
.q-card[style*="background: white"] { background: rgba(255, 255, 255, 0.88) !important; }
.q-card[style*="background: #f0fdf4"] { background: rgba(240, 253, 244, 0.90) !important; }
.q-card[style*="background: #fff5f5"] { background: rgba(255, 245, 245, 0.90) !important; }
.q-card[style*="background: #f8fafc"] { background: rgba(248, 250, 252, 0.90) !important; }
@keyframes rx-badge-pop {
  0%   { transform: scale(0.45); opacity: 0; }
  60%  { transform: scale(1.18); opacity: 1; }
  80%  { transform: scale(0.94); }
  100% { transform: scale(1);    opacity: 1; }
}
.rx-badge-anim { animation: rx-badge-pop 0.30s cubic-bezier(0.34, 1.56, 0.64, 1) both; }
.wg-grid-3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  align-items: start;
}
.wg-grid-2 {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 20px;
  align-items: start;
}
.wg-cards-2 {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}
@media (max-width: 1200px) {
  .wg-grid-3 { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 1000px) {
  .wg-collab-grid { grid-template-columns: 1fr !important; }
}
@media (max-width: 800px) {
  .wg-grid-3, .wg-grid-2, .wg-cards-2 { grid-template-columns: 1fr; }
}
"""


def _avatar_html(user: dict, size: int = 38) -> str:
    import os
    if user.get("avatar_path") and os.path.exists(user["avatar_path"]):
        return (
            f'<img src="/{user["avatar_path"]}" '
            f'style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;cursor:pointer;" />'
        )
    initials = "".join(p[0].upper() for p in (user.get("name") or "?").split()[:2])
    color = user.get("color") or "#4338ca"
    return (
        f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:{color};'
        f'display:flex;align-items:center;justify-content:center;'
        f'color:white;font-weight:700;font-size:{size//3}px;cursor:pointer;">{initials}</div>'
    )


# Baut die Startseite mit Header, Tabs und den drei Inhaltsbereichen.
@ui.page("/")
def main_page():
    user_id = app.storage.user.get("user_id")
    if not user_id:
        ui.navigate.to("/select-user")
        return

    ui.add_head_html(f"<style>{_page_style()}</style>")

    ui.add_head_html("""
<script>
async function reactToPost(postId, emoji, userId) {
  if (!userId) return;
  try {
    var resp = await fetch('/posts/' + postId + '/react', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({emoji: emoji, user_id: userId})
    });
    if (!resp.ok) return;
    var data = await resp.json();
    var bar = document.getElementById('rxbar-' + postId);
    if (!bar) return;
    bar.querySelectorAll('[data-emoji]').forEach(function(btn) {
      var e = btn.getAttribute('data-emoji');
      var countEl = btn.querySelector('.rxcount');
      var count = data.reactions[e] || 0;
      if (countEl) countEl.textContent = count > 0 ? ' ' + count : '';
      if (data.user_reactions.indexOf(e) !== -1) {
        btn.classList.add('rx-active');
      } else {
        btn.classList.remove('rx-active');
      }
    });
  } catch(err) {
    console.error('Reaction error:', err);
  }
}
</script>
""")

    ui.add_head_html("""
<script>
(function () {
    var THRESHOLD = 80;
    var HOLD_MS   = 200;

    var startX = 0, startY = 0;
    var holding = false, dragging = false;
    var holdTimer = null;

    // Selektoren, auf denen kein Drag gestartet werden soll
    var EXCLUDE = [
        'input', 'button', 'a', 'select', 'textarea', 'label',
        '.q-tabs', '.q-btn', '.q-checkbox', '.q-radio',
        '.q-select', '.q-input', '.q-menu', '.q-dialog'
    ].join(', ');

    function tabButtons() {
        return Array.from(document.querySelectorAll('.q-tabs .q-tab'));
    }

    function activeIndex() {
        return tabButtons().findIndex(function (b) {
            return b.classList.contains('q-tab--active');
        });
    }

    function goToTab(i) {
        var btns = tabButtons();
        if (i >= 0 && i < btns.length) btns[i].click();
    }

    function getPanels() {
        return document.querySelector('.q-tab-panels');
    }

    function onDown(e) {
        if (e.target.closest(EXCLUDE)) return;
        var p = e.touches ? e.touches[0] : e;
        startX   = p.clientX;
        startY   = p.clientY;
        holding  = false;
        dragging = false;
        holdTimer = setTimeout(function () { holding = true; }, HOLD_MS);
    }

    function onMove(e) {
        if (!holding) return;
        var p  = e.touches ? e.touches[0] : e;
        var dx = p.clientX - startX;
        var dy = p.clientY - startY;

        if (!dragging) {
            if (Math.abs(dx) < 8 && Math.abs(dy) < 8) return;
            // Mehr vertikal als horizontal → Scrollen erlauben, Drag abbrechen
            if (Math.abs(dy) > Math.abs(dx)) { holding = false; return; }
            dragging = true;
        }

        var el = getPanels();
        if (!el) return;
        e.preventDefault();

        var tabCount = tabButtons().length;
        var ai       = activeIndex();
        var clamped  = dx;

        // Rubber-Band-Effekt an den Rändern (erster / letzter Tab)
        if ((ai === 0 && dx > 0) || (ai === tabCount - 1 && dx < 0)) {
            clamped = dx * 0.15;
        }

        el.style.transition = 'none';
        el.style.transform  = 'translateX(' + clamped + 'px)';
    }

    function onUp(e) {
        clearTimeout(holdTimer);
        if (!dragging) { holding = false; dragging = false; return; }
        holding  = false;
        dragging = false;

        var el = getPanels();
        if (!el) return;

        var p        = e.changedTouches ? e.changedTouches[0] : e;
        var dx       = p.clientX - startX;
        var tabCount = tabButtons().length;
        var ai       = activeIndex();

        if (dx < -THRESHOLD && ai < tabCount - 1) {
            // Ausreichend nach links gezogen → nächster Tab
            el.style.transition = 'transform 0.25s ease';
            el.style.transform  = 'translateX(-80px)';
            setTimeout(function () {
                el.style.transition = 'none';
                el.style.transform  = '';
                goToTab(ai + 1);
            }, 200);
        } else if (dx > THRESHOLD && ai > 0) {
            // Ausreichend nach rechts gezogen → vorheriger Tab
            el.style.transition = 'transform 0.25s ease';
            el.style.transform  = 'translateX(80px)';
            setTimeout(function () {
                el.style.transition = 'none';
                el.style.transform  = '';
                goToTab(ai - 1);
            }, 200);
        } else {
            // Nicht genug gezogen → Snap-Back
            el.style.transition = 'transform 0.3s ease';
            el.style.transform  = '';
            setTimeout(function () { el.style.transition = ''; }, 350);
        }
    }

    function init() {
        document.addEventListener('mousedown', onDown);
        document.addEventListener('mousemove', onMove, { passive: false });
        document.addEventListener('mouseup',   onUp);
        document.addEventListener('touchstart', onDown, { passive: true });
        document.addEventListener('touchmove',  onMove, { passive: false });
        document.addEventListener('touchend',   onUp);
    }

    // Quasar/Vue mountet async → pollen bis q-tab-panels im DOM ist
    function waitAndInit() {
        if (document.querySelector('.q-tab-panels')) {
            init();
        } else {
            setTimeout(waitAndInit, 150);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', waitAndInit);
    } else {
        waitAndInit();
    }
})();
</script>
""")

    current_user = get_user_by_id(user_id)

    with ui.header().classes("p-4").style(
        "background: linear-gradient(135deg, #1e1b4b 0%, #312e81 40%, #4338ca 80%, #6366f1 100%); "
        "box-shadow: 0 4px 32px rgba(30, 27, 75, 0.40); "
        "backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px)"
    ):
        with ui.row().classes("w-full max-w-[1700px] mx-auto items-center px-2"):
            ui.label("WG-Planner").classes("text-h4 text-white font-bold").style(
                "text-shadow: 0 2px 12px rgba(0,0,0,0.25); letter-spacing: -0.5px"
            )
            ui.space()
            with ui.element("div").style("position: relative; margin-right: 4px"):
                bell_btn = ui.button(
                    icon="notifications",
                    on_click=lambda: tabs.set_value(tasks_tab),
                ).props("flat round").style("color: white; font-size: 1.4rem")
                overdue_badge = ui.badge("").props("floating").style(
                    "background: #ef4444; color: white; font-weight: 700; "
                    "font-size: 0.68rem; min-width: 18px; height: 18px; "
                    "border-radius: 9px; padding: 0 5px"
                )
                overdue_badge.set_visibility(False)
                ui.tooltip("Überfällige Ämtli").style("font-size: 0.8rem")
            with ui.element("div").style("position: relative"):
                avatar = ui.html(_avatar_html(current_user or {"name": "?"}, 38))
                with ui.menu().props("auto-close") as user_menu:
                    if current_user:
                        ui.label(current_user["name"]).style(
                            "padding: 8px 16px; font-weight: 600; color: #312e81; font-size: 0.9rem"
                        )
                        ui.separator()
                    ui.menu_item("Einstellungen", on_click=lambda: ui.navigate.to("/settings"))
                    ui.menu_item(
                        "Nutzer wechseln",
                        on_click=lambda: (app.storage.user.pop("user_id", None), ui.navigate.to("/select-user")),
                    )
                avatar.on("click", user_menu.open)

    with ui.tabs().classes("w-full bg-white shadow-sm") as tabs:
        users_tab = ui.tab("Mitbewohner*innen", icon="people")
        finances_tab = ui.tab("Finanzen", icon="payments")
        tasks_tab = ui.tab("Ämtli & Kalender", icon="event")
        collab_tab = ui.tab("Kollaborations-Hub", icon="groups")

    # Tab-Inhalte werden in eigenen Containern gerendert.
    with ui.tab_panels(tabs, value=users_tab).classes("w-full max-w-[1700px] mx-auto bg-transparent p-4"):
        with ui.tab_panel(users_tab).classes("px-0"):
            users_container = ui.column().classes("w-full")
        with ui.tab_panel(finances_tab).classes("px-0"):
            finances_container = ui.column().classes("w-full")
        with ui.tab_panel(tasks_tab).classes("px-0"):
            tasks_container = ui.column().classes("w-full")
        with ui.tab_panel(collab_tab).classes("px-0"):
            collab_container = ui.column().classes("w-full")

    # Renderer liefern Refresh-Funktionen zurueck, damit Daten neu geladen werden koennen.
    finances_refresh = render_finances_tab(finances_container, user_id)
    tasks_refresh = render_tasks_tab(tasks_container, user_id)
    collab_refresh = render_collab_tab(collab_container)
    users_refresh = render_users_tab(
        users_container,
        on_users_changed=lambda: (finances_refresh(), tasks_refresh(), collab_refresh()),
    )

    # Alle Tabs alle 10 Sekunden neu laden – so sehen alle Mitbewohner
    # Änderungen der anderen in Echtzeit. Collab-Tab hat eigene Timer (2s/5s).
    ui.timer(10.0, users_refresh)
    ui.timer(10.0, finances_refresh)
    ui.timer(10.0, tasks_refresh)

    def _refresh_overdue_badge():
        from datetime import date, datetime, time
        cutoff = datetime.combine(date.today(), time())
        with get_session() as s:
            count = s.query(Task).filter(
                Task.is_done == False,
                Task.due_date.isnot(None),
                Task.due_date < cutoff,
            ).count()
        if count > 0:
            overdue_badge.set_text(str(count))
            overdue_badge.set_visibility(True)
        else:
            overdue_badge.set_visibility(False)

    _refresh_overdue_badge()
    ui.timer(10.0, _refresh_overdue_badge)

    def _on_tab_change(e):
        # Finanzen-Tab bei jedem Wechsel neu aufbauen, damit das Layout
        # korrekt gerendert wird (NiceGUI/Quasar Tab-Panel Initialisierungsproblem).
        val = e.args[0] if isinstance(e.args, list) else e.args
        if val == "Finanzen":
            finances_refresh()

    tabs.on("update:model-value", _on_tab_change)


# Register auth + settings pages (must be called at module level)
register_select_user_page()
register_login_page()
register_register_page()
register_forgot_password_page()
register_reset_password_page()
register_settings_page()


if __name__ in {"__main__", "__mp_main__"}:
    init_db()
    seed_db()
    ui.run(
        title="WG-Planner",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        storage_secret=os.environ.get("STORAGE_SECRET", "wg-planner-secret-key-2026"),
        show=False,
    )
