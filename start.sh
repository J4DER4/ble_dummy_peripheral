#!/bin/bash
# Script to start the BLE dummy peripheral

# Default interval is 5 seconds if not specified
INTERVAL=${1:-5}

cd ~/Desktop || exit 1
cd ble_dummy_peripheral || exit 1
source bin/activate
python3 main.py $INTERVAL
