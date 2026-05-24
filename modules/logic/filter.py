def filter_daytrading_kandidaten(df, settings):
    if df.empty:
        return df

    return df[
        (df["Day Kauf"] == "JA") &
        (df["ATR relativ %"] >= float(settings["day_min_atr_rel"])) &
        (df["Ø Tagesrange %"] >= float(settings["day_min_range"])) &
        (df["Hit-Rate > 2 %"] >= float(settings["day_min_hitrate2"])) &
        (df["Day CRV"] >= float(settings["day_min_crv"])) &
        (df["Day Potenzial €"] >= float(settings["day_min_potenzial"])) &
        (df["Day Netto €"] >= 1.0)
    ].copy()


def filter_swingtrading_kandidaten(df, settings):
    if df.empty:
        return df

    return df[
        (df["Swing Kauf"] == "JA") &
        (
            (df["Trend Up"] == True) |
            (df["Trend Stabil"] == True)
        ) &
        (df["RSI 14"].between(
            int(settings["swing_min_rsi"]),
            int(settings["swing_max_rsi"])
        )) &
        (df["Swing CRV"] >= float(settings["swing_min_crv"])) &
        (df["Swing Potenzial €"] >= float(settings["swing_min_potenzial"]))
    ].copy()