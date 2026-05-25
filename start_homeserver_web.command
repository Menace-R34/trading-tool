#!/bin/bash

cd "$HOME/Documents/trading_tool" || exit 1

source .venv/bin/activate

export TRADING_TOOL_STORAGE="${TRADING_TOOL_STORAGE:-local}"
export TRADING_TOOL_START_WORKER=0

streamlit run app.py --server.address 0.0.0.0 --server.port 8501
