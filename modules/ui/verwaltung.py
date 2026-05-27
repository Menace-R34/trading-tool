import streamlit as st
import datetime
import pandas as pd
from modules.prognose_speicher import (
    lade_prognosehistorie,
    _lese_csv_sicher,
    DATEI_PROGNOSEN,
    speichere_standardwerte,
    loesche_historische_daten,
    _zeitstempel_str,
    _jetzt_berlin,
    hole_fixierungs_status,
    liste_backups_auf,
    loesche_alte_backups,
    stelle_backup_wieder_her
)
from modules.prognose_auswertung import berechne_trefferstatistik
from modules.prognose_optimierung import (
    schlage_standardwerte_vor,
    lade_vorschlaege_historie
)
from modules.ui_einstellungen import (
    hole_standard_einstellungen,
    hole_filter_settings_aus_session
)
from modules.ui_styling import baue_styler
from modules.region_logik import filtere_nach_region

def seite_prognosekontrolle():
    st.subheader("Prognosekontrolle")
    st.write("Historische Auswertung der Treffersicherheit.")
    st.caption(f"Letzte Aktualisierung: {_zeitstempel_str()} deutsche Zeit")

    df_hist = lade_prognosehistorie()
    if df_hist.empty:
        st.info("Noch keine Daten vorhanden.")
        return

    statistik = berechne_trefferstatistik()
    col1, col2 = st.columns(2)
    col1.metric("Day Trefferquote", f"{statistik['Day Trefferquote %']}%", f"{statistik['Day Anzahl']} Prognosen")
    col2.metric("Swing Trefferquote", f"{statistik['Swing Trefferquote %']}%", f"{statistik['Swing Anzahl']} Prognosen")

    _zeige_zeitprotokoll(df_hist)

    spalten = [
        "Prognose-Datum", "Prognose-Zeit", "Ticker", 
        "Day Kauf", "Day Treffer", "Day Erreicht am",
        "Swing Kauf", "Swing Treffer", "Swing Erreicht am",
        "Day Netto €", "Swing Netto €"
    ]
    spalten = [sp for sp in spalten if sp in df_hist.columns]
    st.dataframe(baue_styler(df_hist[spalten]), use_container_width=True, hide_index=True)


def _zeige_zeitprotokoll(df_auswertung):
    st.markdown("#### Zeitprotokoll")

    df_prognosen = _lese_csv_sicher(DATEI_PROGNOSEN)
    if df_prognosen.empty:
        st.info("Für das Zeitprotokoll sind noch keine fixierten Prognosen vorhanden.")
        return

    if "Land" not in df_prognosen.columns:
        st.info("Für das Zeitprotokoll fehlt in den historischen Daten die Spalte `Land`.")
        return

    for region in ["Europa", "USA"]:
        df_region = filtere_nach_region(df_prognosen, region)
        tabelle = _baue_zeitprotokoll_tabelle(df_region, region, df_auswertung)
        st.markdown(f"**{region}**")
        if tabelle.empty:
            st.info(f"Für {region} sind noch keine Zeitdaten vorhanden.")
        else:
            st.dataframe(tabelle, use_container_width=True, hide_index=True)


def _baue_zeitprotokoll_tabelle(df_region, region, df_auswertung):
    if df_region.empty:
        return pd.DataFrame()

    benoetigt = ["Prognose-Datum", "Prognose-Zeitstempel"]
    if any(spalte not in df_region.columns for spalte in benoetigt):
        return pd.DataFrame()

    gruppen = df_region.copy()
    gruppen["Prognose-Zeitstempel"] = gruppen["Prognose-Zeitstempel"].fillna("")
    gruppen = gruppen[gruppen["Prognose-Zeitstempel"].astype(str).str.strip() != ""]
    if gruppen.empty:
        return pd.DataFrame()

    zeilen = []
    for (datum, prognose_zeitstempel), gruppe in gruppen.groupby(["Prognose-Datum", "Prognose-Zeitstempel"], sort=False):
        daten_geladen = _erster_wert(gruppe, "Börsendaten geladen") or prognose_zeitstempel
        prognosekontrolle = _hole_prognosekontrolle_zeit(df_auswertung, gruppe, region, str(datum), prognose_zeitstempel)
        fixierung = hole_fixierungs_status(region=region, datum=str(datum), vollstaendig=True) or ""

        zeilen.append({
            "Prognose-Datum": datum,
            "Prognose erstellt": prognose_zeitstempel,
            "Fixierung erstellt": fixierung,
            "Börsendaten heruntergeladen": daten_geladen,
            "Prognosekontrolle durchgeführt": prognosekontrolle or "",
            "Werte": int(gruppe["Ticker"].nunique()) if "Ticker" in gruppe.columns else int(len(gruppe)),
        })

    ergebnis = pd.DataFrame(zeilen)
    if ergebnis.empty:
        return ergebnis
    return ergebnis.sort_values("Prognose erstellt", ascending=False).reset_index(drop=True)


