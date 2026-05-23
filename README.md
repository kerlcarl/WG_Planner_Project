# WG‑Planner: Finances & Task Management

## 1. Projektbeschreibung
Dieses Repository enthält den Code für den **WG‑Planner**, eine browserbasierte Anwendung zur koordinativen Unterstützung von Wohngemeinschaften. Entwickelt im Rahmen des Moduls "Objektorientierte Programmierung" (26FS) an der FHNW, verwaltet die Anwendung gemeinsame Ausgaben, Haushaltsaufgaben, Kommunikation und Einkaufslisten.

## 2. Implementierte Kernfunktionen

* **Mitbewohner\*innen-Verwaltung** – Hinzufügen, Bearbeiten und Löschen von Mitbewohner*innen mit farbkodierten Initialen-Avataren.

* **Shared-Expense-Tracker** – Erfassung gemeinsamer Ausgaben mit:
  - Automatischer Anteilsberechnung (gleichmässige Aufteilung auf Beteiligte)
  - Echtzeit-Kontoständen (Guthaben vs. Schulden)
  - Optimierten Ausgleichsvorschlägen zur Minimierung der Überweisungen
  - Manuell erfassbaren offenen Rechnungen
  - Kategorisierung inkl. Custom-Kategorien und Ausgabenverlauf

* **Ämtli-Plan** – Verwaltung von Haushaltsaufgaben mit Deadline-Tracking und farbkodierter Statusansicht:
  - **Abgelaufen** (rot): Deadline bereits überschritten
  - **Bald fällig** (orange): Deadline innerhalb der nächsten 24 Stunden
  - **Zu erledigen** (gelb): Offene Aufgaben mit zukünftiger Deadline
  - **Erledigt** (grün): Abgehakte Aufgaben mit Erledigungsdatum
  - Deadline-Badge (Wochentag + Datum) direkt auf jeder Aufgabenkarte

* **Kollaborations-Hub** – WG-Blog (Schwarzes Brett) mit Reaktions-Emojis sowie eine Echtzeit-Einkaufsliste mit Auto-Sync alle 2 Sekunden.

* **Nutzerprofile** – Mitbewohner\*in per Dropdown auswählen; Name und Profilbild im Einstellungs-Bereich anpassen.

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
- **`auth_services.py`** – Nutzerverwaltung (Avatar, Profilabfrage); ebenfalls UI-frei
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
- Als Mitbewohner\*in möchte ich abgelaufene Aufgaben sofort erkennen, damit ich sie priorisieren kann.
- Als Mitbewohner\*in möchte ich sehen, welche Aufgaben in den nächsten 24 Stunden fällig sind.
- Als Mitbewohner\*in möchte ich das Erledigungsdatum einer Aufgabe sehen, um den Fortschritt nachzuverfolgen.

**Kommunikation**
- Als Mitbewohner\*in möchte ich Nachrichten im WG-Blog posten, um alle zu informieren.
- Als Mitbewohner\*in möchte ich eine gemeinsame Einkaufsliste führen, die sich live aktualisiert.

**Profil**
- Als Mitbewohner\*in möchte ich meinen Namen im Einstellungs-Bereich anpassen können.
- Als Mitbewohner\*in möchte ich ein Profilbild hochladen können.

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

## 6. Verwendete Bibliotheken

| Bibliothek | Version | Zweck |
|---|---|---|
| **NiceGUI** | ≥ 1.4 | Server-seitiges UI-Framework (Vue.js/Quasar) |
| **SQLAlchemy** | ≥ 2.0 | ORM & Datenbankabstraktion |
| **Pydantic** | ≥ 2.0 | Datenvalidierung (FastAPI-Integration) |
| **FastAPI** | (via NiceGUI) | HTTP-Endpunkte |
| **SQLite** / **PostgreSQL** | – | Persistenzschicht |

## 7. Deployment (Render)

Die Datei `render.yaml` enthält die Konfiguration für ein Deployment auf [Render](https://render.com). Dabei wird automatisch `DATABASE_URL` auf eine PostgreSQL-Instanz gesetzt – die Anwendung erkennt dies und wechselt vom SQLite-Modus.
