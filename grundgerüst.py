import streamlit as st
import pandas as pd
import numpy as np
import datetime
import random
import requests
import matplotlib.pyplot as plt

# --------------------------
# Datenmodell
# --------------------------
class Quelle:
    MANUELL = "Manuell"
    SIMULIERT = "Simuliert"
    LIVE = "Live"


class WetterMessung:
    def __init__(self, datum, temperatur, niederschlag, sonnenstunden, quelle=Quelle.MANUELL, standort="Unbekannt", id=None):
        self.id = id or f"{datum.strftime('%Y%m%d%H%M%S')}_{random.randint(100,999)}"
        self.datum = datum
        self.temperatur = temperatur
        self.niederschlag = niederschlag
        self.sonnenstunden = sonnenstunden
        self.quelle = quelle
        self.standort = standort


class WetterDaten:
    def __init__(self):
        self.messungen = []

    def hinzufuegen(self, messung: WetterMessung):
        pass

    def loeschen(self, id: str):
        pass

    def als_dataframe(self):
        return pd.DataFrame([{
            "ID": m.id,
            "Datum": m.datum,
            "Temperatur": m.temperatur,
            "Niederschlag": m.niederschlag,
            "Sonnenstunden": m.sonnenstunden,
            "Quelle": m.quelle,
            "Standort": m.standort
        } for m in self.messungen]) if self.messungen else pd.DataFrame()

    def import_github_json(self):
        try:
            # Platzhalter für echten Import
            pass
        except Exception as e:
            st.error(f"Fehler beim Laden der GitHub-Daten: {e}")

    def export_github_json(self):
        try:
            # Platzhalter für echten Export
            pass
        except Exception as e:
            st.error(f"Fehler beim Speichern in GitHub: {e}")


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

    # Diagramme
    def plot_3tage_prognose(self, ort_filter="Alle"):
        pass

    def plot_7tage_vergleich(self, ort_filter="Alle"):
        pass

    def plot_monatsvergleich(self, ort_filter="Alle"):
        pass


# --------------------------
# App-Funktionen (Platzhalter)
# --------------------------
def manuelle_eingabe(wd):
    pass


def wettersimulation(wd):
    pass


def live_wetterdaten(wd):
    # API darf bleiben
    st.subheader("Live-Wetterdaten hinzufügen")
    api_key = st.secrets["openweather"]["api_key"]
    live_ort = st.text_input("Ort für Live-Wetter", "Berlin")
    if st.button("Live-Daten abrufen"):
        datum_live = datetime.datetime.now()
        if api_key.strip():
            try:
                url = f"http://api.openweathermap.org/data/2.5/weather?q={live_ort}&appid={api_key}&units=metric"
                response = requests.get(url, timeout=5).json()
                temperatur_live = response["main"]["temp"]
                niederschlag_live = response.get("rain", {}).get("1h", 0)
                sunrise_local = datetime.datetime.fromtimestamp(response["sys"]["sunrise"])
                sunset_local = datetime.datetime.fromtimestamp(response["sys"]["sunset"])
                tageslaenge = (sunset_local - sunrise_local).total_seconds() / 3600
                wolken = response.get("clouds", {}).get("all", 0)
                sonnenstunden_live = round(max(0, tageslaenge * (1 - wolken / 100)), 1)

                wd.hinzufuegen(WetterMessung(
                    datum_live, temperatur_live, niederschlag_live, sonnenstunden_live,
                    quelle=Quelle.LIVE, standort=live_ort
                ))
                wd.export_github_json()
                st.success(f"Live-Wetter für {live_ort} hinzugefügt!")
            except Exception as e:
                st.error(f"API-Fehler: {e}")
        else:
            st.warning("⚠️ Kein API-Key gefunden – Live-Daten können nicht abgerufen werden.")


def download_wetterdaten_csv(wd):
    pass


def anzeigen_und_loeschen(wd):
    pass


# --------------------------
# Haupt-App
# --------------------------
def main():
    st.title("🌤️ Wetterweiser ")
    st.info("Grundgerüst. Funktionen folgen.")

    # Instanz der Analyseklasse
    wd = WetterAnalyse()
    wd.import_github_json()


if __name__ == "__main__":
    main()
