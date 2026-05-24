import pandas as pd
import streamlit as st
from modules.region_logik import filtere_nach_region
from modules.universum import hole_tickerliste_aus_universum
from modules.auswertung_builder import baue_auswertung_fuer_ticker
from modules.logic.filter import filter_daytrading_kandidaten, filter_swingtrading_kandidaten
from modules.ui_styling import baue_styler
from modules.ui_hilfe import zeige_marktlage_box
from modules.prognose_auswertung import (
    berechne_trefferstatistik,
    berechne_ticker_genauigkeit
)
from modules.prognose_speicher import (
    lade_heutigen_snapshot,
    hole_fixierungs_status,
    _zeitstempel_str
)
from modules.markt_lage import berechne_marktlage
from modules.ui.common import _prepare_df

def seite_start():
    st.subheader("Hauptübersicht")
    st.write("Zentrale Übersicht zu Markt, Signalen und Prognosegüte.")
    st.caption(f"Status am: {_zeitstempel_str()}")

    # 1. Datenbasis ermitteln (Snapshots vs. Live)
    df_eu_fixed = lade_heutigen_snapshot(region="Europa")
    df_us_fixed = lade_heutigen_snapshot(region="USA")
    
    ticker_liste = hole_tickerliste_aus_universum()
    markt = berechne_marktlage()
    statistik = berechne_trefferstatistik()

    # 2. Markt-Status Anzeigen
    st.markdown("### Markt-Status & Fixierung")
    status_col_1, status_col_2 = st.columns(2)
    
    with status_col_1:
        fix_zeit_eu = hole_fixierungs_status("Europa")
        if not df_eu_fixed.empty:
            msg = f"🇪🇺 **Europa:** Prognosen fixiert"
            if fix_zeit_eu: msg += f" ({fix_zeit_eu})"
            st.success(msg)
            df_eu = df_eu_fixed
        else:
            st.warning(f"🇪🇺 **Europa:** Zeige Live-Daten (noch nicht fixiert)")
            with st.spinner("Lade EU Live-Daten..."):
                df_all_live = baue_auswertung_fuer_ticker(tuple(ticker_liste), st.session_state["analyse_zeitraum"])
                df_eu = filtere_nach_region(df_all_live, "Europa")

    with status_col_2:
        fix_zeit_us = hole_fixierungs_status("USA")
        if not df_us_fixed.empty:
            msg = f"🇺🇸 **USA:** Prognosen fixiert"
            if fix_zeit_us: msg += f" ({fix_zeit_us})"
            st.success(msg)
            df_us = df_us_fixed
        else:
            st.warning(f"🇺🇸 **USA:** Zeige Live-Daten (noch nicht fixiert)")
            with st.spinner("Lade US Live-Daten..."):
                if 'df_all_live' not in locals():
                    df_all_live = baue_auswertung_fuer_ticker(tuple(ticker_liste), st.session_state["analyse_zeitraum"])
                df_us = filtere_nach_region(df_all_live, "USA")

    zeige_marktlage_box(markt)

    # 3. KPIs kombiniert
    df_total = pd.concat([df_eu, df_us]).drop_duplicates(subset=["Ticker"])
    df_total = _prepare_df(df_total)
    
    df_day = filter_daytrading_kandidaten(df_total, st.session_state)
    df_swing = filter_swingtrading_kandidaten(df_total, st.session_state)

    kpi_1, kpi_2, kpi_3, kpi_4 = st.columns(4)
    kpi_1.metric("Analysierte Werte", len(df_total))
    kpi_2.metric("Signale Heute (Gesamt)", len(df_day) + len(df_swing))
    kpi_3.metric("Ø Trefferquote (Day)", f"{statistik['Day Trefferquote %']:.1f} %")
    kpi_4.metric("Ø Trefferquote (Swing)", f"{statistik['Swing Trefferquote %']:.1f} %")

    # 4. Regionale Top-Listen (Untereinander)
    st.divider()
    st.markdown("### 🇪🇺 Top Europa")
    df_eu = _prepare_df(df_eu)
    _zeige_top_liste(df_eu, markt, region="Europa")
    
    st.divider()
    st.markdown("### 🇺🇸 Top USA")
    df_us = _prepare_df(df_us)
    _zeige_top_liste(df_us, markt, region="USA")

    # 5. Hinweise am Ende der Seite
    st.divider()
    st.markdown("### Hinweise")
    hinweise = []

    if len(df_day) == 0:
        hinweise.append("Aktuell keine belastbaren Daytrading-Setups.")
    if len(df_swing) == 0:
        hinweise.append("Aktuell keine belastbaren Swingtrading-Setups.")
    
    if markt["Marktlage"] == "Risk-Off":
        hinweise.append("Gesamtmarkt defensiv: Long-Setups strenger bewerten.")
    elif markt["Marktlage"] == "Risk-On":
        hinweise.append("Gesamtmarkt konstruktiv: Long-Setups haben Rückenwind.")
    
    if statistik["Day Anzahl"] >= 10 and statistik["Day Trefferquote %"] < 45:
        hinweise.append("Die historische Day-Trefferquote ist ausbaufähig.")
    
    if not hinweise:
        st.success("Aktuell liegen keine besonderen Warnhinweise vor.")
    else:
        for h in hinweise:
            st.info(f"💡 {h}")

def _zeige_top_liste(df_region, markt, region):
    if df_region.empty:
        st.info(f"Keine Daten für {region} vorhanden.")
        return

    df_day = filter_daytrading_kandidaten(df_region, st.session_state)
    df_swing = filter_swingtrading_kandidaten(df_region, st.session_state)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"#### ⚡ Daytrading {region}")
        if df_day.empty:
            st.info("Keine Daytrading-Signale.")
        else:
            day_cols = ["Ticker", "Hist. Prognosegenauigkeit %", "Anzahl Hist. Prognosen", "Day Kauf", "Day Score", "Day CRV", "Day Netto €", "Hist. Idealer Hold (Day)"]
            day_cols = [c for c in day_cols if c in df_day.columns]
            st.dataframe(baue_styler(df_day[day_cols].sort_values("Day Score", ascending=False).head(5)), use_container_width=True, hide_index=True)
            
    with col2:
        st.markdown(f"#### 📈 Swingtrading {region}")
        if df_swing.empty:
            st.info("Keine Swingtrading-Signale.")
        else:
            swing_cols = ["Ticker", "Hist. Prognosegenauigkeit %", "Anzahl Hist. Prognosen", "Swing Kauf", "Swing Score", "Swing CRV", "Swing Netto €", "Saison-Score", "Hist. Idealer Hold (Swing)"]
            swing_cols = [c for c in swing_cols if c in df_swing.columns]
            st.dataframe(baue_styler(df_swing[swing_cols].sort_values("Swing Score", ascending=False).head(5)), use_container_width=True, hide_index=True)
