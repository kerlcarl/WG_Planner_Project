from datetime import datetime

from nicegui import app, ui

from models import EinkaufsItem, MitbewohnerDB, Post, Reaction
from services import (
    add_post,
    add_shopping_item,
    delete_bought_items,
    delete_post,
    delete_shopping_item,
    get_session,
    toggle_post_important,
    toggle_reaction,
    toggle_shopping_item,
)

_BLOG_PALETTE = [
    "#7c3aed", "#6d28d9", "#5b21b6", "#4c1d95",
    "#8b5cf6", "#6366f1", "#4f46e5", "#7e22ce",
]


def _blog_color(name: str) -> str:
    return _BLOG_PALETTE[sum(ord(c) for c in name) % len(_BLOG_PALETTE)]


# current_user_id wird per app.storage pro Verbindung gelesen – kein Parameter nötig.
def render_collab_tab(container):
    _timers: list = []

    def _build():
        for t in _timers:
            t.cancel()
        _timers.clear()
        container.clear()

        # User-ID frisch aus der Session lesen (pro Verbindung eindeutig)
        current_user_id = app.storage.user.get("user_id")

        with get_session() as sess:
            users = sess.query(MitbewohnerDB).order_by(MitbewohnerDB.name).all()
            users_dict = {u.id: u.name for u in users}

        with container:
            # ── Hero ────────────────────────────────────────────────────────────
            with ui.element("div").style(
                "background: linear-gradient(135deg, #0891b2 0%, #0c6c85 55%, #164e63 100%); "
                "border-radius: 20px; padding: 28px 32px; margin-bottom: 24px; "
                "box-shadow: 0 4px 24px rgba(8,145,178,0.22)"
            ):
                with ui.row().classes("items-center gap-4"):
                    with ui.element("div").style(
                        "background: rgba(255,255,255,0.18); border-radius: 16px; "
                        "width: 56px; height: 56px; display: flex; align-items: center; "
                        "justify-content: center; flex-shrink: 0"
                    ):
                        ui.icon("groups").style("color: white; font-size: 2rem")
                    with ui.column().classes("gap-0"):
                        ui.label("Kollaborations-Hub").style(
                            "font-size: 1.4rem; font-weight: 800; color: white; line-height: 1.2"
                        )
                        ui.label("WG-Blog & Echtzeit-Einkaufsliste").style(
                            "color: rgba(255,255,255,0.72); font-size: 0.85rem; margin-top: 4px"
                        )

            # 3-Spalten-Layout: Blog-Form | Feed (breit) | Einkaufsliste
            with ui.element("div").style(
                "display: grid; grid-template-columns: 1fr 2fr 1fr; gap: 20px; align-items: start"
            ).classes("wg-collab-grid"):

                # ── Spalte 1: Blog-Formular ───────────────────────────────────
                with ui.element("div"):
                    with ui.row().classes("items-center gap-3 mb-4"):
                        with ui.element("div").style(
                            "background: #7c3aed; border-radius: 10px; width: 34px; height: 34px; "
                            "display: flex; align-items: center; justify-content: center; flex-shrink: 0"
                        ):
                            ui.icon("campaign").style("color: white; font-size: 1.15rem")
                        with ui.column().classes("gap-0"):
                            ui.label("WG-Blog").style(
                                "font-size: 1.1rem; font-weight: 800; color: #1e1b4b; line-height: 1.2"
                            )
                            ui.label("Schwarzes Brett der WG").style(
                                "font-size: 0.78rem; color: #94a3b8"
                            )

                    with ui.card().classes("w-full").style(
                        "border-radius: 18px; border: 1.5px solid #ede9fe; "
                        "box-shadow: 0 4px 16px rgba(124,58,237,0.07); padding: 20px"
                    ):
                        with ui.row().classes("items-center gap-2 mb-3"):
                            ui.icon("edit_note").style("color: #7c3aed; font-size: 1.3rem")
                            ui.label("Neue Nachricht verfassen").style(
                                "font-weight: 700; color: #4c1d95; font-size: 0.95rem"
                            )
                        blog_content = ui.textarea(
                            "Inhalt", placeholder="Was möchtest du der WG mitteilen?"
                        ).classes("w-full mt-2").props("rows=5 outlined")
                        blog_important = ui.checkbox("Als wichtig markieren").classes("mt-1")
                        blog_important.style("color: #dc2626")
                        ui.button(
                            "Veröffentlichen", icon="send",
                            on_click=lambda: handle_post(),
                        ).props("unelevated").classes("w-full bg-violet-700 text-white mt-3").style(
                            "border-radius: 10px; font-weight: 600"
                        )

                # ── Spalte 2: Blog-Feed (breit) ───────────────────────────────
                with ui.element("div"):
                    with ui.row().classes("items-center gap-2 mb-4"):
                        ui.icon("forum").style("color: #7c3aed; font-size: 1.2rem")
                        ui.label("Nachrichten").style(
                            "font-size: 1.05rem; font-weight: 700; color: #1e1b4b"
                        )
                    blog_feed = ui.column().classes("w-full")

                # ── Spalte 3: Einkaufsliste ───────────────────────────────────
                with ui.element("div"):
                    with ui.row().classes("items-center justify-between mb-4 gap-2"):
                        with ui.row().classes("items-center gap-3"):
                            with ui.element("div").style(
                                "background: #059669; border-radius: 10px; width: 34px; height: 34px; "
                                "display: flex; align-items: center; justify-content: center; flex-shrink: 0"
                            ):
                                ui.icon("shopping_cart").style("color: white; font-size: 1.15rem")
                            with ui.column().classes("gap-0"):
                                ui.label("Einkaufsliste").style(
                                    "font-size: 1.1rem; font-weight: 800; color: #1e1b4b; line-height: 1.2"
                                )
                                ui.label("Echtzeit-Sync").style(
                                    "font-size: 0.78rem; color: #94a3b8"
                                )
                        sync_label = ui.label("").style(
                            "font-size: 0.68rem; color: #94a3b8; background: #f1f5f9; "
                            "padding: 3px 10px; border-radius: 999px; font-family: monospace"
                        )

                    with ui.card().classes("w-full mb-4").style(
                        "border-radius: 18px; border: 1.5px solid #d1fae5; "
                        "box-shadow: 0 4px 16px rgba(5,150,105,0.07); padding: 20px"
                    ):
                        with ui.row().classes("items-center gap-2 mb-3"):
                            ui.icon("add_shopping_cart").style("color: #059669; font-size: 1.3rem")
                            ui.label("Artikel hinzufügen").style(
                                "font-weight: 700; color: #065f46; font-size: 0.95rem"
                            )
                        shop_name = ui.input("Artikel *", placeholder="z. B. Milch").classes("w-full")
                        with ui.row().classes("w-full gap-2 mt-2"):
                            shop_menge = ui.input("Menge", placeholder="z. B. 2").classes("flex-1")
                            shop_einheit = ui.input("Einheit", placeholder="z. B. Liter").classes("flex-1")
                        shop_name.on("keydown.enter", lambda: handle_add_item())
                        ui.button(
                            "Hinzufügen", icon="add",
                            on_click=lambda: handle_add_item(),
                        ).props("unelevated").classes("w-full bg-emerald-600 text-white mt-3").style(
                            "border-radius: 10px; font-weight: 600"
                        )

                    shop_list = ui.column().classes("w-full")

        # ── Refresh-Funktionen ───────────────────────────────────────────────

        _REACTION_EMOJIS = ["👍", "❤️", "😂", "😮", "😢"]

        def _react(post_id: int, emoji: str):
            toggle_reaction(current_user_id, post_id, emoji)
            refresh_blog()

        def refresh_blog():
            blog_feed.clear()
            with get_session() as sess:
                posts = sess.query(Post).order_by(Post.created_at.desc()).all()
                post_ids = [p.id for p in posts]

                reactor_names: dict[int, dict[str, list[str]]] = {}
                user_emoji_by_post: dict[int, str] = {}
                if post_ids:
                    for r in sess.query(Reaction).filter(Reaction.post_id.in_(post_ids)).all():
                        name = users_dict.get(r.user_id, "?")
                        reactor_names.setdefault(r.post_id, {}).setdefault(r.emoji, []).append(name)
                        if r.user_id == current_user_id:
                            user_emoji_by_post[r.post_id] = r.emoji

                rows = [
                    {
                        "id": p.id,
                        "content": p.content,
                        "is_important": p.is_important,
                        "created_at": p.created_at,
                        "author_name": p.author.name if p.author else "Unbekannt",
                        "reactor_names": reactor_names.get(p.id, {}),
                        "my_emoji": user_emoji_by_post.get(p.id),
                    }
                    for p in posts
                ]

            with blog_feed:
                if not rows:
                    with ui.element("div").style(
                        "text-align: center; padding: 40px 20px; background: #faf5ff; "
                        "border-radius: 16px; border: 2px dashed #ddd6fe"
                    ):
                        ui.icon("forum").style("color: #c4b5fd; font-size: 3.5rem")
                        ui.label("Noch keine Nachrichten").style(
                            "color: #8b5cf6; font-weight: 600; margin-top: 10px"
                        )
                        ui.label("Verfasse oben den ersten WG-Beitrag!").style(
                            "color: #c4b5fd; font-size: 0.82rem; margin-top: 4px"
                        )
                    return

                for row in rows:
                    imp = row["is_important"]
                    author_name = row["author_name"]
                    ts = row["created_at"].strftime("%d.%m.%Y · %H:%M") if row["created_at"] else ""
                    post_id = row["id"]
                    color = _blog_color(author_name)
                    rxn_names = row["reactor_names"]
                    my_emoji = row["my_emoji"]

                    with ui.card().classes("w-full mb-3").style(
                        ("border-radius: 14px; border-left: 5px solid #dc2626; background: #fff5f5; "
                         if imp else
                         "border-radius: 14px; border-left: 5px solid #ede9fe; background: white; ")
                        + "padding: 0; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.05)"
                    ):
                        with ui.element("div").style("padding: 14px 16px"):
                            with ui.row().classes("w-full items-start justify-between gap-2 flex-wrap"):
                                with ui.row().classes("items-center gap-3"):
                                    ui.html(
                                        f'<div style="background:{color};border-radius:50%;'
                                        f'width:38px;height:38px;display:flex;align-items:center;'
                                        f'justify-content:center;color:white;font-weight:800;'
                                        f'font-size:0.95rem;flex-shrink:0">'
                                        f'{author_name[0].upper()}</div>'
                                    )
                                    with ui.column().classes("gap-0"):
                                        with ui.row().classes("items-center gap-2 flex-wrap"):
                                            ui.label(author_name).style(
                                                "font-weight: 700; color: #1e1b4b; font-size: 0.9rem"
                                            )
                                            if imp:
                                                ui.label("WICHTIG").style(
                                                    "background: #dc2626; color: white; "
                                                    "border-radius: 999px; font-size: 0.62rem; "
                                                    "font-weight: 800; padding: 2px 8px"
                                                )
                                        ui.label(ts).style("font-size: 0.72rem; color: #94a3b8")
                                with ui.row().classes("gap-1 flex-shrink-0"):
                                    ui.button(
                                        icon="star" if imp else "star_outline",
                                        on_click=lambda pid=post_id: (
                                            toggle_post_important(pid), refresh_blog()
                                        ),
                                    ).props("flat round dense").style(
                                        "color: #dc2626" if imp else "color: #d4d4d4"
                                    )
                                    ui.button(
                                        icon="delete",
                                        on_click=lambda pid=post_id: (
                                            delete_post(pid), refresh_blog()
                                        ),
                                    ).props("flat round dense").style("color: #ef4444")

                            ui.label(row["content"]).style(
                                "color: #374151; font-size: 0.88rem; margin-top: 10px; "
                                "white-space: pre-wrap; word-break: break-word; line-height: 1.55"
                            )

                            # ── Reaktions-Badges ────────────────────────────────
                            active_rxns = {e: names for e, names in rxn_names.items() if names}
                            if active_rxns:
                                with ui.row().classes("flex-wrap gap-2").style("margin-top: 10px"):
                                    for emoji, names in active_rxns.items():
                                        is_mine = (my_emoji == emoji)
                                        badge = ui.element("div").classes("rx-badge-anim").style(
                                            "display: inline-flex; align-items: center; gap: 5px; "
                                            "border-radius: 999px; padding: 4px 12px; "
                                            "font-size: 0.88rem; cursor: default; user-select: none; "
                                            + (
                                                "background: #ede9fe; border: 1.5px solid #c4b5fd; "
                                                "color: #7c3aed; font-weight: 700;"
                                                if is_mine else
                                                "background: #f1f5f9; border: 1.5px solid #e2e8f0; "
                                                "color: #475569;"
                                            )
                                        )
                                        with badge:
                                            ui.label(f"{emoji}  {len(names)}").style(
                                                "line-height: 1.4; font-size: 0.88rem"
                                            )
                                        badge.tooltip(", ".join(names))

                            # ── Emoji-Picker ─────────────────────────────────────
                            with ui.row().classes("flex-wrap gap-1").style("margin-top: 8px"):
                                for emoji in _REACTION_EMOJIS:
                                    is_mine = (my_emoji == emoji)
                                    ui.button(
                                        emoji,
                                        on_click=lambda pid=post_id, e=emoji: _react(pid, e),
                                    ).props("flat dense no-caps").style(
                                        "border-radius: 999px; padding: 1px 8px; font-size: 0.9rem; "
                                        "min-width: unset; transition: all 0.15s ease; "
                                        + (
                                            "background: #ede9fe; border: 1.5px solid #c4b5fd; "
                                            "color: #7c3aed; opacity: 1;"
                                            if is_mine else
                                            "background: transparent; border: 1.5px solid #e8e8e8; "
                                            "color: #94a3b8; opacity: 0.8;"
                                        )
                                    )

        def _render_shop_row(row: dict, refresh_fn):
            is_bought = row["is_bought"]
            item_id = row["id"]
            author_name = row["author_name"]
            parts = [row["name"]]
            if row["menge"] or row["einheit"]:
                qty = " ".join(p for p in [row["menge"], row["einheit"]] if p)
                parts.append(qty)
            label = " · ".join(parts)

            with ui.card().classes("w-full mb-2").style(
                "border-radius: 12px; padding: 0; overflow: hidden; "
                + ("background: #f8fafc; box-shadow: none;"
                   if is_bought else
                   "background: white; box-shadow: 0 2px 8px rgba(5,150,105,0.07);")
            ):
                with ui.row().classes("w-full items-center p-3 gap-2"):
                    ui.checkbox(
                        value=is_bought,
                        on_change=lambda e, iid=item_id: (
                            toggle_shopping_item(iid, e.value), refresh_fn()
                        ),
                    ).style("flex-shrink: 0; color: #059669")
                    with ui.column().classes("flex-grow gap-0"):
                        ui.label(label).style(
                            "font-size: 0.88rem; "
                            + ("font-weight: 500; color: #94a3b8; text-decoration: line-through"
                               if is_bought else
                               "font-weight: 700; color: #1e1b4b")
                        )
                        ui.label(f"von {author_name}").style(
                            "font-size: 0.7rem; color: #94a3b8; margin-top: 1px"
                        )
                    ui.button(
                        icon="close",
                        on_click=lambda iid=item_id: (
                            delete_shopping_item(iid), refresh_fn()
                        ),
                    ).props("flat round dense").style("color: #d1d5db; flex-shrink: 0")

        def refresh_shop():
            shop_list.clear()
            sync_label.text = f"⟳ {datetime.now().strftime('%H:%M:%S')}"
            with get_session() as sess:
                items = sess.query(EinkaufsItem).order_by(EinkaufsItem.created_at.asc()).all()
                rows = [
                    {
                        "id": i.id,
                        "name": i.name,
                        "menge": i.menge,
                        "einheit": i.einheit,
                        "is_bought": i.is_bought,
                        "author_name": i.author.name if i.author else "?",
                    }
                    for i in items
                ]

            active = [r for r in rows if not r["is_bought"]]
            bought = [r for r in rows if r["is_bought"]]

            with shop_list:
                if not rows:
                    with ui.element("div").style(
                        "text-align: center; padding: 40px 20px; background: #f0fdf4; "
                        "border-radius: 16px; border: 2px dashed #a7f3d0"
                    ):
                        ui.icon("shopping_basket").style("color: #6ee7b7; font-size: 3.5rem")
                        ui.label("Einkaufsliste ist leer").style(
                            "color: #10b981; font-weight: 600; margin-top: 10px"
                        )
                        ui.label("Füge oben den ersten Artikel hinzu!").style(
                            "color: #6ee7b7; font-size: 0.82rem; margin-top: 4px"
                        )
                    return

                if active:
                    ui.label(f"ZU KAUFEN  ({len(active)})").style(
                        "font-size: 0.72rem; font-weight: 700; color: #059669; "
                        "letter-spacing: 0.06em; margin-bottom: 8px"
                    )
                    for row in active:
                        _render_shop_row(row, refresh_shop)

                if bought:
                    if active:
                        ui.separator().classes("my-4")
                    ui.label(f"ERLEDIGT  ({len(bought)})").style(
                        "font-size: 0.72rem; font-weight: 700; color: #94a3b8; "
                        "letter-spacing: 0.06em; margin-bottom: 8px"
                    )
                    for row in bought:
                        _render_shop_row(row, refresh_shop)
                    ui.button(
                        f"Alle {len(bought)} Erledigten löschen",
                        icon="cleaning_services",
                        on_click=lambda: (
                            delete_bought_items(),
                            ui.notify("Erledigte Artikel gelöscht", color="positive"),
                            refresh_shop(),
                        ),
                    ).classes("w-full mt-4").style(
                        "background: #f1f5f9; color: #64748b; "
                        "border-radius: 10px; font-weight: 600"
                    )

        # ── Event-Handler ────────────────────────────────────────────────────

        def handle_post():
            if not blog_content.value or not blog_content.value.strip():
                ui.notify("Bitte einen Text eingeben", color="warning")
                return
            add_post(current_user_id, blog_content.value, blog_important.value)
            ui.notify("Nachricht veröffentlicht", color="positive")
            blog_content.value = ""
            blog_important.value = False
            refresh_blog()

        def handle_add_item():
            if not shop_name.value or not shop_name.value.strip():
                ui.notify("Bitte einen Artikelnamen eingeben", color="warning")
                return
            add_shopping_item(shop_name.value, shop_menge.value, shop_einheit.value, current_user_id)
            ui.notify(f'"{shop_name.value}" hinzugefügt', color="positive")
            shop_name.value = ""
            shop_menge.value = ""
            shop_einheit.value = ""
            refresh_shop()

        refresh_blog()
        refresh_shop()

        _timers.append(ui.timer(2.0, refresh_shop))
        _timers.append(ui.timer(5.0, refresh_blog))

    _build()
    return _build
