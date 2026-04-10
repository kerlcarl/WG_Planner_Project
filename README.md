# WG‑Planner Project
# WG‑Planner: Finances & Task Management

## 1. Projektbeschreibung
Dieses Repository enthält den Code für den **WG‑Planner**, eine browserbasierte Anwendung zur koordinativen Unterstützung
von Wohngemeinschaften (WG). Entwickelt im Rahmen des Moduls "Objektorientierte Programmierung" (26FS) an der FHNW,
zielte das Projekt darauf ab, wiederkehrende Aufgaben und gemeinsame Ausgaben strukturiert zu verwalten.

Aktuell ist die Anwendung als MVP (Minimum Viable Product) am Start und bietet eine einfache
Oberfläche zum Hinzufügen und Anzeigen von Mitbewohner*innen. Die geplanten Kernfunktionen
umfassen später ein Shared‑Expense‑Tracking, einen rotierenden Ämtli‑Plan und ein Benutzerprofil‑System.

## 2. Ziele & Kernfunktionen
Die Anwendung soll den administrativen Aufwand in einer WG minimieren und die Transparenz erhöhen. Aktuell
ist ein einfacher Mitbewohner‑Verwaltungsbildschirm implementiert; die folgenden Kernfunktionen sind geplant:

### ✔ Aktuell implementiert
* **Mitbewohner-Verwaltung** – Hinzufügen und Anzeige von Bewohnern
* **Task-System (Ämtli)** – Aufgaben erstellen, zuweisen und als erledigt markieren
* **Finanz-Tracker (Basis)** – Ausgaben erfassen, Teilnehmer auswählen und Kosten automatisch aufteilen

### 🚧 Geplante Kernfunktionen
1. **Shared‑Expense‑Tracker** – Erfassung gemeinsamer Ausgaben mit automatischer Aufteilung der Beträge
	auf alle Bewohner.
2. **Task‑Scheduler (Ämtli‑Plan)** – Zuweisung, Rotation und Statusverfolgung von Haushaltspflichten.
3. **Benutzer­management** – Accounts mit Namen, Kennfarbe und optionalem Profilbild.
4. **Responsive Web‑Frontend** – Bedienung im Browser; gestaltet mit NiceGUI.

## 3. Technische Architektur
Die Lösung ist als klassische Drei‑Schichten‑Architektur implementiert:

* **Presentation Layer (Frontend)** – NiceGUI‑basierte Single‑Page‑Application, dient als Thin Client. Kommuniziert
	per HTTP/WS mit dem Backend.
* **Application Layer (Backend)** – Python‑Module enthalten die OOP‑Modelle (`User`, `Expense`, `Task` etc.) sowie
	Service‑Klassen für Geschäftslogik und Routing (FastAPI/NiceGUI intern). Alle Endpunkte befinden sich
	in `main.py` bzw. im Modul `api/`.
* **Persistence Layer** – SQLite‑Datei (`wgplanner.db`) als lokale Datenbank; SQLAlchemy (Version 1.4.x) wird als ORM
	genutzt. Modelle stehen in `models.py`.

Ein einfaches Sequenzdiagramm:

```
Browser <--> NiceGUI Server (main.py) <--> SQLAlchemy <--> SQLite DB
```

## 4. User Stories
Die Anforderungen wurden in Form von User Stories formuliert. Alle Stories folgen dem Format
"Als [Rolle] möchte ich ... , damit ...". Akzeptanzkriterien sind bei Bedarf im Code/Issues dokumentiert.

> **Status:** Derzeit unterstützt das System nur die Basisstory zum Anlegen von Mitbewohner*innen.

**Finanzen (Shared Expenses)**
* Als Mitbewohner*in möchte ich eine Liste aller bisherigen Ausgaben sehen, um nachzuvollziehen, wofür Geld ausgegeben wurde.
* Als Mitbewohner*in möchte ich den Schuldenstand zu anderen Personen sehen, um den Ausgleich zu planen.
* Als Nutzer*in möchte ich Ausgaben Kategorien (Lebensmittel, Miete, Putzmittel etc.) zuordnen können, um Kostenstellen zu analysieren.