def _erster_wert(df, spalte):
    if spalte not in df.columns:
        return ""
    werte = df[spalte].dropna().astype(str).str.strip()
    werte = werte[werte != ""]
    return werte.iloc[0] if not werte.empty else ""


def _hole_prognosekontrolle_zeit(df_auswertung, gruppe, region, prognose_datum, prognose_zeitstempel):
    if str(prognose_datum) > _jetzt_berlin().strftime("%Y-%m-%d"):
        return ""
    if str(prognose_datum) == _jetzt_berlin().strftime("%Y-%m-%d") and not _region_nach_boersenschluss(region):
        return ""
    if df_auswertung.empty or "Prognosekontrolle durchgeführt" not in df_auswertung.columns:
        return ""
    if "Prognose-Zeitstempel" not in df_auswertung.columns:
        return ""

    auswahl = df_auswertung[
        df_auswertung["Prognose-Zeitstempel"].astype(str) == str(prognose_zeitstempel)
    ].copy()

    if "Ticker" in gruppe.columns and "Ticker" in auswahl.columns:
        ticker = gruppe["Ticker"].dropna().astype(str).unique().tolist()
        auswahl = auswahl[auswahl["Ticker"].astype(str).isin(ticker)]

    return _erster_wert(auswahl, "Prognosekontrolle durchgeführt")


def _region_nach_boersenschluss(region):
    from modules.prognose_auswertung import KONTROLL_DELAY_MINUTEN
    if region == "Europa":
        jetzt = _jetzt_berlin()
        return jetzt.hour * 60 + jetzt.minute >= 17 * 60 + 30 + KONTROLL_DELAY_MINUTEN
    if region == "USA":
        from modules.prognose_speicher import _jetzt_new_york
        jetzt = _jetzt_new_york()
        return jetzt.hour * 60 + jetzt.minute >= 16 * 60 + KONTROLL_DELAY_MINUTEN
    return False

