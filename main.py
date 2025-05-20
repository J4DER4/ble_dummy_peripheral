"""Example of how to create a Peripheral device/GATT Server"""
# Standard modules
import logging
import struct
import sys
import time

# Bluezero modules
from bluezero import async_tools
from bluezero import adapter
from bluezero import peripheral


custom_service = '398629c8-4757-4e72-9b0d-8ebdd6ac82a2'
custom_charasteristic = '094bd4ad-3605-4912-b9d3-a6b91c573137'

heartrate = 60
# Simple lock to prevent multiple timers
timer_lock = False
last_update_time = 0  # Track the last time an update was made
# Default notification interval (seconds) - super short for rapid updates
notification_interval = 0.1  # 100 milliseconds


def update_value_task(characteristic, force_update=False):
    """
    Called by the timer to update and send the characteristic value.
    Schedules the next update if notifications are still active.
    
    Args:
        characteristic: The characteristic to update
        force_update: If True, ignore rate limiting (used for initial updates)
    """
    global heartrate, timer_lock, last_update_time

    current_time = time.time()
    
    # Rate limiting - but allow force_update to override
    #if interval-1 goes under 0 it will be set to 0
    interval_check = max(notification_interval-1, 0.02)
    if not force_update and current_time - last_update_time < interval_check:
        print(f"[{current_time:.2f}] Rate limiting: skipping update (only {current_time - last_update_time:.2f}s since last update)")
        return False
    
    # If another timer is already running, exit immediately
    if timer_lock:
        print("Timer already running, skipping this call")
        return False

    # Set lock to prevent other timers from running
    timer_lock = True
    
    try:
        print(f"[{current_time:.2f}] Updating value, time since last update: {current_time - last_update_time:.2f}s")
        last_update_time = current_time
        
        heartrate += 1
        if heartrate > 180:
            heartrate = 60
        print(f"Current value: {heartrate}")
        
        # Only send notification if the characteristic is actually still notifying
        if characteristic.is_notifying:
            characteristic.set_value(struct.pack('<d', float(heartrate)))
            
            # Instead of scheduling next update immediately, 
            # schedule it with a single-shot function
            def schedule_next():
                print(f"Delayed scheduling: Adding update in {notification_interval} seconds")
                async_tools.add_timer_seconds(notification_interval, update_value_task, characteristic)
            
            # Add a tiny delay to allow any pending timers to be processed
            print("Scheduling delayed timer creation in 0.1 seconds")
            async_tools.add_timer_seconds(0.01, schedule_next)
        else:
            print("Characteristic is no longer notifying, stopping timer chain")
    finally:
        # Release lock after processing is complete
        timer_lock = False
    
    return True


def notify_callback(notifying, characteristic):
    """
    Called when a client subscribes or unsubscribes from notifications.
    Manages the lifecycle of the value update timer.
    """
    global timer_lock, last_update_time

    print(f"notify_callback called with notifying: {notifying}")

    if notifying:
        # Client subscribed - only start a timer if none is running
        if not timer_lock:
            print("Starting value update timer chain.")
            # Mark the start time for timing calculations
            last_update_time = time.time()
            # Call task once to send immediate value and start the timer chain
            # Force the first update to happen regardless of timing
            update_value_task(characteristic, force_update=True)
        else:
            print("Value update timer already active.")
    else:
        print("Client unsubscribed from notifications")
        # The timer will stop automatically on next run because is_notifying will be False
    return True


def main(adapter_address, interval=0.1):
    """
    Creates advertises and starts the peripheral

    :param adapter_address: the MAC address of the hardware adapter
    :param interval: Notification interval in seconds (default: 0.1)
    """
    global notification_interval
    notification_interval = interval
    
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
    # Get command line argument for notification interval (default: 0.1 seconds)
    interval = 0.1
    if len(sys.argv) > 1:
        try:
            interval = float(sys.argv[1])
            print(f"Setting notification interval to {interval} seconds")
        except ValueError:
            print(f"Invalid interval value '{sys.argv[1]}'. Using default: {interval} seconds")
    
    # Get the default adapter address and pass it to main
    main(list(adapter.Adapter.available())[0].address, interval)