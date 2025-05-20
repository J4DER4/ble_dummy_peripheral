#!/bin/bash
# Script to start the BLE dummy peripheral

cd ~/Desktop || exit 1
cd ble_dummy_peripheral || exit 1
source bin/activate
python3 main.py
