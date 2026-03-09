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
[cite_start]Die Anwendung folgt der im Modul vermittelten Softwarearchitektur[cite: 122]:
* [cite_start]**Frontend (Präsentationsschicht):** Realisiert mit **NiceGUI**, ausgeführt im Browser als Thin Client[cite: 123, 126].
* [cite_start]**Backend (Anwendungslogik):** Objektorientierte Programmierung in **Python** zur Abbildung der Businesslogik (Klassen für Bewohner, Ausgaben, Aufgaben)[cite: 128, 131].
* [cite_start]**Datenbank (Persistenzschicht):** Speicherung der Daten in **SQLite** unter Verwendung von **SQLAlchemy** als Object-Relational Mapper (ORM)[cite: 132].

## 4. User Stories
* *Als Mitbewohner möchte ich eine Ausgabe erfassen können, damit das System den Betrag gerecht auf alle aufteilt.*
* *Als Mitbewohner möchte ich sehen, welches "Ämtli" mir diese Woche zugewiesen wurde, damit die WG sauber bleibt.*
* *Als Admin der WG möchte ich neue Mitbewohner hinzufügen können, damit die Finanzberechnung aktuell bleibt.*

## 5. Verwendete Bibliotheken & Tools
* [cite_start]**Python 3.x** [cite: 22]
* [cite_start]**NiceGUI** (Frontend-Framework) [cite: 123]
* [cite_start]**SQLAlchemy** (Datenbank-ORM) [cite: 32, 132]
* [cite_start]**Pydantic** (Datenvalidierung) [cite: 27]
* [cite_start]**Visual Studio Code** (Entwicklungsumgebung) [cite: 43]

## 6. Arbeitsaufteilung (Initiales Konzept)
[cite_start]Gemäss den Richtlinien ist jedes Teammitglied für einen substanziellen Teil des Codes verantwortlich[cite: 109, 141]. [cite_start]Die Beiträge werden über die GitHub-Commits validiert[cite: 110, 142].

* [cite_start]**Mitglied 1:** Entwicklung der Datenmodelle (Klassen), Datenbank-Setup und SQLAlchemy-Integration[cite: 132].
* [cite_start]**Mitglied 2:** Gestaltung des User Interface (UI) mit NiceGUI und Verknüpfung der Frontend-Komponenten[cite: 128].
* [cite_start]**Mitglied 3:** Implementierung der Berechnungslogik (Finanz-Algorithmen) und der Ämtli-Verwaltungslogik[cite: 131].

## 7. Installation & Ausführung
1. Repository klonen.
2. Abhängigkeiten installieren: `pip install nicegui sqlalchemy`.
3. Anwendung starten: `python main.py`.
4. Die App ist im Browser unter `http://localhost:8080` erreichbar.
