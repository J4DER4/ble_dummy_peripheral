"""Example of how to create a Peripheral device/GATT Server"""
# Standard modules
import logging
import struct

# Bluezero modules
from bluezero import async_tools
from bluezero import adapter
from bluezero import peripheral


custom_service = '398629c8-4757-4e72-9b0d-8ebdd6ac82a2'
custom_charasteristic = '094bd4ad-3605-4912-b9d3-a6b91c573137'
# Heartrate measurement and energy expended is persistent between function
# reads
heartrate = 60


def read_heartrate():
    """
    Generates new heartrate and energy expended measurements
    Increments heartrate and energy_expended variables and serializes
    them for BLE transport.
    :return: bytes object for Heartrate Measurement Characteristic
    """
    global heartrate
    # Setup flags for what's supported by this example
    # We are sending UINT8 formats, so don't indicate
    # HEART_RATE_VALUE_FORMAT_UINT16

    # Increment heartrate by one each measurement cycle
    heartrate = heartrate + 1
    if heartrate > 180:
        heartrate = 60

    # Compose a double value for the payload (example: combine heartrate and energy_expended)
    double_value = float(heartrate)
    print(
        f"Sending double payload: {double_value} (as 8 bytes)")
    return struct.pack('<d', double_value)


def update_value(characteristic):
    """
    Example of callback to send notifications

    :param characteristic:
    :return: boolean to indicate if timer should continue
    """
    global heartrate
    # read/calculate new value
    print("updating value")
    heartrate += 1
    if heartrate > 180:
        heartrate = 60
    # Causes characteristic to be updated and send notification
    characteristic.set_value(struct.pack('<d', float(heartrate)))
    # If still notifying, schedule the next update
    if characteristic.is_notifying:
        async_tools.add_timer_seconds(1, update_value, characteristic)
    # Return True to continue notifying. Return a False will stop notifications
    return characteristic.is_notifying


def notify_callback(notifying, characteristic):
    """
    Noitificaton callback example. In this case used to start a timer event
    which calls the update callback every 2 seconds

    :param notifying: boolean for start or stop of notifications
    :param characteristic: The python object for this characteristic
    """
    print("hello from notify cb")
    print("notifications set")

    if notifying:
        async_tools.add_timer_seconds(1, update_value, characteristic)
    return True


def main(adapter_address):
    """
    Creates advertises and starts the peripheral

    :param adapter_address: the MAC address of the hardware adapter
    """
    logger = logging.getLogger('localGATT')
    logger.setLevel(logging.DEBUG)

    # Create peripheral
    hr_monitor = peripheral.Peripheral(adapter_address,
                                       local_name='superpaahdin3000',
                                       appearance=0x0905)
    # Add service
    hr_monitor.add_service(srv_id=1, uuid=custom_service, primary=True)

    # Add characteristics
    hr_monitor.add_characteristic(srv_id=1, chr_id=1, uuid=custom_charasteristic,
                                  value=[], notifying=True,
                                  # May not exactly match standard, but
                                  # including read for tutorial
                                  flags=['read', 'notify'],
                                  read_callback=read_heartrate,
                                  write_callback=None,
                                  notify_callback=notify_callback
                                  )

    # Publish peripheral
    hr_monitor.publish()

    # Start Bluezero async event loop
    event_loop = async_tools.EventLoop()
    try:
        event_loop.run()
    except KeyboardInterrupt:
        hr_monitor.stop()


if __name__ == '__main__':
    # Get the default adapter address and pass it to main
    main(list(adapter.Adapter.available())[0].address)