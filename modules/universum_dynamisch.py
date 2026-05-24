import pandas as pd
from modules.markt_daten import lade_kursdaten


def berechne_universum_dynamisch(ticker_liste, top_n=80, min_anzahl_fallback=20):
    daten = lade_kursdaten(
        ticker_liste=ticker_liste,
        zeitraum="3mo",
        intervall="1d"
    )

    bewertungen = []

    for ticker, df in daten.items():
        if df is None or df.empty or len(df) < 20:
            continue

        try:
            close = pd.to_numeric(df["Close"], errors="coerce")
            high = pd.to_numeric(df["High"], errors="coerce")
            low = pd.to_numeric(df["Low"], errors="coerce")
            volume = pd.to_numeric(df["Volume"], errors="coerce")

            letzter_kurs = close.dropna().iloc[-1]
            if letzter_kurs < 5:
                continue

            range_pct = (((high - low) / close.replace(0, pd.NA)) * 100).rolling(14).mean().iloc[-1]
            avg_volume = volume.rolling(20).mean().iloc[-1]

            if pd.isna(range_pct) or pd.isna(avg_volume):
                continue

            score = (float(range_pct) * 0.6) + ((float(avg_volume) / 1_000_000) * 0.4)

            bewertungen.append({
                "Ticker": ticker,
                "Score": score
            })

        except Exception:
            continue

    if not bewertungen:
        return list(ticker_liste)

    df_scores = pd.DataFrame(bewertungen).sort_values("Score", ascending=False)
    dynamische_ticker = df_scores["Ticker"].dropna().astype(str).tolist()[:top_n]

    if len(dynamische_ticker) < min_anzahl_fallback:
        return list(ticker_liste)

    return dynamische_ticker