import streamlit as st                  # Web-App-Oberfläche
import pandas as pd                     # für Tabellen und Daten
import numpy as np                      # mathematische Berechnungen
import matplotlib.pyplot as plt         # für Diagramme
import datetime                         # Datum & Uhrzeit
import random                           # für die Zufallswerte
import requests                         # für HTTP- Anfragen
import uuid                             # für eindeutige ID´s
from enum import Enum                 # Quelle der Wetterdaten
import base64                           # zum kodieren/decodieren der Json Daten
import json                             # Laden und Speichern
import traceback                        # für Fehlermeldungungen im Debug Modus

# Konstanten & Enums
class Quelle(Enum):
    MANUELL = "Manuell"
    SIMULIERT = "Simuliert"
    LIVE = "Live"

# GitHub-Konfiguration aus Streamlit Secrets

GITHUB_REPO = st.secrets["Legacy91988"]["Wetterweiser"]
GITHUB_BRANCH = st.secrets["Legacy91988"].get("branch", "main")
GITHUB_TOKEN = st.secrets["Legacy91988"]["github_token"]
GITHUB_JSON_PATH = "wetterdaten.json"

class WetterMessung:
    def __init__(self, datum, temperatur, niederschlag, sonnenstunden=None, id=None, quelle=Quelle.MANUELL, standort="Musterstadt"):
        # Eindeutige ID´s
        self.id = id or str(uuid.uuid4())
        self.datum = pd.to_datetime(datum)
        self.temperatur = temperatur
        self.niederschlag = niederschlag
        self.sonnenstunden = sonnenstunden if sonnenstunden is not None else round(random.uniform(0, 12), 1)
        # Sicherstellen, dass 'Quelle' immer als Enum behandelt wird
        if isinstance(quelle, Quelle):
            self.quelle = quelle.value
        else:
            try:
                self.quelle = Quelle(quelle).value
            except ValueError:
                self.quelle = Quelle.MANUELL.value  # Fallback
        self.standort = standort

    def als_dict(self):
        # Wandelt die Messung in ein Dictionary um
        return {
            "ID": self.id,
            "Datum": self.datum.strftime("%Y-%m-%d %H:%M:%S"),
            "Temperatur": self.temperatur,
            "Niederschlag": self.niederschlag,
            "Sonnenstunden": self.sonnenstunden,
            "Quelle": self.quelle,
            "Standort": self.standort
        }