def seite_einstellungen():
    st.subheader("⚙️ Systemeinstellungen")
    st.write("Konfiguriere hier die Analyse-Parameter und die Automatisierung.")
    
    # =========================================================
    # 1. ANALYSE & AUTOMATISIERUNG
    # =========================================================
    with st.container(border=True):
        st.markdown("#### 🔄 Basis-Analyse & Automatik")
        
        # Erste Reihe: Analyse & Hauptschalter
        c1, c2, c3 = st.columns([1.5, 1, 1])
        with c1:
            st.session_state["analyse_zeitraum"] = st.selectbox(
                "Analyse-Zeitraum", ["6mo", "1y", "2y", "5y"],
                index=["6mo", "1y", "2y", "5y"].index(st.session_state["analyse_zeitraum"]),
                help="Zeitraum für technische Indikatoren (RSI, Trends etc.)"
            )
        with c2:
            st.session_state["analyse_top_n"] = st.number_input("Top-Werte pro Region", 3, 20, int(st.session_state["analyse_top_n"]))
        with c3:
            st.write("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True) # Schiebt Toggle leicht runter
            st.session_state["auto_fix_aktiv"] = st.toggle("Auto-Snapshot aktiv", value=st.session_state.get("auto_fix_aktiv", True))

        # Zweite Reihe: Offsets auf gleicher Höhe
        st.write("---") # Trennlinie innerhalb des Containers
        st.caption("Snapshot-Verzögerung (Minuten nach Börsenstart)")
        off1, off2 = st.columns(2)
        with off1:
            st.session_state["auto_fix_offset_eu"] = st.number_input("Europa Offset (Min) [09:00]", -120, 60, int(st.session_state.get("auto_fix_offset_eu", 20)))
        with off2:
            st.session_state["auto_fix_offset_us"] = st.number_input("USA Offset (Min) [15:30]", -120, 60, int(st.session_state.get("auto_fix_offset_us", 20)))

    # =========================================================
    # 2. FILTER-REGELN
    # =========================================================
    st.markdown("#### 🎯 Handels-Filter (Regelwerk)")
    col_day, col_swing = st.columns(2)
    
    with col_day:
        with st.container(border=True):
            st.markdown("**⚡ Daytrading**")
            st.session_state["day_min_atr_rel"] = st.number_input("Min ATR rel %", 0.0, 10.0, float(st.session_state["day_min_atr_rel"]), step=0.1)
            st.session_state["day_min_crv"] = st.number_input("Min Day-CRV", 0.0, 5.0, float(st.session_state["day_min_crv"]), step=0.1)
            st.session_state["day_min_potenzial"] = st.number_input("Min Potenzial €", 0.0, 500.0, float(st.session_state["day_min_potenzial"]), step=1.0)
            st.session_state["day_haltedauer"] = st.slider("Max Haltedauer (D)", 1, 7, int(st.session_state.get("day_haltedauer", 3)))

    with col_swing:
        with st.container(border=True):
            st.markdown("**📈 Swingtrading**")
            st.session_state["swing_min_crv"] = st.number_input("Min Swing-CRV", 0.0, 5.0, float(st.session_state["swing_min_crv"]), step=0.1)
            st.session_state["swing_min_potenzial"] = st.number_input("Min Potenzial € (S)", 0.0, 2000.0, float(st.session_state["swing_min_potenzial"]), step=10.0)
            st.session_state["swing_min_rsi"], st.session_state["swing_max_rsi"] = st.slider("RSI-Bereich", 0, 100, (int(st.session_state["swing_min_rsi"]), int(st.session_state["swing_max_rsi"])))
            st.session_state["swing_haltedauer"] = st.slider("Max Haltedauer (S)", 2, 30, int(st.session_state.get("swing_haltedauer", 10)))

    # =========================================================
    # 3. STRATEGIE-OPTIMIERUNG & SYSTEM
    # =========================================================
    st.markdown("#### 🛠️ Strategie & Daten-Management")
    c_opt, c_sys = st.columns(2)
    
    with c_opt:
        with st.expander("📊 Strategie-Optimierung (Vorschläge)"):
            vorschlag = schlage_standardwerte_vor()
            if vorschlag:
                st.json(vorschlag)
                if st.button("Diese Werte als Standard setzen"):
                    for k, v in vorschlag.items(): st.session_state[k] = v
                    speichere_standardwerte(hole_filter_settings_aus_session())
                    st.success("Übernommen!")
                    st.rerun()
            else:
                st.info("Noch zu wenig Daten für Optimierung.")

    with c_sys:
        with st.expander("💾 Backup & System"):
            if st.button("Werkseinstellungen laden", use_container_width=True):
                standard = hole_standard_einstellungen()
                for k, v in standard.items(): st.session_state[k] = v
                speichere_standardwerte(hole_filter_settings_aus_session())
                st.rerun()
            
            st.divider()
            backups = liste_backups_auf()
            if backups:
                opt = {b["anzeige_name"]: b["zeitstempel"] for b in backups}
                sel = st.selectbox("Snapshot laden", list(opt.keys()))
                if st.button("Wiederherstellen"):
                    ok, meldung = stelle_backup_wieder_her(opt[sel])
                    if ok:
                        st.success(meldung)
                        st.rerun()
                    else:
                        st.error(meldung)

                if st.button("Alte Backups bereinigen (20 behalten)", use_container_width=True):
                    ergebnis = loesche_alte_backups(max_gruppen=20)
                    if ergebnis["fehler"]:
                        st.error("; ".join(ergebnis["fehler"]))
                    else:
                        st.success(f"{ergebnis['geloescht']} Backup-Tabs/Dateien gelöscht. {ergebnis['behalten']} Gruppen behalten.")
                        st.rerun()

            st.divider()
            st.markdown("**🗑️ Daten bereinigen**")
            col_d1, col_d2 = st.columns(2)
            heute_de = _jetzt_berlin().date()
            von = col_d1.date_input("Von", heute_de - datetime.timedelta(days=30))
            bis = col_d2.date_input("Bis", heute_de)
            if st.button("Ausgewählte Periode löschen", use_container_width=True, type="secondary"):
                ergebnis = loesche_historische_daten(von, bis)
                if ergebnis["geloescht"] > 0:
                    st.success(f"{ergebnis['geloescht']} Einträge gelöscht. Backup erstellt.")
                    st.rerun()
                else:
                    st.info("Keine Einträge im Zeitraum gefunden.")

    # Footer Speichern
    st.divider()
    if st.button("💾 Alle Einstellungen dauerhaft speichern", use_container_width=True):
        settings = {k: v for k, v in st.session_state.items() if k in hole_standard_einstellungen()}
        speichere_standardwerte(settings)
        st.success("Einstellungen erfolgreich in `standardwerte_vorschlag.json` gesichert!")
