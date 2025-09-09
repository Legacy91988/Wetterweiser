import streamlit as st
import pandas as pd
import uuid
import datetime

# --------------------------
# Datenklassen
# --------------------------
class WetterMessung:
    def __init__(self, datum, temperatur, niederschlag, sonnenstunden=None,
                 id=None, standort="Musterstadt"):
        pass

    def als_dict(self):
        pass

# --------------------------
# Basisklasse
# --------------------------
class WetterDaten:
    def __init__(self):
        pass

    def hinzufuegen(self, messung):
        pass

    def als_dataframe(self):
        pass

    def loesche_messungen(self, ids):
        pass

# --------------------------
# Erweiterung: WetterAnalyse
# --------------------------
class WetterAnalyse(WetterDaten):
    def extremwerte(self, ort_filter="Alle"):
        pass

    def jahresstatistik(self, ort_filter="Alle"):
        pass

# --------------------------
# Haupt-App
# --------------------------
def main():
    st.title("🌤️ Wetterweiser")
    wd = WetterAnalyse()
    st.write("App gestartet ")

if __name__ == "__main__":
    main()
