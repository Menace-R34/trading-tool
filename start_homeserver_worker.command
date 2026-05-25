#!/bin/bash

cd "$HOME/Documents/trading_tool" || exit 1

source .venv/bin/activate

export TRADING_TOOL_START_WORKER=1

python background_worker.py
