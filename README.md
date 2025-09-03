#  			Wetterweiser





Wetterweiser ist ein Python-Tool zur Analyse, Visualisierung und Verwaltung von Wetterdaten – mit CSV-Support, Plots und optionalem Live-Import von OpenWeatherMap.“



## **Inhalt:**



* **Datenaufbereitung**

   Einlesen, Bereinigen und Speichern von Wetterdaten (CSV-Dateien).





* **Datenvisualisierung**

   Darstellung von Temperatur-, Niederschlags- und Sonnenstundenverläufen über verschiedene Zeiträume.





* **Statistische Auswertung**

   Berechnung von Durchschnitts-, Minimal- und Maximalwerten sowie Gesamtniederschlag und gesamten Sonnenstunden.







## **Voraussetzung:**



* **Python 3.x**
* **Bibliotheken: pandas, matplotlib, seaborn, numpy, streamlit, requests**





## **Installation der Bibliotheken:**



* pip install pandas matplotlib seaborn numpy streamlit requests







## **Ziel:**



* Analyse von Temperaturverläufen, Niederschlag und Sonnenstunden aus realen oder simulierten Messdaten.
* Modularer Aufbau für zukünftige Erweiterungen, z. B. Wettervorhersage per Machine Learning.
* Flexible Handhabung von CSV-Daten mit Import, Export und Update-Funktionalität.





## **Funktionen:**



* Datenverwaltung



* CSV-Dateien einlesen und als Messungen speichern



* Messungen manuell hinzufügen



* Live-Wetterdaten über OpenWeatherMap abrufen



* Wettersimulation für beliebige Tage und Orte



* Einzelne oder mehrere Messungen löschen



* *Download der aktuellen Wetterdaten als CSV*



* Statistische Auswertung



* Durchschnittstemperatur berechnen



* Maximal- und Minimaltemperaturen anzeigen



* Gesamtniederschlag und gesamte Sonnenstunden summieren



* Visualisierung



* Temperaturverlauf über Zeit plotten



* Niederschlags- und Sonnenstundenverlauf der letzten 7 Tage



* Monatsvergleich: Niederschlag und Sonnenstunden, inklusive historischer Daten



* Plots können als PNG-Dateien gespeichert oder direkt angezeigt werden







## **Nutzung:**







* Lade vorhandene CSV-Dateien hoch oder beginne mit neuen Messungen.



* Füge manuelle Messungen hinzu oder simuliere/abrufe Live-Daten.



* Analysiere die Daten über die eingebauten Statistik- und Plotfunktionen.



* Lade die aktuelle Datensammlung als CSV herunter, um sie beim nächsten Start wieder zu verwenden.







## **Erweiterungsmöglichkeiten:**



* Machine-Learning-Vorhersagen auf Basis der gespeicherten Daten



* Erweiterte Filter- und Sortierfunktionen für die Messungen



* Interaktive Plots mit Tooltips und Zoom-Funktion







## **Projektstruktur:**







**WetterProjekt/**

**├── README.md                  |   Projektdokumentation**

**├── wetter\_messung.py          |   Klasse `WetterMessung`**

**├── wetter\_daten.py            |   Klasse `WetterDaten`**

**├── wetter\_plots.py            |   Klasse `WetterPlots`**

**├── wetter\_analyse.py          |   Klasse `WetterAnalyse`**

**├── data/                      |   CSV-Dateien mit Messungen**

**│   └── beispiel.csv**

**├── plots/                     |   generierte Diagramme**

**│   └── temperatur.png**

**└── tests/                     |   Unittests**

    \*\*└── test\\\_wetter\\\_daten.py\*\*















## **Lizenz:**



* MIT-Lizenz





**Autor: Legacy**

