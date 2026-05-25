import pandas as pd


def _zahl(df, spalte):
    if spalte not in df.columns:
        return pd.Series(0.0, index=df.index)
    return pd.to_numeric(
        df[spalte].astype(str).str.replace(",", ".", regex=False),
        errors="coerce",
    ).fillna(0.0)


def _bool(df, spalte):
    if spalte not in df.columns:
        return pd.Series(False, index=df.index)

    def konvertiere(wert):
        if pd.isna(wert):
            return False
        if isinstance(wert, bool):
            return wert
        text = str(wert).strip().lower()
        return text in {"true", "wahr", "ja", "yes", "y", "1", "1.0", "x"}

    return df[spalte].apply(konvertiere)


def filter_daytrading_kandidaten(df, settings):
    if df.empty:
        return df

    return df[
        (df["Day Kauf"] == "JA") &
        (_zahl(df, "ATR relativ %") >= float(settings["day_min_atr_rel"])) &
        (_zahl(df, "Ø Tagesrange %") >= float(settings["day_min_range"])) &
        (_zahl(df, "Hit-Rate > 2 %") >= float(settings["day_min_hitrate2"])) &
        (_zahl(df, "Day CRV") >= float(settings["day_min_crv"])) &
        (_zahl(df, "Day Potenzial €") >= float(settings["day_min_potenzial"])) &
        (_zahl(df, "Day Netto €") >= 1.0)
    ].copy()


def filter_swingtrading_kandidaten(df, settings):
    if df.empty:
        return df

    return df[
        (df["Swing Kauf"] == "JA") &
        (
            (_bool(df, "Trend Up")) |
            (_bool(df, "Trend Stabil"))
        ) &
        (_zahl(df, "RSI 14").between(
            int(settings["swing_min_rsi"]),
            int(settings["swing_max_rsi"])
        )) &
        (_zahl(df, "Swing CRV") >= float(settings["swing_min_crv"])) &
        (_zahl(df, "Swing Potenzial €") >= float(settings["swing_min_potenzial"]))
    ].copy()
