#!/opt/bluelink/venv/bin/python

import subprocess
import signal
import time
import sys

class Bluelink:
    def __init__(self) -> None:
        self.active = True
        
        # Set termination signal links
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
        
        # Run the discovery loop if on main
        if __name__ == '__main__':
            self.discovery_loop()
    
    # Execute CLI commands
    def execute_ctl(self, commands: list) -> str:
        # Add the bluetoothctl command and execute
        commands.insert(0, "bluetoothctl")
        return subprocess.check_output(commands).decode("utf-8")
    
    # Pair with devices
    def pair(self, mac: str) -> bool:
        # Check whether not already paired
        if mac not in self.get_devices('Paired').keys():
            self.execute_ctl(['pair', mac])
            self.execute_ctl(['trust', mac])
            
            return True
        
        return False
    
    # Unpair from devices
    def unpair(self, mac: str) -> bool:
       # Check whether actually paired
        if mac in self.get_devices('Paired').keys():
            self.execute_ctl(['remove', mac])
            self.execute_ctl(['untrust', mac])
            
            return True
        
        return False
    
    # Connect to devices
    def connect(self, mac: str) -> bool:
        # Check whether not already connected
        if mac not in self.get_devices('Connected'):
            # Pair with the device first
            self.pair(mac)
            # Connect to the device
            result = self.execute_ctl(['connect', mac])
            
            # Return the success state
            return result.lower().find("successful") != -1
        
        return False
    
    # Disconnect from devices
    def disconnect(self, mac: str) -> bool:
        # Check whether actually connected
        if mac in self.get_devices('Connected'):
            # Connect to the device
            result = self.execute_ctl(['disconnect', mac])
            
            return result.lower().find("successful") != -1
        
        return False
         
    # Function to get the devices of a specific type, such as paired or trusted
    def get_devices(self, device_type: str) -> dict:
        # Get the output from the paired devices list
        output = self.execute_ctl(device_type == '' and ['devices'] or ['devices', device_type])
        
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
    def auto_connect(self, devices: dict) -> None:
        # Go over all discovered devices
        for mac in devices.keys():
            # Check whether the device is paired and not in the connected or manually disconnected list
            if mac in self.get_devices('Paired').keys() and mac not in self.get_devices('Connected').keys():
                self.connect(mac)
    
    # Function to discover new devices in a loop
    def discovery_loop(self) -> None:
        while self.active:
            devices = self.get_devices('')
            self.auto_connect(devices)
            time.sleep(5)
    
    # Function to shut down the class entirely
    def shutdown(self) -> None:
        # Set inactive for the discovery loop
        self.active = False
        sys.exit()

# Initiate bluelink
if __name__ == '__main__':
    Bluelink()

