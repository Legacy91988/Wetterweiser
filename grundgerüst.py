import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
import random
import requests
import uuid
import json
from enum import Enum
import base64
import json
import os

# --------------------------
# Konstanten & Enums
# --------------------------
class Quelle(Enum):
    MANUELL = "manuell"
    SIMULIERT = "simuliert"
    LIVE = "live"

GITHUB_REPO = st.secrets["Legacy91988"]["Wetterweiser"]
GITHUB_BRANCH = st.secrets["Legacy91988"].get("branch", "main")
GITHUB_TOKEN = st.secrets["Legacy91988"]["github_token"]
GITHUB_JSON_PATH = "wetterdaten.json"

# --------------------------
# Datenklassen
# --------------------------
class WetterMessung:
    def __init__(self, *args, **kwargs):
        st.info("WetterMessung.__init__ noch nicht implementiert")
        pass

    def als_dict(self):
        st.info("WetterMessung.als_dict noch nicht implementiert")
        pass

class WetterDaten:
    def __init__(self):
        self.messungen = []

    def hinzufuegen(self, messung):
        st.info("WetterDaten.hinzufuegen noch nicht implementiert")
        pass

    def als_dataframe(self):
        st.info("WetterDaten.als_dataframe noch nicht implementiert")
        pass

    # --------------------------
    # GitHub JSON
    # --------------------------
    def import_github_json(self):
        if not GITHUB_TOKEN:
            st.warning("Kein GitHub-Token gesetzt – keine Daten geladen.")
            return
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_JSON_PATH}?ref={GITHUB_BRANCH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        try:
            response = requests.get(url, headers=headers, timeout=5).json()
            if "content" not in response:
                st.info("Keine Daten auf GitHub gefunden.")
                return
            content = response["content"]
            decoded = base64.b64decode(content).decode()
            data = json.loads(decoded)
            for entry in data:
                if entry['ID'] not in [m.id for m in self.messungen]:
                    self.hinzufuegen(WetterMessung(**entry))
        except Exception as e:
            st.error(f"Fehler beim Laden der GitHub-Daten: {e}")

    def export_github_json(self):
        if not GITHUB_TOKEN:
            st.warning("Kein GitHub-Token gesetzt – Daten nicht gespeichert.")
            return
        df = [m.als_dict() for m in self.messungen]
        json_data = json.dumps(df, indent=2)

        # Prüfen ob Datei existiert
        url_get = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_JSON_PATH}?ref={GITHUB_BRANCH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        r_get = requests.get(url_get, headers=headers)
        sha = None
        if r_get.status_code == 200:
            sha = r_get.json()["sha"]

        payload = {
            "message": f"Update Wetterdaten {datetime.datetime.now()}",
            "content": base64.b64encode(json_data.encode()).decode(),
            "branch": GITHUB_BRANCH
        }
        if sha:
            payload["sha"] = sha

        url_put = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_JSON_PATH}"
        r_put = requests.put(url_put, headers=headers, data=json.dumps(payload))
        if r_put.status_code in [200,201]:
            st.success("Daten erfolgreich auf GitHub gespeichert!")
        else:
            st.error(f"Fehler beim Speichern: {r_put.text}")

class WetterAnalyse(WetterDaten):
    def extremwerte(self, ort_filter="Alle"):
        st.info("WetterAnalyse.extremwerte noch nicht implementiert")
        pass

    def jahresstatistik(self, ort_filter="Alle"):
        st.info("WetterAnalyse.jahresstatistik noch nicht implementiert")
        pass

    def plot_3tage_prognose(self, ort_filter="Alle"):
        st.info("WetterAnalyse.plot_3tage_prognose noch nicht implementiert")
        pass

    def plot_7tage_vergleich(self, ort_filter="Alle"):
        st.info("WetterAnalyse.plot_7tage_vergleich noch nicht implementiert")
        pass

    def plot_monatsvergleich(self, ort_filter="Alle"):
        st.info("WetterAnalyse.plot_monatsvergleich noch nicht implementiert")
        pass

# --------------------------
# App-Funktionen
# --------------------------
def manuelle_eingabe(wd):
    st.info("manuelle_eingabe noch nicht implementiert")
    pass

def wettersimulation(wd):
    st.info("wettersimulation noch nicht implementiert")
    pass

def live_wetterdaten(wd):
    st.info("live_wetterdaten noch nicht implementiert")
    pass

# --------------------------
# Haupt-App
# --------------------------
def main():
    st.title("🌤️ Wetterweiser")
    wd = WetterAnalyse()
    wd.import_github_json()
    wd.export_github_json()  # Damit sichtbar, dass JSON-Funktionen laufen

if __name__ == "__main__":
    main()
