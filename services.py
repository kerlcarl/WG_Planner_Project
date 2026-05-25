# Anwendungslogik und CRUD-Funktionen – vollständig frei von UI-Abhängigkeiten.
from contextlib import contextmanager
from datetime import datetime

from models import EinkaufsItem, Expense, ManualDebt, MitbewohnerDB, Post, Reaction, Session, Task

USER_PALETTE = [
    "#6366f1",  # indigo
    "#3b82f6",  # blue
    "#ef4444",  # red
    "#10b981",  # emerald
    "#f59e0b",  # amber
    "#06b6d4",  # cyan
    "#ec4899",  # pink
    "#f97316",  # orange
]

DEFAULT_EXPENSE_CATEGORIES = [
    "Lebensmittel",
    "Haushalt",
    "Miete",
    "Internet",
    "Strom",
    "Putzmittel",
    "Freizeit",
    "Sonstiges",
]

SETTLEMENT_CATEGORY = "Ausgleich"


@contextmanager
def get_session():
    session = Session()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ── Finanzen ───────────────────────────────────────────────────────────────────

def calculate_balances() -> dict[int, float]:
    with get_session() as session:
        users = session.query(MitbewohnerDB).all()
        balances = {user.id: 0.0 for user in users}

        for expense in session.query(Expense).all():
            share = expense.calculate_share()
            for user in expense.participants:
                if user.id in balances:
                    balances[user.id] -= share
            if expense.paid_by_id in balances:
                balances[expense.paid_by_id] += expense.amount

        for debt in session.query(ManualDebt).all():
            if debt.from_user_id in balances:
                balances[debt.from_user_id] -= debt.amount
            if debt.to_user_id in balances:
                balances[debt.to_user_id] += debt.amount

    return balances


def calculate_settlements() -> list[dict[str, float | int]]:
    balances = calculate_balances()
    settlements: list[dict[str, float | int]] = []

    creditors = [
        {"user_id": uid, "amount": round(amt, 2)}
        for uid, amt in balances.items()
        if amt > 0.01
    ]
    debtors = [
        {"user_id": uid, "amount": round(-amt, 2)}
        for uid, amt in balances.items()
        if amt < -0.01
    ]

    ci = di = 0
    while ci < len(creditors) and di < len(debtors):
        creditor, debtor = creditors[ci], debtors[di]
        transfer = round(min(creditor["amount"], debtor["amount"]), 2)
        if transfer > 0.01:
            settlements.append({
                "from_user_id": debtor["user_id"],
                "to_user_id": creditor["user_id"],
                "amount": transfer,
            })
        creditor["amount"] = round(creditor["amount"] - transfer, 2)
        debtor["amount"] = round(debtor["amount"] - transfer, 2)
        if creditor["amount"] <= 0.01:
            ci += 1
        if debtor["amount"] <= 0.01:
            di += 1

    return settlements


def is_settlement_category(category: str | None) -> bool:
    return (category or "").strip().casefold() == SETTLEMENT_CATEGORY.casefold()


def calculate_category_totals() -> list[dict[str, float]]:
    with get_session() as session:
        totals: dict[str, float] = {}
        for expense in session.query(Expense).all():
            if is_settlement_category(expense.category):
                continue
            category = expense.category or "Sonstiges"
            totals[category] = totals.get(category, 0.0) + expense.amount

    return [
        {"category": cat, "amount": round(amt, 2)}
        for cat, amt in sorted(totals.items(), key=lambda item: item[1], reverse=True)
    ]


def save_expense(desc: str, amt: float, cat: str, payer_id: int, participant_ids: list[int]) -> None:
    if len(participant_ids) < 2:
        raise ValueError("Es müssen mindestens 2 Personen an einer Ausgabe beteiligt sein.")
    with get_session() as session:
        expense = Expense(description=desc, amount=amt, category=cat, paid_by_id=payer_id)
        for uid in participant_ids:
            user = session.get(MitbewohnerDB, uid)
            if user:
                expense.participants.append(user)
        session.add(expense)
        session.commit()


