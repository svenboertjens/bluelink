#!/opt/pypackages/bin/python

import systemlogs as syslogs
from sysframe import membridge as mb
import subprocess
import threading
import signal
import time
import sys

class Bluelink:
    def __init__(self):
        self.active = True
        
        # The shared memory names for the shared handles
        self.shm_pair = '/bluelink-pair-handle'
        self.shm_unpair = '/bluelink-unpair-handle'
        self.shm_connect = '/bluelink-connect-handle'
        self.shm_disconnect = '/bluelink-disconnect-handle'
        self.shm_getdevices = '/bluelink-getdevices-handle'
        
        # Thread the function handles to offer them at the same time
        threading.Thread(target=mb.create_function, args=(self.shm_pair, self.pair,)).start()
        threading.Thread(target=mb.create_function, args=(self.shm_unpair, self.unpair,)).start()
        threading.Thread(target=mb.create_function, args=(self.shm_connect, self.connect,)).start()
        threading.Thread(target=mb.create_function, args=(self.shm_disconnect, self.disconnect,)).start()
        threading.Thread(target=mb.create_function, args=(self.shm_getdevices, self.get_devices,)).start()
        
        # Set termination signal links
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
        
        # Run the discovery loop
        self.discovery_loop()
    
    # Execute CLI commands
    def execute_ctl(self, commands):
        # Add the bluetoothctl command and execute
        commands.insert(0, "bluetoothctl")
        return subprocess.check_output(commands).decode("utf-8")
    
    # Pair with devices
    def pair(self, mac):
        # Check whether not already paired
        if mac not in self.get_devices('paired').keys():
            self.execute_ctl((f'pair {mac}',))
            self.execute_ctl((f'trust {mac}',))
            
            syslogs.log(f'Paired to device {mac}.')
            return True
        
        return False
            
    # Unpair from devices
    def unpair(self, mac):
       # Check whether actually paired
        if mac in self.get_devices('paired').keys():
            self.execute_ctl((f'remove {mac}',))
            self.execute_ctl((f'untrust {mac}',))
            
            syslogs.log(f'Unpaired from device {mac}.')
            return True
        
        return False
        
    # Connect to devices
    def connect(self, mac):
        # Check whether not already connected
        if mac not in self.get_devices('Connected'):
            # Pair with the device first
            self.pair(mac)
            # Connect to the device
            result = self.execute_ctl(f'connect {mac}')
            
            # Return the success state
            return result.lower().find("successful") != -1
        
        return False
            
    # Disconnect from devices
    def disconnect(self, mac):
        # Check whether actually connected
        if mac in self.get_devices('Connected'):
            # Connect to the device
            result = self.execute_ctl(f'disconnect {mac}')
            
            return result.lower().find("successful") != -1
        
        return False
                
    # Function to get the devices of a specific type, such as paired or trusted
    def get_devices(self, device_type: str):
        # Get the output from the paired devices list
        output = self.execute_ctl(('devices', device_type))
        
        # Split the output by separating based on newlines
        lines = output.split("\n")
        
        devices = {}
        
        # Go over all lines to extract the MAC and name
        for line in lines:
            # Continue if the line is empty
            if line == "": continue
            
            # Get the first and second index of the spaces in the line
            idx1 = line.find(" ")
            if idx1 == -1: continue
            
            idx2 = line.find(" ", idx1 + 1)
            if idx2 == -1: continue

            # Extract the MAC address and the host name from the string
            mac = line[idx1 + 1:idx2]
            name = line[idx2 + 1:]
            
            # And store them to the list
            devices[mac] = name
                
        # Return the list of devices
        return devices
    
    # Function to automatically connect to known devices
    def auto_connect(self, devices):
        # Go over all discovered devices
        for mac in devices.keys():
            # Check whether the device is paired and not in the connected or manually disconnected list
            if mac in self.paired and mac not in self.connected and mac not in disconnected:
                self.connect(mac)
    
    # Function to discover new devices in a loop
    def discovery_loop(self):
        while self.active:
            devices = self.get_devices('Connected')
            self.auto_connect(devices)
            time.sleep(5)
        
    # Function to shut down the class entirely
    def shutdown(self):
        syslogs.log("Shutting down bluelink.", "info")
        
        # Set inactive for the discovery loop
        self.active = False
        
        # Remove the function handles
        mb.remove_function(self.shm_pair)
        mb.remove_function(self.shm_unpair)
        mb.remove_function(self.shm_connect)
        mb.remove_function(self.shm_disconnect)
        mb.remove_function(self.shm_getdevices)
        
        syslogs.log("Succesfully shut down bluelink.", "info")
        sys.exit(0)


# Initiate bluelink
if __name__ == "__main__":
    Bluelink()

