#!/bin/bash

# Projektordner
cd "$HOME/Documents/trading_tool" || exit 1

# Virtuelle Umgebung aktivieren
source .venv/bin/activate

# Streamlit starten
streamlit run app.py