from bluezero import adapter, advertisement
import time
import sys

def main():
    print("Starting BLE advertisement setup...")
    
    try:
        # Get the default Bluetooth adapter
        print("\n1. Initializing Bluetooth adapter...")
        dongle = adapter.Adapter()
        
        # Adapter check
        if not dongle:
            print("ERROR: No Bluetooth adapter found!")
            return
        
        print(f"Adapter found: {dongle.address} (Powered: {dongle.powered})")
        
        # Ensure adapter is powered on
        if not dongle.powered:
            print("Adapter is off - powering on...")
            dongle.powered = True
            time.sleep(2)  # Give time to power on
            if dongle.powered:
                print("Adapter successfully powered on")
            else:
                print("ERROR: Failed to power on adapter!")
                return

        # Create advertisement
        print("\n2. Creating advertisement...")
        adv = advertisement.Advertisement(1, 'peripheral')
        
        # Set custom UUID
        my_uuid = 'db0a2604-4778-46b3-8563-5b54c410b76f'
        print(f"Setting service UUID: {my_uuid}")
        adv.service_UUIDs = [my_uuid]
        
        # Set service data
        payload = bytes([0x01, 0x02, 0x03, 0x04, 0x05])
        print(f"Setting service data payload: {payload.hex(':')}")
        adv.service_data = {my_uuid: payload}
        
        # Set other advertisement properties
        print("\n3. Setting advertisement properties...")
        adv.appearance = 0  # Generic
        adv.local_name = 'MyBLEDevice'
        adv.include_tx_power = True
        print(f"Configured - Name: {adv.local_name}, Appearance: {adv.appearance}, TX Power: {adv.include_tx_power}")

        # Start advertising
        print("\n4. Starting advertisement...")
        adv.start()
        print("Advertisement started successfully!")
        print(f"Device should be visible as '{adv.local_name}' with UUID {my_uuid}")

        # Main loop
        print("\n5. Running (Press Ctrl+C to stop)...")
        try:
            while True:
                time.sleep(1)
                # You could add periodic status checks here
        except KeyboardInterrupt:
            print("\nReceived stop signal...")
        finally:
            print("Stopping advertisement...")
            adv.stop()
            print("Advertisement stopped. Cleaning up...")
            # Additional cleanup if needed
            print("Exit")

    except Exception as e:
        print(f"\nERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()