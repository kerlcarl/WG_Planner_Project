# WG-Planner Project
# WG-Planner: Finanzen & Aufgabenverwaltung

## 1. Projektbeschreibung
[cite_start]Dieses Repository enthält den Code für den **WG-Planner**, eine browserbasierte Anwendung zur koordinativen Unterstützung von Wohngemeinschaften (WG)[cite: 106, 107]. [cite_start]Entwickelt im Rahmen des Moduls „Objektorientierte Programmierung“ (26FS) an der Hochschule für Wirtschaft FHNW, zielt das Projekt darauf ab, wiederkehrende Aufgaben und gemeinsame Ausgaben strukturiert zu verwalten[cite: 3, 21].

[cite_start]Die Anwendung ist als vollwertige Web-Applikation mit Frontend, Backend und Datenbank implementiert[cite: 107, 122]. Sie bietet Funktionen zum Management von Mitbewohner*innen, ein Shared-Expense-Tracking mit automatischer Abrechnung sowie einen interaktiven Ämtli-Plan mit integrierter Kalenderansicht.

## 2. Kernfunktionen
[cite_start]Die Anwendung minimiert den administrativen Aufwand in einer WG und erhöht die Transparenz durch zentrale Datenhaltung[cite: 105].

### ✔ Aktuell implementiert
* **Mitbewohner*innen-Verwaltung** – Vollständiges CRUD (Erstellen, Lesen, Bearbeiten, Löschen) von Profilen inkl. Tastatur-Unterstützung (Enter-Taste) für eine schnelle Eingabe.
* **Shared-Expense-Tracker** – Erfassung gemeinsamer Ausgaben mit automatischer Berechnung der Salden pro Person sowie einem detaillierten Ausgabenverlauf[cite: 24, 132].
* **Ämtli-Plan & Kalender** – Verwaltung von Haushaltsaufgaben mit Checkbox-Status, Rotationslogik und Visualisierung fälliger Aufgaben in einem interaktiven Kalender.
* **Responsive Web-Frontend** – Intuitive, helle Benutzeroberfläche ohne Dark Mode, gestaltet mit NiceGUI für flüssige Bedienung ohne Seiten-Reloads[cite: 123, 126].

## 3. Technische Architektur & Design
Die Lösung ist als klassische Drei-Schichten-Architektur implementiert[cite: 122]:

* **Presentation Layer (Frontend)** – Realisiert mit **NiceGUI**. [cite_start]Der Browser fungiert als Thin Client und rendert UI-Komponenten dynamisch[cite: 123, 126].
* **Application Layer (Backend)** – Objektorientierte Programmierung in **Python**. [cite_start]Die Geschäftslogik (z. B. Kostenaufteilung `calculate_share`) ist in modulare Klassen gekapselt[cite: 131].
* [cite_start]**Persistence Layer** – Lokale **SQLite**-Datenbank mit **SQLAlchemy** als Object-Relational Mapper (ORM), um direktes SQL zu vermeiden[cite: 32, 132].

### UML-Klassendiagramm & ER-Modell
[cite_start]Das Design nutzt Assoziationen zwischen den Domänenobjekten[cite: 26]:
* **MitbewohnerDB**: Zentrales Objekt für Nutzer*innendaten (Tabelle `users`).
* **Expense**: Speichert Beträge und Kategorien; berechnet Anteile (Tabelle `expenses`).
* **Task**: Verwaltet Ämtli und deren Zuweisung (Tabelle `tasks`).
* **expense_participants**: Verknüpfungstabelle (n:m) für die Kostenaufteilung zwischen Mitbewohner*innen.

## 4. Qualitätssicherung (Testfälle)
Zur Sicherstellung der Funktionalität wurden folgende Testfälle definiert:
1. **TC-01:** Hinzufügen einer neuen Person via Enter-Taste und Validierung der Anzeige.
2. **TC-02:** Korrekte mathematische Aufteilung eines Rechnungsbetrags auf mehrere Beteiligte.
3. **TC-03:** Persistenz-Check der Ämtli-Statusänderungen nach Browser-Neustart.

## 5. User Stories
* **Finanzen:** Als Mitbewohner*in möchte ich Ausgaben erfassen, damit das System die Abrechnung automatisch für alle übernimmt.
* **Organisation:** Als Mitbewohner*in möchte ich meine Aufgaben im Kalender sehen, um meinen Haushaltstag zu planen.
* **Transparenz:** Als WG-Mitglied möchte ich den Ausgabenverlauf einsehen, um die monatlichen Kosten zu verstehen.

## 6. Verwendete Bibliotheken & Tools
* **Python 3.11+** [cite: 21]
* [cite_start]**NiceGUI** – Frontend-Framework [cite: 123]
* [cite_start]**SQLAlchemy** – ORM für die Datenbankanbindung [cite: 32]
* **SQLite** – Lokale Datenbankdatei (`wg_planner.db`) [cite: 132]

## 7. Installation & Ausführung
1. Repository klonen.
2. Abhängigkeiten installieren: `pip install -r requirements.txt`.
3. Anwendung starten: `python main.py`.
4. Im Browser öffnen: `http://localhost:8081`[cite: 126].

## 8. Projektmanagement & Team
Das Projekt ist eine Gruppenarbeit von drei Studierenden[cite: 86, 106].
* **Backend:** Datenbank-Design & SQLAlchemy-Modelle.
* **Frontend:** UI-Design mit NiceGUI & Event-Handling.
* **Logik:** Finanz-Algorithmen & Aufgaben-Rotation.
