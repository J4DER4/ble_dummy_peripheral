#!/bin/bash
# Script to start the BLE dummy peripheral

# Default interval is 0.1 seconds if not specified (super short)
INTERVAL=${1:-0.1}

cd ~/Desktop || exit 1
cd ble_dummy_peripheral || exit 1
source bin/activate
python3 main.py $INTERVAL