def update_expense(expense_id: int, desc: str, amt: float, cat: str, payer_id: int, participant_ids: list[int]) -> None:
    if len(participant_ids) < 2:
        raise ValueError("Es müssen mindestens 2 Personen an einer Ausgabe beteiligt sein.")
    with get_session() as session:
        expense = session.get(Expense, expense_id)
        if not expense:
            raise ValueError("Ausgabe nicht gefunden.")
        expense.description = desc
        expense.amount = amt
        expense.category = cat
        expense.paid_by_id = payer_id
        expense.participants.clear()
        for uid in participant_ids:
            user = session.get(MitbewohnerDB, uid)
            if user:
                expense.participants.append(user)
        session.commit()


def delete_expense(expense_id: int) -> None:
    with get_session() as session:
        expense = session.get(Expense, expense_id)
        if expense:
            session.delete(expense)
            session.commit()


def create_manual_debt(from_id: int, to_id: int, amount: float, method: str, description: str) -> str:
    """Legt eine manuelle Schuld an oder aktualisiert eine bestehende. Gibt eine Bestätigungsmeldung zurück."""
    with get_session() as session:
        desc = description.strip() if description.strip() else f"Offene Rechnung via {method}"
        existing = session.query(ManualDebt).filter(
            ManualDebt.from_user_id == from_id,
            ManualDebt.to_user_id == to_id,
        ).first()
        if existing:
            existing.amount = round(existing.amount + amount, 2)
            if desc:
                existing.description = (
                    f"{existing.description}, {desc}" if existing.description else desc
                )
            existing.payment_method = method
            msg = f"Rechnung aktualisiert – neu CHF {existing.amount:.2f}"
        else:
            session.add(ManualDebt(
                description=desc, amount=amount, payment_method=method,
                from_user_id=from_id, to_user_id=to_id,
            ))
            msg = "Offene Rechnung erfasst"
        session.commit()
    return msg


def delete_manual_debt(debt_id: int) -> None:
    with get_session() as session:
        debt = session.get(ManualDebt, debt_id)
        if debt:
            session.delete(debt)
            session.commit()


def delete_manual_debts_by_pair(from_id: int, to_id: int) -> None:
    with get_session() as session:
        session.query(ManualDebt).filter(
            ManualDebt.from_user_id == from_id,
            ManualDebt.to_user_id == to_id,
        ).delete()
        session.commit()


def save_settlement(from_id: int, to_id: int, amount: float, method: str, note: str = "") -> None:
    """Erfasst einen Ausgleich als Expense und löscht zugehörige manuelle Schulden."""
    desc = note if note.strip() else f"Ausgleich via {method}"
    with get_session() as session:
        expense = Expense(description=desc, amount=amount, category=SETTLEMENT_CATEGORY, paid_by_id=from_id)
        to_user = session.get(MitbewohnerDB, to_id)
        if to_user:
            expense.participants.append(to_user)
        session.add(expense)
        session.query(ManualDebt).filter(
            ManualDebt.from_user_id == from_id,
            ManualDebt.to_user_id == to_id,
        ).delete()
        session.commit()


# ── Aufgaben ───────────────────────────────────────────────────────────────────

def save_task(title_val: str, who_id, due_date_str: str) -> str | None:
    """Legt ein neues Ämtli an. Gibt eine Fehlermeldung zurück oder None bei Erfolg."""
    if not title_val or not title_val.strip():
        return "Titel darf nicht leer sein"
    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, "%d.%m.%Y")
        except ValueError:
            return "Ungültiges Datum – bitte TT.MM.JJJJ verwenden"
    with get_session() as session:
        session.add(Task(title=title_val.strip(), assigned_to_id=who_id, due_date=due_date))
        session.commit()
    return None


def update_task_status(task_id: int, value: bool) -> None:
    from datetime import datetime
    with get_session() as session:
        task = session.get(Task, task_id)
        if task:
            task.is_done = value
            task.completed_at = datetime.now() if value else None
            session.commit()


def update_task(task_id: int, title_val: str, who_id, due_date_str: str) -> str | None:
    """Aktualisiert ein bestehendes Ämtli. Gibt eine Fehlermeldung zurück oder None bei Erfolg."""
    if not title_val or not title_val.strip():
        return "Titel darf nicht leer sein"
    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, "%d.%m.%Y")
        except ValueError:
            return "Ungültiges Datum – bitte TT.MM.JJJJ verwenden"
    with get_session() as session:
        task = session.get(Task, task_id)
        if not task:
            return "Ämtli nicht gefunden"
        task.title = title_val.strip()
        task.assigned_to_id = who_id
        task.due_date = due_date
        session.commit()
    return None


