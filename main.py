from bluezero import tools
from bluezero import adapter
from bluezero import advertisement
import uuid

SERVICE_UUID = 'B3C60426-15C1-45C8-BFC0-A129094D994D'

def main():
    # Get the first available Bluetooth adapter
    bt_adapters = list(adapter.Adapter.available())
    if not bt_adapters:
        print("No Bluetooth adapter found")
        return

    dongle = adapter.Adapter(bt_adapters[0])

    # Create an advertisement
    adv = advertisement.Advertisement(dongle.path, 0, 'peripheral')
    adv.service_uuids = [SERVICE_UUID]
    adv.local_name = "DummyDevice"
    adv.include_tx_power = True

    # Register the advertisement
    dongle.advertisement_register(adv)

    print(f"Starting advertisement with service UUID: {SERVICE_UUID}")
    print(f"Using adapter: {dongle.address}")
    print("Press Ctrl+C to stop")

    try:
        tools.start_mainloop()
    except KeyboardInterrupt:
        print("\nStopping advertisement")
        dongle.advertisement_unregister(adv)

if __name__ == '__main__':
    main()
