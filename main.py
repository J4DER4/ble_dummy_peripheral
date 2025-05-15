from bluezero import adapter, advertisement

# Get the default Bluetooth adapter
dongle = adapter.Adapter()

# Create an advertisement object
adv = advertisement.Advertisement(1, 'peripheral')

# Set your custom 128-bit UUID (as a string, no dashes)
my_uuid = 'db0a2604477846b385635b54c410b76f'
adv.service_UUIDs = [my_uuid]

# Add Service Data (UUID as key, payload as value)
payload = bytes([0x01, 0x02, 0x03, 0x04])  # Example payload
adv.service_data = {my_uuid: payload}

# Optionally, set other fields
adv.appearance = 0  # Generic
adv.local_name = 'MyBLEDevice'
adv.include_tx_power = True

# Start advertising
adv.start()

print('Advertising with custom UUID and payload. Press Ctrl+C to stop.')
try:
    while True:
        pass
except KeyboardInterrupt:
    adv.stop()