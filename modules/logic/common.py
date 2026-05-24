def _wert(daten, schluessel, standard=0.0):
    return daten.get(schluessel, standard)


def _begrenzt(wert, minimum, maximum):
    return max(minimum, min(maximum, wert))


def _signal_farbe(kaufsignal):
    return "#c6efce" if kaufsignal == "JA" else "#ffc7ce"


def _signal_textfarbe(kaufsignal):
    return "#006100" if kaufsignal == "JA" else "#9c0006"


def _hole_marktlage(markt):
    if not isinstance(markt, dict):
        return "Neutral"
    return str(markt.get("Marktlage", "Neutral")).strip()
