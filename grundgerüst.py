import streamlit as st               # Web-App-Oberfläche
import pandas as pd                  # für Tabellen und Daten
import numpy as np                   # mathematische Berechnungen
import matplotlib.pyplot as plt      # für Diagramme
import datetime                      # Datum & Uhrzeit
import random                        # für die Zufallswerte
import requests                      # für HTTP- Anfragen
import uuid                          # für eindeutige ID´s
import base64                        # zum kodieren/decodieren der Json Daten
import json                          # Laden und Speichern
import traceback                     # für Fehlermeldungungen im Debug Modus


# Konstanten & Enums
class Quelle:
    MANUELL = "Manuell"
    SIMULIERT = "Simuliert"
    LIVE = "Live"


# GitHub-Konfiguration aus Streamlit Secrets
# Repo-Name, Branch, Token und Pfad zur JSON-Datei mit Wetterdaten

GITHUB_REPO = st.secrets["Legacy91988"]["Wetterweiser"]
GITHUB_BRANCH = st.secrets["Legacy91988"].get("branch", "main")
GITHUB_TOKEN = st.secrets["Legacy91988"]["github_token"]
GITHUB_JSON_PATH = "wetterdaten.json"


class WetterMessung:
    def __init__(self, datum, temperatur, niederschlag, sonnenstunden, quelle=Quelle.MANUELL, standort="Unbekannt", id=None):
        # eindeutige ID´s
        self.id = id or f"{datum.strftime('%Y%m%d%H%M%S')}_{random.randint(100,999)}"
        self.datum = datum
        self.temperatur = temperatur
        self.niederschlag = niederschlag
        self.sonnenstunden = sonnenstunden
        self.quelle = quelle
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
            if m.standort == standort and m.datum.date() == datum.date():
                return True
        return False

    def ersetze_eintrag(self, datum, standort, neue_messung):
        # löscht vorhandene Messung und fügt die neue ein
        self.messungen = [m for m in self.messungen if not (m.standort == standort and m.datum.date() == datum.date())]
        self.messungen.append(neue_messung)

    def loeschen(self, id: str):
        # Messung nach ID löschen
        pass

    def als_dataframe(self):
        # Alle Messungen als DataFrame zurückgeben
        return pd.DataFrame([m.als_dict() for m in self.messungen]) if self.messungen else pd.DataFrame()

    def import_github_json(self, debug_mode=False):
        if not GITHUB_TOKEN:
            st.warning("Kein GitHub-Token gesetzt – keine Daten geladen.")
            return

        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_JSON_PATH}?ref={GITHUB_BRANCH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}

        try:
            response = requests.get(url, headers=headers, timeout=5).json()

            if debug_mode:
                st.text_area("🔍 GitHub-Response", json.dumps(response, indent=2), height=250)

            if "content" not in response:
                st.info("Keine Daten auf GitHub gefunden.")
                return

            content = response["content"]
            decoded = base64.b64decode(content).decode()
            data = json.loads(decoded)

            for entry in data:
                # wandelt die Namen um
                mapped_entry = {
                    "id": entry.get("ID", None),
                    "datum": pd.to_datetime(entry.get("Datum")) if "Datum" in entry else datetime.datetime.now(),
                    "temperatur": entry.get("Temperatur", 0),
                    "niederschlag": entry.get("Niederschlag", 0),
                    "sonnenstunden": entry.get("Sonnenstunden", 0),
                    "quelle": entry.get("Quelle", Quelle.MANUELL),
                    "standort": entry.get("Standort", "Unbekannt")
                }

                if mapped_entry['id'] not in [m.id for m in self.messungen]:
                    try:
                        self.hinzufuegen(WetterMessung(**mapped_entry))
                    except ValueError as e:
                        st.warning(f"Ungültige Messung übersprungen: {e}")

        except Exception as e:
            st.error(f"Fehler beim Laden der GitHub-Daten: {e}")
            if debug_mode:
                st.text_area("🔍 Traceback", traceback.format_exc(), height=200)

    def export_github_json(self, debug_mode=False):
        # Daten auf GitHub speichern
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

            # Debug-Ausgabe
            if debug_mode:
                st.text_area("🔍 GitHub-Payload", json.dumps(payload, indent=2), height=250)

            url_put = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_JSON_PATH}"
            r_put = requests.put(url_put, headers=headers, data=json.dumps(payload))
            if r_put.status_code in [200, 201]:
                st.success("Daten erfolgreich auf GitHub gespeichert!")
            else:
                st.error(f"Fehler beim Speichern: {r_put.text}")


class WetterAnalyse(WetterDaten):
    def extremwerte(self, ort_filter="Alle"):
        pass

    def jahresstatistik(self, ort_filter="Alle"):
        pass

    def durchschnittstemperatur(self):
        pass

    def gesamtniederschlag(self):
        pass

    def gesamte_sonnenstunden(self):
        pass

    def prognose_temperatur(self, tage=3):
        pass

    def prognose_niederschlag(self, tage=3):
        pass

    def plot_3tage_prognose(self, ort_filter="Alle"):
        pass

    def plot_7tage_vergleich(self, ort_filter="Alle"):
        pass

    def plot_monatsvergleich(self, ort_filter="Alle"):
        pass


