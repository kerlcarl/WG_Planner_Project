from nicegui import ui
from models import Expense, MitbewohnerDB, Session, Task, engine, Base
from datetime import datetime, timedelta

# --- Hilfsfunktionen ---
def get_session():
    return Session()

def calculate_balances() -> dict[int, float]:
    session = get_session()
    users = session.query(MitbewohnerDB).all()
    balances = {u.id: 0.0 for u in users}
    for expense in session.query(Expense).all():
        share = expense.calculate_share()
        for user in expense.participants:
            balances[user.id] -= share
        balances[expense.paid_by_id] += expense.amount
    session.close()
    return balances

# --- UI Render-Funktionen ---

def render_users_tab(container):
    # 1. Bereich zum Hinzufügen (fest oben)
    with ui.card().classes('w-full mb-4 p-4 shadow-md'):
        ui.label('Neue*n Mitbewohner*in hinzufügen').classes('text-h6 text-blue-700 font-bold')
        name_input = ui.input('Name')
        
        def handle_add():
            if name_input.value:
                add_user(name_input, refresh_list)
        
        name_input.on('keydown.enter', handle_add)
        ui.button('Hinzufügen', on_click=handle_add).classes('w-full bg-blue-600 text-white mt-2')
    
    # 2. Feste Überschrift für die Liste (steht immer an derselben Stelle)
    ui.label('Aktuelle Mitbewohner*innen').classes('text-h6 mt-4 mb-2 font-bold')
    
    # 3. Container NUR für die dynamischen Listeneinträge
    list_items_container = ui.column().classes('w-full')

    def refresh_list():
        list_items_container.clear()
        session = get_session()
        users = session.query(MitbewohnerDB).order_by(MitbewohnerDB.name).all()
        with list_items_container:
            if not users:
                ui.label('Noch keine Mitbewohner*innen vorhanden.').classes('text-gray-500 italic p-4')
            for user in users:
                with ui.card().classes('w-full border-l-4 border-blue-500 shadow-sm mb-2'):
                    with ui.row().classes('w-full items-center justify-between p-2'):
                        ui.label(user.name).classes('text-bold text-lg')
                        with ui.row().classes('gap-1'):
                            ui.button(icon='edit', on_click=lambda u=user: edit_user(u, refresh_list)).props('flat round')
                            ui.button(icon='delete', on_click=lambda u=user: delete_user(u, refresh_list)).props('flat round color=red')
        session.close()

    # Initiales Laden der Liste
    refresh_list()

def render_finances_tab(container):
    def refresh():
        container.clear()
        session = get_session()
        balances = calculate_balances()
        users = session.query(MitbewohnerDB).order_by(MitbewohnerDB.name).all()
        expenses = session.query(Expense).order_by(Expense.id.desc()).all()
        
        with container:
            with ui.expansion('Neue Ausgabe erfassen', icon='add_shopping_cart').classes('w-full bg-green-50 mb-4 shadow-sm'):
                desc = ui.input('Beschreibung')
                amt = ui.number('Betrag (CHF)', format='%.2f')
                cat = ui.input('Kategorie')
                u_map = {u.id: u.name for u in users}
                payer = ui.select(u_map, label='Bezahlt von')
                parts = ui.select(u_map, label='Beteiligte Mitbewohner*innen', multiple=True)
                
                def handle_save():
                    save_expense(desc, amt, cat, payer, parts, refresh)
                
                desc.on('keydown.enter', handle_save)
                ui.button('Speichern', on_click=handle_save).classes('bg-green-600 text-white w-full mt-2')

            ui.label('Kontostände').classes('text-h6 font-bold mb-2')
            for user in users:
                bal = balances.get(user.id, 0.0)
                color = 'text-green-700' if bal >= 0 else 'text-red-700'
                with ui.card().classes('w-full mb-2 shadow-sm border-l-4 border-green-500'):
                    with ui.row().classes('w-full justify-between items-center p-2'):
                        ui.label(user.name).classes('text-bold')
                        ui.label(f'CHF {bal:.2f}').classes(f'text-bold {color}')

            ui.label('Ausgabenverlauf').classes('text-h6 font-bold mt-6 mb-2')
            for exp in expenses:
                with ui.card().classes('w-full p-3 bg-white mb-2 shadow-sm'):
                    with ui.row().classes('w-full justify-between items-center'):
                        with ui.column():
                            ui.label(exp.description).classes('text-bold')
                            ui.label(f"Kategorie: {exp.category or 'Allgemein'}").classes('text-xs text-gray-500')
                        with ui.column().classes('items-end'):
                            ui.label(f"CHF {exp.amount:.2f}").classes('text-bold')
                            ui.label(f"Bezahlt von {exp.paid_by.name if exp.paid_by else 'Unbekannt'}").classes('text-xs')
                    ui.separator().classes('my-1')
                    ui.label(f"Beteiligt: {', '.join([p.name for p in exp.participants])}").classes('text-xs italic')

        session.close()
    refresh()

