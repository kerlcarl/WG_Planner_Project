# WG_Planner_Project
# WG-Planner: Finanzen & Ämtli-Management

## 1. Projektbeschreibung
Dieses Projekt wurde im Rahmen des Moduls Objektorientierte Programmierung (26FS) an der FHNW entwickelt. Der WG-Planner ist eine webbasierte Anwendung, die darauf abzielt, das Zusammenleben in einer Wohngemeinschaft zu organisieren und zu vereinfachen. Die App ermöglicht das Tracking von gemeinsamen Ausgaben sowie die Verwaltung eines digitalen Ämtliplan.

## 2. Projektziele & Funktionen
**Finanz-Tracker:** Erfassung von Ausgaben und automatische Berechnung der Anteile pro Mitbewohner.
**Ämtli-Kalender:** Zuweisung und Visualisierung von Haushaltsaufgaben für alle Teammitglieder.
**Benutzerverwaltung:** Individuelle Profile für jeden WG-Bewohner.
**Web-UI:** Intuitive Bedienung über eine moderne Browser-Oberfläche.

## 3. Technische Architektur
Die Anwendung folgt der im Modul vermittelten Softwarearchitektur:
**Frontend (Präsentationsschicht):** Realisiert mit **NiceGUI**, ausgeführt im Browser als Thin Client.
**Backend (Anwendungslogik):** Objektorientierte Programmierung in **Python** zur Abbildung der Businesslogik (Klassen für Bewohner, Ausgaben, Aufgaben).
**Datenbank (Persistenzschicht):** Speicherung der Daten in **SQLite** unter Verwendung von **SQLAlchemy** als Object-Relational Mapper (ORM).

## 4. User Stories
* *Als Mitbewohner möchte ich eine Ausgabe erfassen können, damit das System den Betrag gerecht auf alle aufteilt.*
* *Als Mitbewohner möchte ich sehen, welches "Ämtli" mir diese Woche zugewiesen wurde, damit die WG sauber bleibt.*
* *Als Admin der WG möchte ich neue Mitbewohner hinzufügen können, damit die Finanzberechnung aktuell bleibt.*

## 5. Verwendete Bibliotheken & Tools
**Python 3.x** 
**NiceGUI** (Frontend-Framework)
**SQLAlchemy** (Datenbank-ORM)
**Pydantic** (Datenvalidierung)
**Visual Studio Code** (Entwicklungsumgebung)

## 6. Arbeitsaufteilung (Initiales Konzept)
Gemäss den Richtlinien ist jedes Teammitglied für einen substanziellen Teil des Codes verantwortlich. Die Beiträge werden über die GitHub-Commits validiert.

* **Mitglied 1:** Entwicklung der Datenmodelle (Klassen), Datenbank-Setup und SQLAlchemy-Integration
* **Mitglied 2:** Gestaltung des User Interface (UI) mit NiceGUI und Verknüpfung der Frontend-Komponenten
* **Mitglied 3:** Implementierung der Berechnungslogik (Finanz-Algorithmen) und der Ämtli-Verwaltungslogik

## 7. Installation & Ausführung
1. Repository klonen.
2. Abhängigkeiten installieren: `pip install nicegui sqlalchemy`.
3. Anwendung starten: `python main.py`.
4. Die App ist im Browser unter `http://localhost:8080` erreichbar.