# --------------------------
# App-Funktionen
# --------------------------
def manuelle_eingabe(wd):
    st.subheader("Manuelle Eingabe")
    datum = st.date_input("Datum")
    standort = st.text_input("Ort")
    temp_min = st.number_input("Min °C", value=15.0)
    temp_max = st.number_input("Max °C", value=25.0)
    temperatur = round((temp_min + temp_max) / 2, 1)
    nied = st.number_input("Niederschlag (mm)", value=0.0)
    sonne = st.number_input("Sonnenstunden", value=6.0)

    if st.button("Hinzufügen"):
        datum_dt = datetime.datetime.combine(datum, datetime.datetime.now().time())

        # Prüfen, ob Eintrag für Datum + Standort schon existiert
        if wd.existiert_eintrag(datum_dt, standort):
            st.warning(f"Für {standort} am {datum_dt.date()} existiert bereits ein Eintrag!")
        else:
            wd.hinzufuegen(WetterMessung(datum_dt, temperatur, nied, sonne, quelle=Quelle.MANUELL, standort=standort))
            wd.export_github_json()
            st.success(f"{standort} am {datum_dt.date()} hinzugefügt!")




def wettersimulation(wd):
    st.subheader("Simulation")
    ort = st.text_input("Ort", "Musterstadt")
    # Anzahl der Tage für die Simulation auswählen , 1-30, 7-Standart
    tage = st.number_input("Tage", 1, 30, 7)
    if st.button("Simulieren"):
        heute = datetime.datetime.now()
        # Schleife für Anzahl Tage
        for i in range(tage):
            # Datum rückwärts berechnen
            datum = heute - datetime.timedelta(days=i)
            wd.hinzufuegen(WetterMessung(
                datum,
                round(random.uniform(15, 30), 1),
                round(random.uniform(0, 10), 1),
                round(random.uniform(0, 12), 1),
                quelle=Quelle.SIMULIERT,
                standort=ort
            ))
        wd.export_github_json()
        st.success(f"{tage} Tage simuliert für {ort}!")


def live_wetterdaten(wd, debug_mode=False):
    st.subheader("Live-Daten")
    api_key = st.secrets["openweather"]["api_key"]

    if "api_info_angezeigt" not in st.session_state:
        if api_key:
            st.info("API-Key wird automatisch aus den Streamlit Secrets verwendet.")
        else:
            st.warning("Kein API-Key gefunden – Live-Daten können nicht abgerufen werden.")
        st.session_state["api_info_angezeigt"] = True

    ort = st.text_input("Ort für Live-Wetter")
    if st.button("Abrufen"):
        datum = datetime.datetime.now()
        if not api_key.strip():
            st.error("Kein API-Key – Daten können nicht geladen werden.")
            return
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={ort}&appid={api_key}&units=metric"
            r = requests.get(url, timeout=5)
            data = r.json()

            # Debug: kompletten API-Response anzeigen
            if debug_mode:
                st.text_area("🔍 OpenWeather API Response", json.dumps(data, indent=2), height=250)

            if r.status_code != 200 or "main" not in data:
                st.error(f"API-Fehler ({r.status_code}): {data.get('message','Unbekannter Fehler')}")
                return

            temp = data["main"]["temp"]
            nied = data.get("rain", {}).get("1h", 0)
            sunrise = datetime.datetime.fromtimestamp(data["sys"]["sunrise"])
            sunset = datetime.datetime.fromtimestamp(data["sys"]["sunset"])
            tageslaenge = (sunset - sunrise).total_seconds() / 3600
            wolken = data.get("clouds", {}).get("all", 0)
            sonne = round(max(0, tageslaenge * (1 - wolken / 100)), 1)

            wd.hinzufuegen(WetterMessung(datum, temp, nied, sonne, quelle=Quelle.LIVE, standort=ort))
            wd.export_github_json(debug_mode=debug_mode)
            st.success(f"Live-Wetter für {ort} hinzugefügt!")

        except Exception as e:
            st.error(f"Fehler: {e}")
            if debug_mode:
                st.text_area("🔍 Traceback", traceback.format_exc(), height=200)


def download_wetterdaten_csv(wd):
    pass


def anzeigen_und_loeschen(wd):
    pass


# --------------------------
# Haupt-App
# --------------------------
def main():
    st.title("🌤️ Wetterweiser")
    st.info("Dateneingabe funktioniert - weitere Funktionen folgen")
    # Entwickler-Passwort prüfen
    dev_password = st.secrets["dev"]["debug_password"]
    eingabe = st.sidebar.text_input(
        "Entwickler-Passwort",
        type="password",
        key="dev_password_input"
    )
    ist_entwickler = eingabe == dev_password

    # Checkbox nur sichtbar, wenn Entwickler
    debug_mode = False
    if ist_entwickler:
        debug_mode = st.sidebar.checkbox(
            "🔍 Debug-Modus aktivieren",
            value=False,
            key="debug_mode"
        )
        if debug_mode:
            st.sidebar.success("🔍 Debug-Modus aktiv")

    # WetterAnalyse-Objekt erstellen und GitHub-Daten laden
    wd = WetterAnalyse()
    wd.import_github_json(debug_mode=debug_mode)

    if debug_mode:
        st.text_area(
            "🔍 Debug: GitHub-Daten geladen",
            str([m.als_dict() for m in wd.messungen]),
            height=200
        )

    # Abschnitt zum Hinzufügen von Daten
    st.subheader("Daten hinzufügen")
    modus = st.radio("Modus", ("Manuelle Eingabe", "Simulation", "Live-Abfrage"))

    if modus == "Manuelle Eingabe":
        manuelle_eingabe(wd)
    elif modus == "Simulation":
        wettersimulation(wd)
    elif modus == "Live-Abfrage":
        live_wetterdaten(wd, debug_mode=debug_mode)

    # CSV-Download
    download_wetterdaten_csv(wd)
    anzeigen_und_loeschen(wd)


if __name__ == "__main__":
    main()
