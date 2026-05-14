# WG‑Planner: Finances & Task Management

## 1. Projektbeschreibung
Dieses Repository enthält den Code für den **WG‑Planner**, eine browserbasierte Anwendung zur koordinativen Unterstützung von Wohngemeinschaften. Entwickelt im Rahmen des Moduls "Objektorientierte Programmierung" (26FS) an der FHNW, verwaltet die Anwendung gemeinsame Ausgaben, Haushaltsaufgaben, Kommunikation und Einkaufslisten.

## 2. Implementierte Kernfunktionen

* **Mitbewohner\*innen-Verwaltung** – Vollständiges CRUD mit Tastatur-Unterstützung, farbkodierten Avataren und Inline-Bearbeitung.

* **Shared-Expense-Tracker** – Erfassung gemeinsamer Ausgaben mit:
  - Automatischer Anteilsberechnung (gleichmässige Aufteilung auf Beteiligte)
  - Echtzeit-Kontoständen (Guthaben vs. Schulden)
  - Optimierten Ausgleichsvorschlägen zur Minimierung der Überweisungen
  - Manuell erfassbaren offenen Rechnungen
  - Kategorisierung inkl. Custom-Kategorien und Ausgabenverlauf

* **Ämtli-Plan & Kalender** – Verwaltung von Haushaltsaufgaben mit Deadline-Tracking, interaktivem Kalender und Completion-Checkbox.

* **Kollaborations-Hub** – WG-Blog (Schwarzes Brett) mit Reaktions-Emojis sowie eine Echtzeit-Einkaufsliste mit Auto-Sync alle 2 Sekunden.

* **Authentifizierung & Profile** – Registrierung, Login, Passwort-Änderung, Avatar-Upload und Passwort-Reset-Flow.

## 3. Technische Architektur

Die Lösung ist als klassische **Drei-Schichten-Architektur** implementiert:

| Schicht | Technologie | Verantwortung |
|---|---|---|
| **Präsentation** | Browser (Vue.js/Quasar via NiceGUI) | Thin Client, rendert UI-Komponenten |
| **Anwendungslogik** | Python / NiceGUI (server-seitig) | UI-Zustand, Geschäftslogik, OOP-Klassen |
| **Persistenz** | SQLAlchemy ORM + SQLite / PostgreSQL | Datenhaltung ohne direktes SQL |

```
Browser  ←→  NiceGUI-Server (main.py + ui/)  ←→  SQLAlchemy  ←→  DB
```

### Schichttrennung

- **`models.py`** – ORM-Datenmodelle (`MitbewohnerDB`, `Task`, `Expense`, `Post` etc.) und DB-Initialisierung
- **`services.py`** – Reine Anwendungslogik; keinerlei NiceGUI-Abhängigkeiten, akzeptiert plain Python-Werte
- **`auth_services.py`** – Authentifizierungslogik (Hashing, Tokens); ebenfalls UI-frei
- **`ui/`** – Alle NiceGUI-Komponenten; zuständig für Darstellung, Validierungsmeldungen (`ui.notify`) und User-Feedback

Session-Management erfolgt durchgängig mit SQLAlchemy Context Managern (`with Session() as session:`). Schema-Migrationen werden via `sqlalchemy.inspect` abgesichert, sodass Spalten nur hinzugefügt werden, wenn sie fehlen.

## 4. User Stories

**Finanzen**
- Als Mitbewohner\*in möchte ich gemeinsame Ausgaben erfassen, damit der Überblick erhalten bleibt.
- Als Mitbewohner\*in möchte ich den Schuldenstand sehen, um den Ausgleich zu planen.
- Als Nutzer\*in möchte ich Ausgaben Kategorien zuordnen, um Kostenstellen zu analysieren.

**Ämtli & Organisation**
- Als Mitbewohner\*in möchte ich ein Ämtli als "erledigt" markieren, damit andere den Status sehen.
- Als Mitbewohner\*in möchte ich Aufgaben mit Deadlines versehen, damit nichts vergessen geht.

**Kommunikation**
- Als Mitbewohner\*in möchte ich Nachrichten im WG-Blog posten, um alle zu informieren.
- Als Mitbewohner\*in möchte ich eine gemeinsame Einkaufsliste führen, die sich live aktualisiert.

**Administration & Profil**
- Als Nutzer\*in möchte ich mich registrieren und anmelden, damit mein Konto geschützt ist.
- Als Nutzer\*in möchte ich mein Profilbild und meinen Namen anpassen.

## 5. Installation & Ausführung

1. Repository klonen:
   ```bash
   git clone https://github.com/kerlcarl/WG_Planner_Project.git
   cd WG_Planner_Project
   ```
2. Virtuelle Umgebung erstellen und aktivieren:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   ```
3. Abhängigkeiten installieren:
   ```bash
   pip install -r requirements.txt
   ```
4. Anwendung starten:
   ```bash
   python3 main.py
   ```
5. Im Browser öffnen: `http://localhost:8080`

### Umgebungsvariablen (optional)

| Variable | Standard | Beschreibung |
|---|---|---|
| `PORT` | `8080` | HTTP-Port |
| `DATABASE_URL` | `sqlite:///wg_planner.db` | DB-Verbindung (SQLite oder PostgreSQL) |
| `STORAGE_SECRET` | *(dev-Wert)* | Secret für NiceGUI Session-Storage |

## 6. Passwort vergessen (Entwicklungsmodus)

Da in der lokalen Entwicklungsumgebung kein E-Mail-Dienst eingerichtet ist, wird der Reset-Link **nicht per E-Mail verschickt**, sondern direkt im Browser angezeigt:

1. Gehe auf `/forgot-password` und gib deine E-Mail ein.
2. Klicke auf „Link anfordern".
3. Ein **blauer Info-Toast** erscheint auf derselben Seite mit dem kompletten Reset-Link.
4. Kopiere den Pfad (`/reset-password?token=...`) und öffne ihn im Browser.

> **Für ein echtes Deployment** muss ein E-Mail-Dienst (z.B. SendGrid, SMTP) in `ui/auth.py` → `do_reset()` eingebunden werden. Der Platzhalter-Kommentar `# In a real deployment, send this via email.` markiert die Stelle.

## 7. Verwendete Bibliotheken

| Bibliothek | Version | Zweck |
|---|---|---|
| **NiceGUI** | ≥ 1.4 | Server-seitiges UI-Framework (Vue.js/Quasar) |
| **SQLAlchemy** | ≥ 2.0 | ORM & Datenbankabstraktion |
| **Pydantic** | ≥ 2.0 | Datenvalidierung (FastAPI-Integration) |
| **bcrypt** | – | Passwort-Hashing |
| **FastAPI** | (via NiceGUI) | HTTP-Endpunkte |
| **SQLite** / **PostgreSQL** | – | Persistenzschicht |

## 8. Deployment (Render)

Die Datei `render.yaml` enthält die Konfiguration für ein Deployment auf [Render](https://render.com). Dabei wird automatisch `DATABASE_URL` auf eine PostgreSQL-Instanz gesetzt – die Anwendung erkennt dies und wechselt vom SQLite-Modus.