class WetterDaten:
    def __init__(self):
        self.messungen = []

    def hinzufuegen(self, messung: WetterMessung):
        self.messungen.append(messung)

    def existiert_eintrag(self, datum, standort):
        for m in self.messungen:
            if m.standort == standort and m.datum.date() == pd.to_datetime(datum).date():
                return True
        return False

    def ersetze_eintrag(self, datum, standort, neue_messung):
        # löscht vorhandene Messung und fügt die neue ein
        self.messungen = [m for m in self.messungen if not (m.standort == standort and m.datum.date() == pd.to_datetime(datum).date())]
        self.messungen.append(neue_messung)

    # Messung nach ID löschen
    def loeschen(self, messung_id):
        self.messungen = [m for m in self.messungen if m.id != messung_id]

    def als_dataframe(self):
        df = pd.DataFrame([m.als_dict() for m in self.messungen])
        if not df.empty:
            df['Datum'] = pd.to_datetime(df['Datum'])
            df = df.sort_values('Datum', ascending=False)
        return df

    def import_github_json(self):
        # Importiert Messdaten von GitHub aus der JSON-Datei
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_JSON_PATH}?ref={GITHUB_BRANCH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

        try:
            response = requests.get(url, headers=headers, timeout=5).json()
        except Exception as e:
            st.error(f"Fehler beim Zugriff auf GitHub: {e}")
            return

        if "content" not in response:
            msg = response.get("message", "Unbekannter Fehler beim Laden der Daten.")
            st.info(f"GitHub-API-Fehler: {msg}")
            return

        try:
            content = base64.b64decode(response["content"]).decode("utf-8")
            data = json.loads(content)
        except Exception as e:
            st.error(f"Fehler beim Dekodieren der GitHub-Daten: {e}")
            return

        for eintrag in data:
            eintrag_korrigiert = {
                'id': eintrag.get("ID"),
                'datum': eintrag.get("Datum"),
                'temperatur': eintrag.get("Temperatur"),
                'niederschlag': eintrag.get("Niederschlag"),
                'sonnenstunden': eintrag.get("Sonnenstunden"),
                'quelle': eintrag.get("Quelle"),
                'standort': eintrag.get("Standort")
            }
            wetter = WetterMessung(**eintrag_korrigiert)
            if not self.existiert_eintrag(wetter.datum, wetter.standort):
                self.hinzufuegen(wetter)

        st.info(f"Einträge von GitHub importiert.")

    @staticmethod
    def load_github_data(debug=False):
        # lädt Wetterdaten aus GitHub , für die lokale Version
        def _load():
            wd = WetterDaten()
            wd.import_github_json()
            return wd

        if debug:
            return _load()
        else:
            @st.cache_data(ttl=300)
            def cached_load():
                return _load()
            return cached_load()

    def export_github_json(self, debug_mode=False):
        if not GITHUB_TOKEN:
            st.warning("Kein GitHub-Token gesetzt – Daten nicht gespeichert.")
            return

        df = [m.als_dict() for m in self.messungen]
        json_data = json.dumps(df, indent=2)
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}

        # Prüfen ob Datei existiert
        url_get = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_JSON_PATH}?ref={GITHUB_BRANCH}"
        r_get = requests.get(url_get, headers=headers)
        sha = r_get.json()["sha"] if r_get.status_code == 200 else None

        payload = {
            "message": f"Update Wetterdaten {datetime.datetime.now()}",
            "content": base64.b64encode(json_data.encode()).decode(),
            "branch": GITHUB_BRANCH
        }
        if sha:
            payload["sha"] = sha

        if debug_mode:
            st.text_area("🔍 GitHub-Payload", json.dumps(payload, indent=2), height=250)

        url_put = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_JSON_PATH}"
        r_put = requests.put(url_put, headers=headers, data=json.dumps(payload))
        if r_put.status_code in [200, 201]:
            st.success("Daten erfolgreich auf GitHub gespeichert!")
        else:
            st.error(f"Fehler beim Speichern: {r_put.text}")

# Analyse & Diagramme

class WetterAnalyse(WetterDaten):
    def extremwerte(self, ort_filter="Alle"): pass
    def jahresstatistik(self, ort_filter="Alle"): pass
    def durchschnittstemperatur(self): pass
    def gesamtniederschlag(self): pass
    def gesamte_sonnenstunden(self): pass
    def prognose_temperatur(self, tage=3): pass
    def prognose_niederschlag(self, tage=3): pass
    def plot_3tage_prognose(self, ort_filter="Alle"): pass
    def plot_7tage_vergleich(self, ort_filter="Alle"): pass
    def plot_monatsvergleich(self, ort_filter="Alle"): pass

# --------------------------
# App-Funktionen
# --------------------------
def manuelle_eingabe(wd):
    st.subheader("Manuelle Eingabe")
    datum = st.date_input("Datum")
    standort = st.text_input("Ort")
    temp_min = st.number_input("Min °C", value=15.0)
    temp_max = st.number_input("Max °C", value=25.0)
    temperatur = round((temp_min + temp_max)/2,1)
    nied = st.number_input("Niederschlag (mm)", value=0.0)
    sonne = st.number_input("Sonnenstunden", value=6.0)

    if st.button("Hinzufügen"):
        datum_dt = datetime.datetime.combine(datum, datetime.datetime.now().time())
        if wd.existiert_eintrag(datum_dt, standort):
            st.warning(f"Für {standort} am {datum_dt.date()} existiert bereits ein Eintrag!")
        else:
            wd.hinzufuegen(WetterMessung(datum_dt, temperatur, nied, sonne, quelle=Quelle.MANUELL, standort=standort))
            wd.export_github_json()
            st.success(f"{standort} am {datum_dt.date()} hinzugefügt!")

