# =========================================================
# 01_KONSTANTEN
# =========================================================
EU_LAENDER = ["DE", "FR", "NL", "CH", "IT", "UK", "AT", "BE", "ES", "EU", "IE", "LU", "SE", "NO", "DK", "FI"]
US_LAENDER = ["US", "CA"]

# =========================================================
# 02_HILFSFUNKTIONEN
# =========================================================
def bestimme_region(land):
    """
    Ordnet ein Land einer Region (Europa oder USA) zu.
    """
    if not land:
        return "Unbekannt"
    
    land_up = str(land).strip().upper()
    
    if land_up in EU_LAENDER:
        return "Europa"
    if land_up in US_LAENDER:
        return "USA"
    
    return "Andere"

def filtere_nach_region(df, region):
    """
    Filtert einen DataFrame basierend auf der Region.
    Erfordert eine Spalte 'Land'.
    """
    if df is None or df.empty:
        return df
    
    if "Land" not in df.columns:
        return df
        
    df = df.copy()
    df["Region"] = df["Land"].apply(bestimme_region)
    
    if region == "Europa":
        return df[df["Region"] == "Europa"]
    elif region == "USA":
        return df[df["Region"] == "USA"]
    
    return df
