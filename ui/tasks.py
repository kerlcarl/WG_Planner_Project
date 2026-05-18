import json
from datetime import datetime

from nicegui import ui
from sqlalchemy.orm import joinedload

from models import MitbewohnerDB, Task
from services import delete_task, get_session, save_task, update_task, update_task_status


# Rendert den Aufgaben-Tab und liefert eine Refresh-Funktion zurueck.
def render_tasks_tab(container, current_user_id: int = None):
    _form_active = {"value": False}
    _dialog_open = {"value": False}

    # Baut den kompletten Tab aus aktuellen DB-Daten neu auf.
    def refresh():
        if _form_active["value"] or _dialog_open["value"]:
            return
        container.clear()
        with get_session() as session:
            # joinedload verhindert DetachedInstanceError nach Session-Close.
            tasks = session.query(Task).options(joinedload(Task.assigned_to)).all()
            users = session.query(MitbewohnerDB).all()
        # Nur Aufgaben mit Deadline im Kalender markieren.
        event_days = list(dict.fromkeys(
            task.due_date.strftime("%Y/%m/%d") for task in tasks if task.due_date and not task.is_done
        ))
        # Sortierung: Aufgaben mit Deadline zuerst (aufsteigend), danach ohne Datum
        open_tasks = sorted(
            [t for t in tasks if not t.is_done],
            key=lambda t: (t.due_date is None, t.due_date),
        )
        done_tasks = sorted(
            [t for t in tasks if t.is_done],
            key=lambda t: (t.due_date is None, t.due_date),
        )
        tasks_with_deadline = sorted(
            [t for t in tasks if t.due_date and not t.is_done],
            key=lambda t: t.due_date,
        )
        _WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
        now = datetime.now()
        today_str = now.strftime("%Y/%m/%d")
        datum_label = f"{_WOCHENTAGE[now.weekday()]}, {now.strftime('%d.%m.%Y')}"
        uhrzeit_label = now.strftime("%H:%M")
        # Tooltip-Inhalt: Titel + Zuständige*r für jeden Tag
        task_map = {}
        user_color = {u.id: (u.color or "#336699") for u in users}
        for t in tasks_with_deadline:
            assigned = t.assigned_to.name if t.assigned_to else "–"
            task_map.setdefault(t.due_date.strftime("%Y/%m/%d"), []).append(
                f"{t.title} ({assigned})"
            )
        # Farbpunkte: ein Punkt pro eindeutigem Nutzer pro Tag
        color_map: dict[str, list[str]] = {}
        _seen_uid: dict[str, set] = {}
        for t in tasks_with_deadline:
            day_str = t.due_date.strftime("%Y/%m/%d")
            uid = t.assigned_to_id
            _seen_uid.setdefault(day_str, set())
            if uid in _seen_uid[day_str]:
                continue
            _seen_uid[day_str].add(uid)
            color_map.setdefault(day_str, []).append(
                user_color.get(uid, "#f97316") if uid else "#f97316"
            )
        # Quasar event-color nutzt bg-{name}-Klassen, keine Hex-Werte.
        # Daher eigene CSS-Klassen definieren und diese als Farbnamen übergeben.
        _css_rules = " ".join(
            f".bg-wg-uc-{u.id}{{background:{u.color or '#336699'}!important;}}"
            for u in users
        )
        date_to_class: dict[str, str] = {}
        for t in tasks_with_deadline:
            day_str = t.due_date.strftime("%Y/%m/%d")
            if day_str not in date_to_class:
                uid = t.assigned_to_id
                date_to_class[day_str] = f"wg-uc-{uid}" if uid else "orange"

        with container:
            # Hero-Banner
            with ui.element("div").style(
                "background: linear-gradient(135deg, #fff7ed 0%, #fed7aa 60%, #fdba74 100%); "
                "border-radius: 20px; padding: 28px 32px; margin-bottom: 20px; "
                "box-shadow: 0 4px 20px rgba(249,115,22,0.16)"
            ):
                with ui.row().classes("w-full items-center justify-between flex-wrap gap-4"):
                    with ui.row().classes("items-center gap-4"):
                        with ui.element("div").style(
                            "background: #f97316; border-radius: 16px; width: 56px; height: 56px; "
                            "display: flex; align-items: center; justify-content: center; flex-shrink: 0"
                        ):
                            ui.icon("task_alt").style("color: white; font-size: 2rem")
                        with ui.column().classes("gap-0"):
                            ui.label("Ämtli & Kalender").style(
                                "font-size: 1.4rem; font-weight: 800; color: #9a3412; line-height: 1.2"
                            )
                            ui.label("Aufgaben verwalten und den Überblick behalten").style(
                                "color: #f97316; font-size: 0.85rem; margin-top: 4px"
                            )
                    with ui.row().classes("gap-6"):
                        with ui.column().classes("items-end gap-0"):
                            ui.label(str(len(open_tasks))).style(
                                "font-size: 1.9rem; font-weight: 900; color: #9a3412; line-height: 1"
                            )
                            ui.label("Offen").style("color: #f97316; font-size: 0.78rem; margin-top: 2px")
                        with ui.column().classes("items-end gap-0"):
                            ui.label(str(len(done_tasks))).style(
                                "font-size: 1.9rem; font-weight: 900; color: #9a3412; line-height: 1"
                            )
                            ui.label("Erledigt").style("color: #f97316; font-size: 0.78rem; margin-top: 2px")

            # ── Ämtli-Bearbeiten-Dialog ───────────────────────────────────────
            _edit_task_id = {"value": None}

            with ui.dialog().props("persistent") as edit_task_dialog, ui.card().classes(
                "w-[38rem] max-w-[95vw] rounded-2xl shadow-xl"
            ):
                with ui.row().classes("w-full items-center justify-between p-5 pb-2"):
                    with ui.column().classes("gap-0"):
                        ui.label("Ämtli bearbeiten").classes("text-h6 font-bold text-slate-900")
                        ui.label("Titel, Zuständigkeit und Deadline anpassen.").classes("text-sm text-slate-500")
                    ui.button(
                        icon="close",
                        on_click=lambda: (_dialog_open.update(value=False), edit_task_dialog.close()),
                    ).props("flat round")

                with ui.column().classes("w-full gap-4 px-5 pb-5 pt-3"):
                    edit_title = ui.input("Titel").classes("w-full")
                    edit_who = ui.select(
                        {user.id: user.name for user in users},
                        label="Zuständige*r Mitbewohner*in",
                    ).classes("w-full")

                    with ui.input("Deadline (optional)", placeholder="TT.MM.JJJJ") as edit_deadline:
                        with ui.menu().props("no-parent-event") as edit_deadline_menu:
                            with ui.date().props(
                                f'mask="DD.MM.YYYY" :options="d => d >= \'{today_str}\'"'
                            ).bind_value(edit_deadline):
                                with ui.row().classes("justify-end"):
                                    ui.button("OK", on_click=edit_deadline_menu.close).props("flat dense")
                        with edit_deadline.add_slot("append"):
                            ui.icon("calendar_month").classes("cursor-pointer").on(
                                "click", edit_deadline_menu.open
                            )
                    edit_deadline.classes("w-full")

                    def handle_edit_task_save():
                        err = update_task(_edit_task_id["value"], edit_title.value, edit_who.value, edit_deadline.value)
                        if err:
                            ui.notify(err, color="warning")
                            return
                        ui.notify("Ämtli aktualisiert", color="positive")
                        _dialog_open["value"] = False
                        edit_task_dialog.close()
                        refresh()

                    with ui.row().classes("w-full justify-end gap-2 pt-2"):
                        ui.button(
                            "Abbrechen",
                            on_click=lambda: (_dialog_open.update(value=False), edit_task_dialog.close()),
                        ).props("flat")
                        ui.button("Speichern", on_click=handle_edit_task_save).style(
                            "background: #f97316; color: white; border-radius: 10px; font-weight: 600"
                        )

            def _open_edit_task_dialog(task):
                _edit_task_id["value"] = task.id
                edit_title.value = task.title
                edit_who.value = task.assigned_to_id
                edit_deadline.value = task.due_date.strftime("%d.%m.%Y") if task.due_date else ""
                _dialog_open["value"] = True
                edit_task_dialog.open()

            # 3-Spalten-Layout
            with ui.element("div").classes("wg-grid-3"):

                # ── Spalte 1: Neues Ämtli ────────────────────────────────────
                with ui.element("div"):
                    with ui.card().classes("w-full").style(
                        "border-radius: 18px; box-shadow: 0 4px 20px rgba(249,115,22,0.10); "
                        "border: 1.5px solid #fed7aa; padding: 22px"
                    ):
                        with ui.row().classes("items-center gap-3 mb-3"):
                            ui.icon("add_task").style("color: #f97316; font-size: 1.4rem")
                            ui.label("Neues Ämtli erstellen").style(
                                "font-size: 1rem; font-weight: 700; color: #9a3412"
                            )

                        title = ui.input(
                            "Titel", placeholder="z.B. Küche putzen",
                            on_change=lambda e: _form_active.update(value=bool(e.value.strip())),
                        ).classes("w-full")
                        who = ui.select(
                            {user.id: user.name for user in users},
                            label="Zuständige*r Mitbewohner*in",
                            value=current_user_id,
                        ).classes("w-full mt-2")

                        with ui.input("Deadline (optional)", placeholder="TT.MM.JJJJ") as deadline:
                            with ui.menu().props("no-parent-event") as deadline_menu:
                                with ui.date().props(
                                    f'mask="DD.MM.YYYY" :options="d => d >= \'{today_str}\'"'
                                ).bind_value(deadline):
                                    with ui.row().classes("justify-end"):
                                        ui.button("OK", on_click=deadline_menu.close).props("flat dense")
                            with deadline.add_slot("append"):
                                ui.icon("calendar_month").classes("cursor-pointer").on(
                                    "click", deadline_menu.open
                                )
                        deadline.classes("w-full mt-2")

                        def handle_task():
                            err = save_task(title.value, who.value, deadline.value)
                            if err:
                                ui.notify(err, color="warning")
                                return
                            ui.notify("Neues Ämtli erstellt", color="positive")
                            _form_active["value"] = False
                            refresh()

                        title.on("keydown.enter", handle_task)
                        ui.button("Ämtli erstellen", icon="add", on_click=handle_task).classes(
                            "w-full bg-orange-500 text-white mt-3"
                        ).style("border-radius: 10px; font-weight: 600")

                # ── Spalte 2: Kalender ───────────────────────────────────────
                with ui.element("div"):
                    with ui.card().classes("w-full shadow-md rounded-xl bg-white"):
                        with ui.row().classes(
                            "w-full items-center justify-between px-4 pt-4 pb-1 flex-wrap gap-2"
                        ):
                            with ui.row().classes("items-center gap-2"):
                                ui.icon("calendar_month").style("color: #f97316; font-size: 1.3rem")
                                with ui.column().classes("gap-0"):
                                    ui.label("Ämtli-Kalender").style(
                                        "font-size: 1.05rem; font-weight: 700; color: #1e1b4b"
                                    )
                                    ui.label("Punkt = Zuständige*r · Grau = vergangen · Hover/Klick").style(
                                        "font-size: 0.73rem; color: #94a3b8"
                                    )
                            with ui.column().classes("items-end gap-0"):
                                ui.label(datum_label).style(
                                    "font-size: 0.88rem; font-weight: 700; color: #9a3412"
                                )
                                ui.label(uhrzeit_label).style(
                                    "font-size: 1.1rem; font-weight: 800; color: #f97316"
                                )
                        with ui.element("div").classes("px-4 pb-4"):
                            _dtc = json.dumps(date_to_class, separators=(',', ':'))
                            ui.date().props(
                                f':events=\'{json.dumps(event_days)}\' '
                                f':event-color=\'(d) => ({_dtc})[d] || "orange"\' '
                                f':options="d => d >= \'{today_str}\'"'
                            ).classes("w-full wg-tasks-calendar")
                        # Farblegende: wer hat welche Farbe
                        with ui.element("div").classes("px-4 pb-3 pt-2").style(
                            "border-top: 1px solid #f1f5f9"
                        ):
                            with ui.row().classes("items-center gap-4 flex-wrap"):
                                for u in users:
                                    _col = u.color or "#336699"
                                    with ui.row().classes("items-center gap-1"):
                                        ui.element("div").style(
                                            f"width:11px;height:11px;border-radius:50%;"
                                            f"background:{_col};flex-shrink:0;"
                                            f"box-shadow:0 1px 3px rgba(0,0,0,0.25)"
                                        )
                                        ui.label(u.name).style(
                                            "font-size:0.75rem;color:#475569;font-weight:600"
                                        )

                # ── Spalte 3: Aufgabenliste ──────────────────────────────────
                with ui.element("div"):
                    with ui.row().classes("items-center gap-2 mb-3"):
                        ui.icon("pending_actions").style("color: #f97316; font-size: 1.2rem")
                        ui.label("Aufgaben").style(
                            "font-size: 1.05rem; font-weight: 700; color: #1e1b4b"
                        )
                        ui.label(str(len(open_tasks))).style(
                            "background: #f97316; color: white; border-radius: 999px; "
                            "font-size: 0.78rem; font-weight: 700; padding: 2px 9px"
                        )

                    def _render_task_card(task, is_done):
                        card_style = (
                            "border-radius: 16px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); "
                            "border-left: 5px solid #86efac; background: #f0fdf4; "
                            "padding: 0; overflow: hidden; margin-bottom: 10px"
                            if is_done else
                            "border-radius: 16px; box-shadow: 0 2px 10px rgba(249,115,22,0.10); "
                            "border-left: 5px solid #f97316; background: white; "
                            "padding: 0; overflow: hidden; margin-bottom: 10px"
                        )
                        with ui.card().classes("w-full").style(card_style):
                            with ui.row().classes("w-full items-center p-3 gap-3"):
                                ui.checkbox(
                                    value=is_done,
                                    on_change=lambda event, t=task: (
                                        update_task_status(t.id, event.value), refresh()
                                    ),
                                ).style("flex-shrink: 0")
                                with ui.column().classes("flex-grow gap-0"):
                                    label_style = (
                                        "font-weight: 600; color: #6b7280; text-decoration: line-through"
                                        if is_done else
                                        "font-weight: 700; color: #1e1b4b"
                                    )
                                    ui.label(task.title).style(label_style)
                                    assigned_name = task.assigned_to.name if task.assigned_to else "Niemand"
                                    meta_parts = [f"Zuständig: {assigned_name}"]
                                    if task.due_date:
                                        meta_parts.append(f"Deadline: {task.due_date.strftime('%d.%m.%Y')}")
                                    ui.label("  ·  ".join(meta_parts)).style(
                                        "font-size: 0.78rem; color: #94a3b8; margin-top: 2px"
                                    )
                                if not is_done:
                                    with ui.row().classes("gap-0"):
                                        ui.button(
                                            icon="edit",
                                            on_click=lambda t=task: _open_edit_task_dialog(t),
                                        ).props("flat round color=orange")
                                        ui.button(
                                            icon="delete",
                                            on_click=lambda t=task: (
                                                delete_task(t.id),
                                                ui.notify("Ämtli gelöscht", color="negative"),
                                                refresh(),
                                            ),
                                        ).props("flat round color=red")

                    # Offene Aufgaben
                    if not open_tasks:
                        with ui.element("div").style(
                            "text-align: center; padding: 48px 20px; background: #fff7ed; "
                            "border-radius: 18px; border: 2px dashed #fed7aa"
                        ):
                            ui.icon("task_alt").style("color: #fdba74; font-size: 3.5rem")
                            ui.label("Keine offenen Ämtli vorhanden.").style(
                                "color: #fb923c; margin-top: 10px; font-weight: 600"
                            )
                            ui.label("Erstelle links dein erstes Ämtli!").style(
                                "color: #fdba74; font-size: 0.85rem; margin-top: 4px"
                            )
                    else:
                        for task in open_tasks:
                            _render_task_card(task, False)

                    # Erledigte Aufgaben
                    if done_tasks:
                        ui.separator().classes("my-4")
                        with ui.row().classes("items-center gap-2 mb-3"):
                            ui.icon("check_circle").style("color: #16a34a; font-size: 1.2rem")
                            ui.label("Erledigt").style(
                                "font-size: 1.05rem; font-weight: 700; color: #16a34a"
                            )
                            ui.label(str(len(done_tasks))).style(
                                "background: #16a34a; color: white; border-radius: 999px; "
                                "font-size: 0.78rem; font-weight: 700; padding: 2px 9px"
                            )
                        for task in done_tasks:
                            _render_task_card(task, True)

        # Kalender-Interaktion: farbige Nutzerpunkte, Hover-Tooltip, Klick-Panel
        _tm = json.dumps(task_map)
        _cm = json.dumps(color_map)
        _init_ym = json.dumps({"y": now.year, "m": now.month})
        ui.run_javascript(f"""(function(){{
  var s=document.getElementById('_wgUserColors');if(!s){{s=document.createElement('style');s.id='_wgUserColors';document.head.appendChild(s);}}s.textContent='{_css_rules}';
  var TM={_tm};
  var CM={_cm};
  var INIT_YM={_init_ym};
  var MO={{'January':1,'February':2,'March':3,'April':4,'May':5,'June':6,'July':7,'August':8,'September':9,'October':10,'November':11,'December':12,'Januar':1,'Februar':2,'März':3,'April':4,'Mai':5,'Juni':6,'Juli':7,'August':8,'September':9,'Oktober':10,'November':11,'Dezember':12}};
  var tip=document.getElementById('_wgTip');
  if(!tip){{tip=document.createElement('div');tip.id='_wgTip';tip.style.cssText='position:fixed;z-index:9999;background:#1e1b4b;color:white;padding:8px 14px;border-radius:12px;font-size:0.82rem;pointer-events:none;display:none;box-shadow:0 4px 20px rgba(0,0,0,0.3);line-height:1.7;max-width:260px;';document.body.appendChild(tip);}}
  function getYM(){{
    var cal=document.querySelector('.wg-tasks-calendar');
    if(!cal)return null;
    var y=null,m=null;
    function scanWords(root){{
      root.querySelectorAll('button,span,div').forEach(function(el){{
        if(el.children.length)return;
        (el.textContent||'').trim().split(/\\s+/).forEach(function(w){{
          if(!m&&MO[w])m=MO[w];
          var n=parseInt(w);
          if(!y&&!isNaN(n)&&n>=2020&&n<=2040)y=n;
        }});
      }});
    }}
    var nav=cal.querySelector('.q-date__navigation');
    if(nav)scanWords(nav);
    if(!m||!y){{
      var grid=cal.querySelector('.q-date__calendar-days');
      cal.querySelectorAll('button,span,div').forEach(function(el){{
        if(grid&&grid.contains(el))return;
        if(el.children.length)return;
        (el.textContent||'').trim().split(/\\s+/).forEach(function(w){{
          if(!m&&MO[w])m=MO[w];
          var n=parseInt(w);
          if(!y&&!isNaN(n)&&n>=2020&&n<=2040)y=n;
        }});
      }});
    }}
    return(m&&y)?{{y:y,m:m}}:null;
  }}
  function ensurePanel(){{var p=document.getElementById('_wgSelPanel');if(!p){{var w=document.querySelector('.wg-tasks-calendar');if(!w)return null;p=document.createElement('div');p.id='_wgSelPanel';p.style.cssText='display:none;background:#fff7ed;border-radius:12px;padding:12px 16px;margin-top:10px;border:2px solid #fed7aa;font-size:0.83rem;line-height:1.8;';w.parentNode.insertBefore(p,w.nextSibling);}}return p;}}
  function attach(){{
    var ym=getYM()||INIT_YM;
    var cal=document.querySelector('.wg-tasks-calendar .q-date__calendar-days');if(!cal)return;
    ensurePanel();
    cal.querySelectorAll('.q-date__calendar-item--event').forEach(function(item){{
      var btn=item.querySelector('button');if(!btn)return;
      var sp=btn.querySelector('span.block');if(!sp)return;
      var d=parseInt(sp.textContent.trim());if(isNaN(d))return;
      var ds=ym.y+'/'+String(ym.m).padStart(2,'0')+'/'+String(d).padStart(2,'0');
      var colors=CM[ds]||[];
      if(colors.length>1&&!item.dataset.wgDots){{item.dataset.wgDots='1';var ed=item.querySelector('.q-date__event');if(ed){{var n=colors.length,gap=6,so=-((n-1)*gap)/2;ed.style.transform='translateX(calc(-50% + '+so+'px))';for(var ci=1;ci<n;ci++){{var xd=document.createElement('div');xd.style.cssText='position:absolute;bottom:4px;width:4px;height:4px;border-radius:50%;left:50%;transform:translateX(calc(-50% + '+(so+ci*gap)+'px));background:'+colors[ci]+';pointer-events:none;border-radius:50%;';item.appendChild(xd);}}}}}}
      if(btn.dataset.wgH)return;btn.dataset.wgH='1';
      var tasks=TM[ds]||[];
      btn.addEventListener('mouseenter',function(e){{if(!tasks.length)return;tip.innerHTML='<b>'+String(d).padStart(2,'0')+'.'+String(ym.m).padStart(2,'0')+'.'+ym.y+'</b><br>'+tasks.map(function(t){{return '• '+t;}}).join('<br>');tip.style.display='block';tip.style.left=(e.clientX+16)+'px';tip.style.top=(e.clientY-8)+'px';}});
      btn.addEventListener('mousemove',function(e){{tip.style.left=(e.clientX+16)+'px';tip.style.top=(e.clientY-8)+'px';}});
      btn.addEventListener('mouseleave',function(){{tip.style.display='none';}});
      btn.addEventListener('click',function(){{
        tip.style.display='none';if(!tasks.length)return;
        var panel=document.getElementById('_wgSelPanel');if(!panel)return;
        document.querySelectorAll('.wg-tasks-calendar .wg-sel').forEach(function(b){{b.classList.remove('wg-sel');b.style.outline='';b.style.outlineOffset='';}});
        btn.classList.add('wg-sel');btn.style.outline='2px solid #f97316';btn.style.outlineOffset='2px';
        var dh=colors.map(function(c){{return '<span style="width:9px;height:9px;border-radius:50%;background:'+c+';display:inline-block;margin-left:4px;vertical-align:middle;"></span>';}}).join('');
        var dateStr=String(d).padStart(2,'0')+'.'+String(ym.m).padStart(2,'0')+'.'+ym.y;
        panel.innerHTML='<div style="font-weight:700;color:#9a3412;margin-bottom:8px;">'+dateStr+dh+'</div>'+tasks.map(function(t){{return '<div style="padding:2px 0 2px 8px;color:#1e1b4b;border-left:3px solid #f97316;margin-bottom:4px;">'+t+'</div>';}}).join('');
        panel.style.display='block';
      }});
    }});
    cal.querySelectorAll('.q-date__calendar-item:not(.q-date__calendar-item--event) button').forEach(function(btn){{
      if(btn.dataset.wgNE)return;btn.dataset.wgNE='1';
      btn.addEventListener('click',function(){{
        var panel=document.getElementById('_wgSelPanel');if(panel)panel.style.display='none';
        document.querySelectorAll('.wg-tasks-calendar .wg-sel').forEach(function(b){{b.classList.remove('wg-sel');b.style.outline='';}});
      }});
    }});
  }}
  setTimeout(attach,600);
  var el=document.querySelector('.wg-tasks-calendar');
  if(el){{if(window._wgCalObs)window._wgCalObs.disconnect();window._wgCalObs=new MutationObserver(function(){{var p=document.getElementById('_wgSelPanel');if(p)p.style.display='none';document.querySelectorAll('.wg-tasks-calendar .wg-sel').forEach(function(b){{b.classList.remove('wg-sel');b.style.outline='';}});clearTimeout(window._wgCalT);window._wgCalT=setTimeout(attach,350);}});window._wgCalObs.observe(el,{{subtree:true,childList:true}});}}
}})();""")

    refresh()
    return refresh