def wettersimulation(wd):
    st.subheader("Simulation")
    ort = st.text_input("Ort", "Musterstadt")
    tage = st.number_input("Tage", 1, 30, 7)
    if st.button("Simulieren"):
        heute = datetime.datetime.now()
        for i in range(tage):
            datum = heute - datetime.timedelta(days=i)
            wd.hinzufuegen(WetterMessung(
                datum,
                round(random.uniform(15,30),1),
                round(random.uniform(0,10),1),
                round(random.uniform(0,12),1),
                quelle=Quelle.SIMULIERT,
                standort=ort
            ))
        wd.export_github_json()
        st.success(f"{tage} Tage simuliert für {ort}!")

def live_wetterdaten(wd, ort):
    # OWM_API_KEY aus Streamlit Secrets holen
    OWM_API_KEY = st.secrets["Legacy91988"]["OWM_API_KEY"]

    if not OWM_API_KEY:
        st.error("OpenWeatherMap API-Key ist nicht gesetzt!")
        return

    url = f"http://api.openweathermap.org/data/2.5/weather?q={ort}&appid={OWM_API_KEY}&units=metric&lang=de"
    try:
        data = requests.get(url, timeout=5).json()
    except Exception as e:
        st.error(f"Fehler beim Abrufen der Live-Daten: {e}")
        return

    temp = data.get("main", {}).get("temp")
    niederschlag = data.get("rain", {}).get("1h", 0)

    if temp is None:
        msg = data.get("message", "Keine Temperaturdaten erhalten.")
        st.error(f"OpenWeatherMap-Fehler: {msg}")
        return

    messung = WetterMessung(
        datum=datetime.datetime.now(),
        temperatur=temp,
        niederschlag=niederschlag,
        sonnenstunden=0,
        quelle=Quelle.LIVE,
        standort=ort
    )
    if not wd.existiert_eintrag(messung.datum, ort):
        wd.hinzufuegen(messung)
        st.success(f"Live-Daten für {ort} hinzugefügt: {temp}°C, {niederschlag}mm")
    else:
        st.info(f"Für {ort} existiert bereits ein Eintrag für heute.")

def download_wetterdaten_csv(wd): pass

def anzeigen_und_loeschen(wd):
    st.subheader("Messungen anzeigen & löschen")
    df = wd.als_dataframe()
    if df.empty:
        st.info("Keine Daten vorhanden.")
        return

    orte = df['Standort'].unique()
    ort_filter = st.selectbox("Ort auswählen:", np.append("Alle", orte))
    if ort_filter != "Alle":
        df = df[df['Standort'] == ort_filter]

    st.dataframe(df[['ID','Standort','Datum','Temperatur','Niederschlag','Sonnenstunden']])

    df_sorted = df.sort_values('Datum', ascending=False)
    eintraege = [
        f"{row['ID']} | {row['Standort']} | {row['Datum'].strftime('%d.%m.%Y')} | {row['Temperatur']}°C | {row['Niederschlag']}mm | {row['Sonnenstunden']}h"
        for _, row in df_sorted.iterrows()
    ]

    if eintraege:
        auswahl = st.multiselect("Einträge zum Löschen auswählen:", options=eintraege)
        if auswahl and st.button("Löschen"):
            for eintrag in auswahl:
                eintrag_id = eintrag.split(" | ")[0]
                wd.loeschen(eintrag_id)
            wd.export_github_json()
            st.success(f"{len(auswahl)} Messung(en) gelöscht!")
            st.rerun()

# Haupt-App
def main():
    st.title("🌤️ Wetterweiser")
    st.info("Dateneingabe funktioniert – weitere Funktionen folgen")

    wd = WetterAnalyse()
    wd.import_github_json()

    st.subheader("Daten hinzufügen")
    modus = st.radio("Modus", ("Manuelle Eingabe", "Simulation", "Live-Abfrage"))
    if modus == "Manuelle Eingabe":
        manuelle_eingabe(wd)
    elif modus == "Simulation":
        wettersimulation(wd)
    elif modus == "Live-Abfrage":
        ort = st.text_input("Ort für Live-Abfrage", "Musterstadt")
        if st.button("Live-Daten abrufen"):
            live_wetterdaten(wd, ort)

    download_wetterdaten_csv(wd)
    anzeigen_und_loeschen(wd)

if __name__ == "__main__":
    main()
