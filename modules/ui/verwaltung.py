import streamlit as st
import datetime
from modules.prognose_speicher import (
    lade_prognosehistorie,
    speichere_standardwerte,
    loesche_historische_daten,
    _zeitstempel_str,
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

def seite_prognosekontrolle():
    st.subheader("Prognosekontrolle")
    st.write("Historische Auswertung der Treffersicherheit.")
    st.caption(f"Letzte Aktualisierung: {_zeitstempel_str()}")

    df_hist = lade_prognosehistorie()
    if df_hist.empty:
        st.info("Noch keine Daten vorhanden.")
        return

    statistik = berechne_trefferstatistik()
    col1, col2 = st.columns(2)
    col1.metric("Day Trefferquote", f"{statistik['Day Trefferquote %']}%", f"{statistik['Day Anzahl']} Prognosen")
    col2.metric("Swing Trefferquote", f"{statistik['Swing Trefferquote %']}%", f"{statistik['Swing Anzahl']} Prognosen")

    spalten = [
        "Prognose-Datum", "Prognose-Zeit", "Ticker", 
        "Day Kauf", "Day Treffer", "Day Erreicht am",
        "Swing Kauf", "Swing Treffer", "Swing Erreicht am",
        "Day Netto €", "Swing Netto €"
    ]
    spalten = [sp for sp in spalten if sp in df_hist.columns]
    st.dataframe(baue_styler(df_hist[spalten]), use_container_width=True, hide_index=True)

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
            von = col_d1.date_input("Von", datetime.date.today() - datetime.timedelta(days=30))
            bis = col_d2.date_input("Bis", datetime.date.today())
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
