"""Example of how to create a Peripheral device/GATT Server"""
# Standard modules
import logging
import struct
import time

# Bluezero modules
from bluezero import async_tools
from bluezero import adapter
from bluezero import peripheral


custom_service = '398629c8-4757-4e72-9b0d-8ebdd6ac82a2'
custom_charasteristic = '094bd4ad-3605-4912-b9d3-a6b91c573137'

heartrate = 60
value_update_timer_id = None  # Global timer ID
is_timer_running = False  # Flag to track timer state
last_update_time = 0  # Track the last time an update was made


def update_value_task(characteristic):
    """
    Called by the timer to update and send the characteristic value.
    Schedules the next update if notifications are still active.
    """
    global heartrate, value_update_timer_id, is_timer_running, last_update_time

    current_time = time.time()
    print(f"[{current_time:.2f}] Updating value, time since last update: {current_time - last_update_time:.2f}s")
    last_update_time = current_time
    
    heartrate += 1
    if heartrate > 180:
        heartrate = 60
    print(f"Current value: {heartrate}")
    
    # Only send notification if the characteristic is actually still notifying
    if characteristic.is_notifying:
        characteristic.set_value(struct.pack('<d', float(heartrate)))
        
        # Cancel any existing timer before creating a new one
        if value_update_timer_id is not None:
            print(f"WARNING: Timer already exists with ID {value_update_timer_id}, removing it first")
            try:
                async_tools.remove_timer(value_update_timer_id)
            except Exception as e:
                print(f"Error removing timer: {e}")
        
        # Schedule the next update with explicit timeout
        is_timer_running = True
        value_update_timer_id = async_tools.add_timer_seconds(5, update_value_task, characteristic)
        print(f"Scheduled next update with timer ID {value_update_timer_id}")
    else:
        print("Characteristic is no longer notifying, stopping timer chain")
        is_timer_running = False
        value_update_timer_id = None
    
    return True


def notify_callback(notifying, characteristic):
    """
    Called when a client subscribes or unsubscribes from notifications.
    Manages the lifecycle of the value update timer.
    """
    global value_update_timer_id, is_timer_running, last_update_time

    print(f"notify_callback called with notifying: {notifying}")

    if notifying:
        # Client subscribed - only start a timer if none is running
        if not is_timer_running:
            print("Starting value update timer chain.")
            # Mark the start time for timing calculations
            last_update_time = time.time()
            # Call task once to send immediate value and start the timer chain
            update_value_task(characteristic)
        else:
            print(f"Value update timer chain already active (ID: {value_update_timer_id}).")
    else:
        # Client unsubscribed
        if value_update_timer_id is not None:
            print(f"Stopping value update timer (ID: {value_update_timer_id}).")
            try:
                async_tools.remove_timer(value_update_timer_id)
                is_timer_running = False
                value_update_timer_id = None
            except Exception as e:
                print(f"Error removing timer: {e}")
        else:
            print("No active value update timer to stop.")
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
                                       local_name='airmodus',
                                       appearance=0x0905)
    # Add service
    hr_monitor.add_service(srv_id=1, uuid=custom_service, primary=True)

    # Set initial value to 8 bytes, no read_callback, notifying False
    hr_monitor.add_characteristic(srv_id=1, chr_id=1, uuid=custom_charasteristic,
                                  value=[0]*8, notifying=False,
                                  flags=['notify'],
                                  read_callback=None,  # No read_heartrate
                                  write_callback=None,
                                  notify_callback=notify_callback)

    # Publish peripheral
    hr_monitor.publish()

    # Start Bluezero async event loop
    event_loop = async_tools.EventLoop()
    event_loop.run()


if __name__ == '__main__':
    # Get the default adapter address and pass it to main
    main(list(adapter.Adapter.available())[0].address)