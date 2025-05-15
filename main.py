from bluezero import tools
from bluezero import adapter
from bluezero import advertisement
import uuid

# Define the service UUID
SERVICE_UUID = uuid.UUID('{B3C60426-15C1-45C8-BFC0-A129094D994D}')

def main():
    # Get the first available Bluetooth adapter
    bt_adapters = adapter.Adapter.available()
    if not bt_adapters:
        print("No Bluetooth adapter found")
        return
    
    dongle = bt_adapters[0]
    
    # Create an advertisement manager using the adapter's path
    advert_mgr = advertisement.AdvertisingManager(dongle.path)
    
    # Create an advertisement
    adv = advertisement.Advertisement(dongle.path, 0, 'peripheral')
    
    # Set advertisement properties
    adv.service_uuids = [str(SERVICE_UUID)]
    adv.local_name = "DummyDevice"
    adv.include_tx_power = True
    
    # Register the advertisement
    advert_mgr.register_advertisement(adv, {})
    
    # Start advertising
    print(f"Starting advertisement with service UUID: {SERVICE_UUID}")
    print(f"Using adapter: {dongle.address}")
    print("Press Ctrl+C to stop")
    
    try:
        tools.start_mainloop()
    except KeyboardInterrupt:
        print("\nStopping advertisement")
        advert_mgr.unregister_advertisement(adv)

if __name__ == '__main__':
    main()