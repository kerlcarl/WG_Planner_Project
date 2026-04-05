# WG-Planner

Browserbasierte Anwendung zur Verwaltung einer Wohngemeinschaft. Der aktuelle Stand deckt Mitbewohner*innen, gemeinsame Ausgaben sowie Aufgaben mit Kalenderansicht ab.

## Projektstruktur

```text
WG_Planner_Project/
  main.py
  models.py
  services.py
  ui/
    __init__.py
    users.py
    finances.py
    tasks.py
```

- `main.py`: Einstiegspunkt, Startlogik und Aufbau der Hauptseite
- `models.py`: SQLAlchemy-Modelle, Session und Datenbankinitialisierung
- `services.py`: Gemeinsame Business-Logik und CRUD-Funktionen
- `ui/users.py`: Darstellung des Mitbewohner*innen-Tabs
- `ui/finances.py`: Darstellung des Finanzen-Tabs
- `ui/tasks.py`: Darstellung des Ämtli- und Kalender-Tabs

## Architektur

Die Anwendung ist grob in drei Verantwortungsbereiche getrennt:

- Presentation Layer: NiceGUI-Komponenten in `main.py` und `ui/`
- Application Layer: Aktionen und Geschäftslogik in `services.py`
- Persistence Layer: SQLAlchemy-Modelle und SQLite in `models.py`

Datenfluss:

```text
Browser <-> NiceGUI Server (main.py / ui) <-> services.py <-> SQLAlchemy <-> SQLite
```

## Aktuell implementiert

- Mitbewohner*innen anlegen, bearbeiten und löschen
- Ausgaben erfassen und Kontostände berechnen
- Aufgaben erstellen, anzeigen und als erledigt markieren

## Geplante Erweiterungen

- Rotationslogik für Ämtli
- Benutzerprofile mit zusätzlichen Einstellungen
- Filter, Auswertungen und Exporte für Finanzen
- Verbesserte mobile Darstellung und UX

## Installation

1. Repository klonen
2. Virtuelle Umgebung erstellen
3. Abhängigkeiten installieren
4. Anwendung starten

```bash
git clone https://github.com/kerlcarl/WG_Planner_Project.git
cd WG_Planner_Project
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Die Anwendung läuft aktuell auf Port `8081`.