**Ämtli & Organisation**
* Als Mitbewohner*in möchte ich ein Ämtli als "erledigt" markieren können, damit andere den aktuellen Status sehen.
* Die Aufgabenzuordnung soll sich wöchentlich rotieren, um die Last gerecht zu verteilen.
* Als Mitbewohner*in möchte ich Aufgaben als "dringend" markieren können.

**Administration & Profil**
* Als Nutzer*in möchte ich meinen Namen und eine Kennfarbe definieren, damit meine Einträge in der UI eindeutig erkennbar sind.
* Als WG möchte ich monatliche Statistiken (z. B. "Wer hat am meisten geputzt?") sehen.

## 8. Roadmap (geplante Erweiterungen)

1. **Shared‑Expense‑Tracker**
	* Ausgaben eintragen, kategorisieren und filtern
	* Automatische Aufteilung / Settlements zwischen Bewohnern
	* Export als CSV / PDF

2. **Ämtli / Task‑Scheduler**
	* Aufgaben erstellen und wiederkehrend planen
	* Rotationslogik (wöchentlich/monatlich)
	* Status, Priorität, Erinnerungen

3. **Benutzerprofil & Authentifizierung**
	* Nutzerkonto mit Name, Kennfarbe, optionalem Profilbild
	* Rollen/Administration (z. B. WG‑Admin)

4. **UX / UI‑Modernisierung**
	* Responsive Layout (Mobile + Desktop)
	* Fokus auf Klarheit: Karten, Farben, kurze Feedback-Popups
	* Barrierefreiheit (kontrastfreundliche Farben, Tastaturnavigation)

## 5. Verwendete Bibliotheken & Tools
* **Python 3.11** (minimal), getestet unter 3.11/3.12
* **NiceGUI** 1.0.x – Frontend-Framework
* **SQLAlchemy** 1.4.x – ORM
* **Pydantic** 2.x – Validierung
* **FastAPI** (als HTTP Server, via NiceGUI)
* **pytest** – Testframework (falls vorhanden)
* **black**, **flake8** – Formatierung & Linting
* **SQLite** – eingebettete DB
* **Visual Studio Code** – empfohlene IDE

Versionen werden in `requirements.txt` festgehalten.

## 6. Arbeitsaufteilung (Initiales Konzept)
Die Teamorganisation erfolgte über GitHub Issues/Projektboard; jeder Beitrag ist durch Commits und PRs
nachvollziehbar. Beispielhafte Rollenverteilung:

* **Backend / Datenmodell** – Klassen, Datenbankmigration, ORM-Integration
* **Frontend / UI** – NiceGUI-Layouts, Event-Handler, Client-seitige Logik
* **Business-Logik** – Berechnungsalgorithmen (Finanzausgleich), Turnus-Mechanismus für Aufgaben

Diese Gliederung hilft beim Review-Prozess und der Evaluierung durch Dozenten.

## 7. Installation & Ausführung
1. Repository klonen:
	```bash
	git clone https://github.com/kerlcarl/WG_Planner_Project.git
	cd WG_Planner_Project
	```
2. Virtuelle Umgebung erstellen und aktivieren (empfohlen):
	```bash
	python3 -m venv .venv
	source .venv/bin/activate
	```
3. Abhängigkeiten installieren:
	```bash
	pip install -r requirements.txt
	```
4. (Optional) Umgebungsvariablen setzen, z.B. `PORT=8000` oder `DATABASE_URL=sqlite:///wgplanner.db`.
5. Anwendung starten:
	```bash
	python3 main.py
	```
6. Im Browser öffnen: `http://localhost:8080` (Standardport; konfigurierbar via `PORT`).

Weitere Hinweise siehe Kommentarzeilen in `main.py`.
