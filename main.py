from nicegui import ui

from models import init_db
from ui import render_collab_tab, render_finances_tab, render_tasks_tab, render_users_tab


# Baut die Startseite mit Header, Tabs und den drei Inhaltsbereichen.
@ui.page("/")
def main_page():
    ui.query("body").style("background-color: #f0f2f5")

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

    with ui.header().classes("bg-indigo-700 p-4 shadow-lg"):
        with ui.row().classes("w-full max-w-[1700px] mx-auto items-center px-2"):
            ui.label("WG-Planner").classes("text-h4 text-white font-bold")

    with ui.tabs().classes("w-full bg-white shadow-sm") as tabs:
        users_tab = ui.tab("Mitbewohner*innen", icon="people")
        finances_tab = ui.tab("Finanzen", icon="payments")
        tasks_tab = ui.tab("Ämtli & Kalender", icon="event")
        collab_tab = ui.tab("Kollaborations-Hub", icon="groups")

    # Tab-Inhalte werden in eigenen Containern gerendert.
    with ui.tab_panels(tabs, value=users_tab).classes("w-full max-w-[1700px] mx-auto bg-transparent p-4").props("animated"):
        with ui.tab_panel(users_tab).classes("px-0"):
            users_container = ui.column().classes("w-full")
        with ui.tab_panel(finances_tab).classes("px-0"):
            finances_container = ui.column().classes("w-full")
        with ui.tab_panel(tasks_tab).classes("px-0"):
            tasks_container = ui.column().classes("w-full")
        with ui.tab_panel(collab_tab).classes("px-0"):
            collab_container = ui.column().classes("w-full")

    # Renderer liefern Refresh-Funktionen zurueck, damit Daten neu geladen werden koennen.
    finances_refresh = render_finances_tab(finances_container)
    tasks_refresh = render_tasks_tab(tasks_container)
    collab_refresh = render_collab_tab(collab_container)
    render_users_tab(
        users_container,
        on_users_changed=lambda: (finances_refresh(), tasks_refresh(), collab_refresh()),
    )

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