def delete_task(task_id: int) -> None:
    with get_session() as session:
        task = session.get(Task, task_id)
        if task:
            session.delete(task)
            session.commit()


# ── Mitbewohner ────────────────────────────────────────────────────────────────

def add_user(name: str) -> None:
    with get_session() as session:
        used = {u.color for u in session.query(MitbewohnerDB).all()}
        color = next((c for c in USER_PALETTE if c not in used), USER_PALETTE[len(used) % len(USER_PALETTE)])
        session.add(MitbewohnerDB(name=name, color=color))
        session.commit()


def assign_palette_colors() -> None:
    """Weist Nutzern mit der Standard-Farbe automatisch verschiedene Palette-Farben zu."""
    with get_session() as session:
        users = session.query(MitbewohnerDB).order_by(MitbewohnerDB.id).all()
        used: set[str] = set()
        for u in users:
            if u.color in ("#336699", None, ""):
                color = next((c for c in USER_PALETTE if c not in used), USER_PALETTE[len(used) % len(USER_PALETTE)])
                u.color = color
            used.add(u.color)
        session.commit()


def delete_user(user_id: int) -> None:
    with get_session() as session:
        user = session.get(MitbewohnerDB, user_id)
        if user:
            session.delete(user)
            session.commit()


def save_user_edit(user_id: int, new_name: str) -> None:
    with get_session() as session:
        user = session.get(MitbewohnerDB, user_id)
        if user:
            user.name = new_name
            session.commit()


# ── Blog ───────────────────────────────────────────────────────────────────────

def add_post(author_id: int, content: str, is_important: bool) -> None:
    with get_session() as session:
        session.add(Post(author_id=author_id, content=content.strip(), is_important=is_important))
        session.commit()


def delete_post(post_id: int) -> None:
    with get_session() as session:
        post = session.get(Post, post_id)
        if post:
            session.delete(post)
            session.commit()


def toggle_post_important(post_id: int) -> None:
    with get_session() as session:
        post = session.get(Post, post_id)
        if post:
            post.is_important = not post.is_important
            session.commit()


def toggle_reaction(user_id: int, post_id: int, emoji: str) -> tuple[dict, list]:
    with get_session() as session:
        existing = session.query(Reaction).filter(
            Reaction.user_id == user_id,
            Reaction.post_id == post_id,
        ).first()

        if existing:
            if existing.emoji == emoji:
                session.delete(existing)
            else:
                existing.emoji = emoji
        else:
            session.add(Reaction(user_id=user_id, post_id=post_id, emoji=emoji))

        session.commit()

        reactions_count: dict[str, int] = {}
        user_reactions: list[str] = []
        for r in session.query(Reaction).filter(Reaction.post_id == post_id).all():
            reactions_count[r.emoji] = reactions_count.get(r.emoji, 0) + 1
            if r.user_id == user_id:
                user_reactions.append(r.emoji)

    return reactions_count, user_reactions


# ── Einkaufsliste ──────────────────────────────────────────────────────────────

def add_shopping_item(name: str, menge: str, einheit: str, author_id: int) -> None:
    with get_session() as session:
        session.add(EinkaufsItem(
            name=name.strip(),
            menge=menge.strip() if menge else None,
            einheit=einheit.strip() if einheit else None,
            author_id=author_id,
        ))
        session.commit()


def toggle_shopping_item(item_id: int, is_bought: bool) -> None:
    with get_session() as session:
        item = session.get(EinkaufsItem, item_id)
        if item:
            item.is_bought = is_bought
            session.commit()


def delete_shopping_item(item_id: int) -> None:
    with get_session() as session:
        item = session.get(EinkaufsItem, item_id)
        if item:
            session.delete(item)
            session.commit()


def delete_bought_items() -> None:
    with get_session() as session:
        session.query(EinkaufsItem).filter(EinkaufsItem.is_bought == True).delete()
        session.commit()
