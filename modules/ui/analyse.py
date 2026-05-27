import streamlit as st
from modules.region_logik import filtere_nach_region
from modules.universum import hole_tickerliste_aus_universum
from modules.auswertung_builder import baue_auswertung_fuer_ticker
from modules.logic.filter import filter_daytrading_kandidaten, filter_swingtrading_kandidaten
from modules.ui_styling import baue_styler
from modules.ui_hilfe import zeige_marktlage_box
from modules.prognose_speicher import speichere_prognosen, lade_heutigen_snapshot, protokolliere_fixierung
from modules.prognose_speicher import _zeitstempel_str
from modules.markt_lage import berechne_marktlage
from modules.ui_einstellungen import hole_filter_settings_aus_session
from modules.ui.common import _prepare_df

def seite_marktueberblick():
    st.subheader("Marktüberblick")
    st.write("Gesamtübersicht aller ausgewerteten Werte.")
    st.caption(f"Letzte Aktualisierung: {_zeitstempel_str()} deutsche Zeit")

    ticker_liste = hole_tickerliste_aus_universum()
    if not ticker_liste:
        st.warning("Im Universum sind keine analysierbaren Ticker vorhanden.")
        return

    nur_kandidaten = st.toggle(
        "Nur Kandidaten anzeigen",
        value=st.session_state["marktueberblick_nur_kandidaten"]
    )

    with st.spinner("Lade und berechne Daten..."):
        df = baue_auswertung_fuer_ticker(
            tuple(ticker_liste),
            st.session_state["analyse_zeitraum"]
        )

    if df.empty:
        st.warning("Es konnten keine Daten geladen werden.")
        return

    df_day_kandidaten = filter_daytrading_kandidaten(df, st.session_state)
    df_swing_kandidaten = filter_swingtrading_kandidaten(df, st.session_state)

    if nur_kandidaten:
        ticker_kandidaten = (
            set(df_day_kandidaten["Ticker"].tolist()) |
            set(df_swing_kandidaten["Ticker"].tolist())
        )
        df_anzeige = df[df["Ticker"].isin(ticker_kandidaten)].copy()
    else:
        df_anzeige = df.copy()

    df_anzeige = _prepare_df(df_anzeige)

    st.write(f"Gesamtwerte: {len(df)} | Day Kandidaten: {len(df_day_kandidaten)} | Swing Kandidaten: {len(df_swing_kandidaten)}")

    df_eu = filtere_nach_region(df_anzeige, "Europa")
    df_us = filtere_nach_region(df_anzeige, "USA")

    st.markdown("### 🇪🇺 Europa Markt")
    if df_eu.empty:
        st.info("Keine Werte für Europa gefunden.")
    else:
        st.dataframe(baue_styler(df_eu), use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### 🇺🇸 USA Markt")
    if df_us.empty:
        st.info("Keine Werte für USA gefunden.")
    else:
        st.dataframe(baue_styler(df_us), use_container_width=True, hide_index=True)

def seite_signale():
    st.subheader("Signale")
    st.write("Konsolidierte Signalübersicht nach Handelsregionen.")
    st.caption(f"Letzte Aktualisierung: {_zeitstempel_str()} deutsche Zeit")

    nur_kandidaten = st.toggle(
        "Nur echte Kandidaten verwenden",
        value=st.session_state["signale_nur_kandidaten"],
        key="signale_nur_kandidaten_toggle"
    )

    ticker_liste = hole_tickerliste_aus_universum()
    if not ticker_liste:
        st.warning("Im Universum sind keine analysierbaren Ticker vorhanden.")
        return

    with st.spinner("Berechne Marktdaten & Signale..."):
        df = baue_auswertung_fuer_ticker(tuple(ticker_liste), st.session_state["analyse_zeitraum"])
        markt = berechne_marktlage()

    if df.empty:
        st.warning("Es konnten keine Signaldaten geladen werden.")
        return

    zeige_marktlage_box(markt)
    df = _prepare_df(df)

    df_eu = filtere_nach_region(df, "Europa")
    df_us = filtere_nach_region(df, "USA")

    if nur_kandidaten:
        df_eu = df_eu[
            df_eu["Day Kauf"].astype(str).str.upper().eq("JA") |
            df_eu["Swing Kauf"].astype(str).str.upper().eq("JA")
        ]
        df_us = df_us[
            df_us["Day Kauf"].astype(str).str.upper().eq("JA") |
            df_us["Swing Kauf"].astype(str).str.upper().eq("JA")
        ]

    st.markdown(f"### 🇪🇺 Europa Signale ({len(df_eu)})")
    _zeige_signal_tabelle_kompakt(df_eu, "Europa")

    st.divider()
    st.markdown(f"### 🇺🇸 USA Signale ({len(df_us)})")
    _zeige_signal_tabelle_kompakt(df_us, "USA")

def _zeige_signal_tabelle_kompakt(df, region):
    if df is None or df.empty:
        st.info(f"ℹ️ Keine Signale für {region} (Filter: 'Nur echte Kandidaten' ist {st.session_state['signale_nur_kandidaten_toggle']})")
        return

    spalten = [
        "Ticker", "Land", "Hist. Prognosegenauigkeit %", "Anzahl Hist. Prognosen", "Handelsfenster",
        "Day Kauf", "Day Score", "Day Signalstärke", "Day CRV", "Day Netto €",
        "Swing Kauf", "Swing Score", "Swing Signalstärke", "Swing CRV", "Swing Netto €",
        "Saison-Score", "News-Score"
    ]
    vorhandene_spalten = [s for s in spalten if s in df.columns]
    sort_spalte = "Day Score" if "Day Score" in df.columns else "Ticker"
    df_plot = df[vorhandene_spalten].copy()
    if sort_spalte != "Ticker":
        df_plot["_sort_key"] = pd.to_numeric(
            df_plot[sort_spalte].astype(str).str.replace(",", ".", regex=False),
            errors="coerce",
        ).fillna(0.0)
        df_plot = df_plot.sort_values("_sort_key", ascending=False).drop(columns=["_sort_key"])
    else:
        df_plot = df_plot.sort_values(sort_spalte, ascending=False)

    st.dataframe(baue_styler(df_plot), use_container_width=True, hide_index=True)

def seite_europa_aktien():
    st.subheader("🇪🇺 Europa Aktien")
    st.write("Analyse und Prognosen für den europäischen Markt.")
    _darstellung_regionen_seite("Europa")

def seite_usa_aktien():
    st.subheader("🇺🇸 USA Aktien")
    st.write("Analyse und Prognosen für den US-Markt.")
    _darstellung_regionen_seite("USA")

def _darstellung_regionen_seite(region):
    df_snapshot = lade_heutigen_snapshot(region=region)
    if not df_snapshot.empty:
        st.success(f"📌 Es werden fixierte Prognosen für heute ({_zeitstempel_str().split(' ')[0]}) angezeigt.")
        df_snapshot = _prepare_df(df_snapshot)
        _zeige_signale_tabelle(df_snapshot)
    else:
        st.info(f"Es wurden noch keine Prognosen für {region} fixiert. Zeige Live-Daten.")
        ticker_liste = hole_tickerliste_aus_universum()
        with st.spinner(f"Lade Live-Daten für {region}..."):
            df_live = baue_auswertung_fuer_ticker(tuple(ticker_liste), st.session_state["analyse_zeitraum"])
            df_region = filtere_nach_region(df_live, region)
            
        if df_region.empty:
            st.warning(f"Keine Aktien für Region {region} gefunden.")
        else:
            if st.button(f"Diese Signale für {region} jetzt fixieren"):
                settings = hole_filter_settings_aus_session()
                settings["daten_geladen_zeitstempel"] = _zeitstempel_str()
                speichere_prognosen(df_region, settings)
                protokolliere_fixierung(region)
                st.success("Prognosen erfolgreich fixiert!")
                st.rerun()
            
            df_region = _prepare_df(df_region)
            _zeige_signale_tabelle(df_region)

def _zeige_signale_tabelle(df):
    st.markdown("### ⚡ Daytrading")
    df_day = filter_daytrading_kandidaten(df, st.session_state)
    if df_day.empty:
        st.info("Keine Daytrading-Signale gefunden.")
    else:
        st.dataframe(baue_styler(df_day), use_container_width=True)
        
    st.divider()
    st.markdown("### 📈 Swingtrading")
    df_swing = filter_swingtrading_kandidaten(df, st.session_state)
    if df_swing.empty:
        st.info("Keine Swingtrading-Signale gefunden.")
    else:
        st.dataframe(baue_styler(df_swing), use_container_width=True)
