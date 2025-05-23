"""Example of how to create a Peripheral device/GATT Server"""
# Standard modules
from enum import IntEnum
import logging
import struct

# Bluezero modules
from bluezero import async_tools
from bluezero import adapter
from bluezero import peripheral

# Documentation can be found on Bluetooth.com
# https://www.bluetooth.com/specifications/specs/heart-rate-service-1-0/

# There are also published xml specifications for possible values
# For the Service:
# https://github.com/oesmith/gatt-xml/blob/master/org.bluetooth.service.heart_rate.xml

# For the Characteristics:
# Heart Rate Measurement
# https://github.com/oesmith/gatt-xml/blob/master/org.bluetooth.characteristic.heart_rate_measurement.xml
# Body Sensor Location
# https://github.com/oesmith/gatt-xml/blob/master/org.bluetooth.characteristic.body_sensor_location.xml
# Heart Rate Control Point
# https://github.com/oesmith/gatt-xml/blob/master/org.bluetooth.characteristic.heart_rate_control_point.xml


HRM_SRV = 'B3C60426-15C1-45C8-BFC0-A129094D994D'
HR_MSRMT_UUID = '00002a37-0000-1000-8000-00805f9b34fb'
BODY_SNSR_LOC_UUID = '00002a38-0000-1000-8000-00805f9b34fb'
HR_CTRL_PT_UUID = '00002a39-0000-1000-8000-00805f9b34fb'

custom_service = '398629c8-4757-4e72-9b0d-8ebdd6ac82a2'
custom_charasteristic = '094bd4ad-3605-4912-b9d3-a6b91c573137'
class HeartRateMeasurementFlags(IntEnum):
    HEART_RATE_VALUE_FORMAT_UINT16 = 0b00000001
    SENSOR_CONTACT_DETECTED = 0b00000010
    SENSOR_CONTACT_SUPPORTED = 0b00000100
    ENERGY_EXPENDED_PRESENT = 0b00001000
    RR_INTERVALS_PRESENT = 0b00010000


class BodySensorLocation(IntEnum):
    OTHER = 0
    CHEST = 1
    WRIST = 2
    FINGER = 3
    HAND = 4
    EAR_LOBE = 5
    FOOT = 6


class HeartRateControlPoint(IntEnum):
    RESET_ENERGY_EXPENDED = 1


# Heartrate measurement and energy expended is persistent between function
# reads
heartrate = 60
energy_expended = 0


def read_heartrate():
    """
    Generates new heartrate and energy expended measurements
    Increments heartrate and energy_expended variables and serializes
    them for BLE transport.
    :return: bytes object for Heartrate Measurement Characteristic
    """
    global heartrate, energy_expended
    # Setup flags for what's supported by this example
    # We are sending UINT8 formats, so don't indicate
    # HEART_RATE_VALUE_FORMAT_UINT16
    flags = HeartRateMeasurementFlags.SENSOR_CONTACT_DETECTED | \
        HeartRateMeasurementFlags.SENSOR_CONTACT_SUPPORTED | \
        HeartRateMeasurementFlags.ENERGY_EXPENDED_PRESENT

    # Increment heartrate by one each measurement cycle
    heartrate = heartrate + 1
    if heartrate > 180:
        heartrate = 60

    # Increment energy expended each measurement cycle
    energy_expended = energy_expended + 1

    # Compose a double value for the payload (example: combine heartrate and energy_expended)
    double_value = float(heartrate) + float(energy_expended) / 1000.0
    print(
        f"Sending double payload: {double_value} (as 8 bytes)")
    return struct.pack('<d', double_value)


def read_sensor_location():
    """
    Reports the simulated heartrate sensor location.
    :return: bytes object for Body Sensor Location Characteristic
    """
    sensor_location = BodySensorLocation.CHEST
    print(f"Sending sensor location of {sensor_location!r}")
    return struct.pack('<B', sensor_location)


def update_value(characteristic):
    """
    Example of callback to send notifications

    :param characteristic:
    :return: boolean to indicate if timer should continue
    """
    global heartrate, energy_expended
    # read/calculate new value
    print("updating value")
    heartrate += 1
    if heartrate > 180:
        heartrate = 60
    energy_expended += 1
    double_value = float(heartrate) + float(energy_expended) / 1000.0
    # Causes characteristic to be updated and send notification
    characteristic.set_value(struct.pack('<d', double_value))
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


def write_control_point(value, options):
    """
    Called when a central writes to our write characteristic.

    :param value: data sent by the central
    :param options:
    """
    global energy_expended

    # Note use of control_point, to assign one or more values into variables
    # from struct.unpack output which returns a tuple
    control_point, = struct.unpack('<B', bytes(value))
    if control_point == HeartRateControlPoint.RESET_ENERGY_EXPENDED:
        print("Resetting Energy Expended from Sensor Control Point Request")
        energy_expended = 0


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
    """
    
    hr_monitor.add_characteristic(srv_id=1, chr_id=2, uuid=BODY_SNSR_LOC_UUID,
                                  value=[], notifying=False,
                                  flags=['read'],
                                  read_callback=read_sensor_location,
                                  write_callback=None,
                                  notify_callback=None
                                  )

    hr_monitor.add_characteristic(srv_id=1, chr_id=3, uuid=HR_CTRL_PT_UUID,
                                  value=[], notifying=False,
                                  flags=['write'],
                                  read_callback=None,
                                  write_callback=write_control_point,
                                  notify_callback=None
                                  ) """

    # Publish peripheral
    hr_monitor.publish()

    # Function to print heart rate periodically
    def print_heart_rate():
        print("sanity check\n")
        print(heartrate)
        async_tools.add_timer_seconds(1, print_heart_rate)

    # Start periodic print
    async_tools.add_timer_seconds(1, print_heart_rate)

    # Start Bluezero async event loop
    event_loop = async_tools.EventLoop()
    try:
        event_loop.run()
    except KeyboardInterrupt:
        hr_monitor.stop()

if __name__ == '__main__':
    # Get the default adapter address and pass it to main
    main(list(adapter.Adapter.available())[0].address)