def render_tasks_tab(container):
    def refresh():
        container.clear()
        session = get_session()
        tasks = session.query(Task).all()
        users = session.query(MitbewohnerDB).all()
        event_days = [t.created_at.strftime('%Y-%m-%d') for t in tasks if t.created_at]

        with container:
            with ui.expansion('Neues Ämtli erstellen', icon='playlist_add').classes('w-full bg-orange-50 mb-4 shadow-sm'):
                title = ui.input('Titel')
                who = ui.select({u.id: u.name for u in users}, label='Zuständige*r Mitbewohner*in')
                
                def handle_task():
                    save_task(title, who, refresh)
                
                title.on('keydown.enter', handle_task)
                ui.button('Erstellen', on_click=handle_task).classes('bg-orange-500 text-white w-full mt-2')

            ui.label('Ämtli-Kalender').classes('text-h6 font-bold mb-2')
            ui.date().props(f'events={event_days} event-color="orange"').classes('w-full mb-4')

            ui.label('Offene Aufgaben').classes('text-h6 font-bold mb-2')
            for task in tasks:
                status_class = 'bg-green-100 line-through text-gray-400' if task.is_done else 'bg-yellow-50'
                with ui.card().classes(f'w-full mb-2 border-l-4 border-orange-400 {status_class} shadow-sm'):
                    with ui.row().classes('w-full items-center p-2'):
                        ui.checkbox(value=task.is_done, on_change=lambda e, t=task: update_task_status(t, e.value, refresh))
                        with ui.column().classes('flex-grow'):
                            ui.label(task.title).classes('text-bold')
                            ui.label(f'Zuständig: {task.assigned_to.name if task.assigned_to else "Niemand"}').classes('text-xs')
        session.close()
    refresh()

# --- CRUD-Operationen ---

def add_user(input_field, callback):
    s = get_session()
    s.add(MitbewohnerDB(name=input_field.value.strip()))
    s.commit(); s.close()
    input_field.value = ''
    ui.notify('Mitbewohner*in hinzugefügt', color='positive')
    callback()

def save_expense(desc, amt, cat, payer, parts, callback):
    if not desc.value or not amt.value or not payer.value:
        ui.notify('Bitte alle Pflichtfelder ausfüllen', color='warning')
        return
    s = get_session()
    exp = Expense(description=desc.value, amount=amt.value, category=cat.value, paid_by_id=payer.value)
    if parts.value:
        for p_id in parts.value:
            u = s.get(MitbewohnerDB, p_id)
            if u: exp.participants.append(u)
    s.add(exp); s.commit(); s.close()
    ui.notify('Ausgabe erfolgreich gespeichert', color='positive')
    callback()

def save_task(title, who, callback):
    if not title.value: return
    s = get_session()
    s.add(Task(title=title.value, assigned_to_id=who.value))
    s.commit(); s.close()
    ui.notify('Neues Ämtli erstellt', color='positive')
    callback()

def update_task_status(task, val, callback):
    s = get_session()
    task.is_done = val
    s.merge(task); s.commit(); s.close()
    callback()

def delete_user(user, callback):
    s = get_session()
    u_to_del = s.get(MitbewohnerDB, user.id)
    if u_to_del:
        s.delete(u_to_del)
        s.commit()
    s.close()
    ui.notify('Eintrag gelöscht', color='negative')
    callback()

def edit_user(user, callback):
    with ui.dialog() as d, ui.card():
        ui.label(f'Bearbeite {user.name}').classes('text-h6')
        name_in = ui.input(value=user.name)
        with ui.row():
            ui.button('Speichern', on_click=lambda: (save_user_edit(user.id, name_in.value, d), callback()))
            ui.button('Abbrechen', on_click=d.close).props('flat')
    d.open()

def save_user_edit(uid, new_name, dialog):
    s = get_session()
    u = s.get(MitbewohnerDB, uid)
    if u: u.name = new_name
    s.commit(); s.close()
    dialog.close()

# --- Hauptseite ---

@ui.page('/')
def main_page():
    ui.query('body').style('background-color: #f0f2f5')
    
    with ui.header().classes('bg-indigo-700 p-4 shadow-lg'):
        ui.label('WG-Planner').classes('text-h4 text-white font-bold')

    with ui.tabs().classes('w-full bg-white shadow-sm') as tabs:
        t1 = ui.tab('Mitbewohner*innen', icon='people')
        t2 = ui.tab('Finanzen', icon='payments')
        t3 = ui.tab('Ämtli & Kalender', icon='event')

    with ui.tab_panels(tabs, value=t1).classes('w-full max-w-2xl mx-auto bg-transparent p-4'):
        with ui.tab_panel(t1):
            c1 = ui.column().classes('w-full')
            render_users_tab(c1)
        with ui.tab_panel(t2):
            c2 = ui.column().classes('w-full')
            render_finances_tab(c2)
        with ui.tab_panel(t3):
            c3 = ui.column().classes('w-full')
            render_tasks_tab(c3)

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title='WG-Planner', port=8081, show=False)