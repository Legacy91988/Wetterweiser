# 🌤️ Wetterweiser

Ein interaktives **Streamlit-Dashboard** zur Verwaltung, Analyse und Prognose von Wetterdaten.  
Das Tool erlaubt die **manuelle Eingabe**, **Simulation** oder den **Abruf von Live-Wetterdaten** über die OpenWeather-API.  
Alle Messungen können in einem GitHub-Repository gespeichert und später wieder importiert werden.

---

## 📑 Inhalt

- Verwaltung von Wetterdaten (manuell, simuliert, live)  
- Speicherung & Laden der Daten aus GitHub (JSON)  
- CSV-Export aller Daten  
- Analysefunktionen:  
  - Jahresstatistik (Durchschnittswerte, Extremwerte)  
  - 3-Tages-Prognosen (verschiedene Methoden)  
  - Vergleich der letzten 7 Tage  
  - Monatsvergleich (aktuelles vs. letztes Jahr)  
- Interaktive Diagramme mit Matplotlib  

---

## ⚙️ Voraussetzungen

- **Python 3.9+**  
- Installierte Pakete (z. B. per `pip install -r requirements.txt`):  
streamlit
pandas
numpy
matplotlib
requests
- Streamlit Secrets mit den Zugangsdaten:
- GitHub Token + Repo für Speicherung der Wetterdaten
- OpenWeather API-Key für Live-Wetterdaten

---

## 🎯 Ziel

Dieses Projekt soll es ermöglichen, Wetterdaten zentral zu sammeln, zu speichern und visuell aufzubereiten.  
Durch flexible Eingabemethoden (manuell, Simulation, Live-Daten) eignet es sich sowohl für Übungszwecke als auch für kleine private Wetterstationen.

---

## 🔧 Funktionen

- Manuelle Eingabe von Temperatur, Niederschlag und Sonnenstunden  
- Simulation von Wetterdaten über mehrere Tage  
- Abruf von Live-Daten über die OpenWeather-API  
- Speicherung der Daten als JSON in GitHub  
- Export aller Wetterdaten als CSV  
- Analyse & Visualisierung von Trends und Statistiken  

---

## 📂 Projektstruktur

wetterweiser/
├── app/
│ └── wetterweiser.py
├── data/
│ └── wetterdaten.json
├── docs/
│ └── README.md
├── requirements.txt
└── .gitignore


---

## 🖥️ Lokale Installation & Ausführung

1. **Repository klonen**

   ```bash
   git clone https://github.com/DEIN_USERNAME/Wetterweiser.git
   cd Wetterweiser

2. **Virtuelle Umgebung erstellen & aktivieren (empfohlen)**

python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

3. **Abhängigkeiten installieren**

pip install -r requirements.txt

4. **Streamlit-Secrets konfigurieren**

Lege im Projektordner einen Ordner .streamlit an und darin die Datei secrets.toml mit folgendem Inhalt:

[Legacy91988]
Wetterweiser = "Legacy91988/Wetterweiser"

github_token = "DEIN_GITHUB_TOKEN"

OWM_API_KEY = "DEIN_OPENWEATHERMAP_KEY"

[dev]
debug_password = "DEIN_DEV_PASSWORT"

5. **App starten**

streamlit run app/wetterweiser.py


🔮 Erweiterungsmöglichkeiten

Erweiterung der Prognosemodelle (z. B. Machine Learning)

Unterstützung für mehrere Wetter-APIs

Integration einer Benutzerverwaltung

Export in weitere Formate (Excel, Datenbanken)

Automatischer Scheduler für tägliche Live-Datenabfragen

📜 Lizenz

MIT-Lizenz
