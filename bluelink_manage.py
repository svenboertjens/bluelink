#!/usr/bin/env python3

import bluelink_system_logs as syslogs
from collections.abc import Iterable
from bluelink_shared import Shared
import subprocess
import threading
import warnings
import signal
import types
import time
import sys

# Suppress the memory leak warning, as the memory is still in use elsewhere when received
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Initiate the shared class for shared memory variables
shared = Shared()

# This will hold a reference to the class
bluelink = None

# A fake function to return when a callable is expected but none is found
def fake_callable(self):
    return

# Function to attempt to solve some common kwargs argument issues
def solve_kwargs_issues(**kwargs):
    # List of the new kwargs
    new_kwargs = {}
    
    # Go over the values and the name of the variables. Log warnings where something was corrected
    for name, value in kwargs.items():
        value_type = type(value)
        # Check whether it's a process ID but not an integer
        if name == "process_id" and value_type != int:
            new_kwargs[name] = -1
            syslogs.log(f"An incorrect value was recieved as process ID. A '{str(int)}' was expected, got '{value_type}'.", "warning")
        # A non-callable function
        elif name == "function" and not callable(value):
            new_kwargs[name] = fake_callable
            syslogs.log(f"An incorrect value was recieved as function. A 'callable' was expected, got '{value_type}'.", "warning")
        # Invalid args
        elif name == "args" and value != None and not isinstance(value, Iterable):
            new_kwargs[name] = None
            syslogs.log(f"An incorrect value was recieved as args. An 'iterable' or 'None' was expected, got '{value_type}'.", "warning")
        # A non-string name
        elif name == "name" and value_type != str:
            new_kwargs[name] = "Unknown"
            syslogs.log(f"An incorrect value was recieved as name. A '{str(str)}' was expected, got '{value_type}'.", "warning")
        # An invalid device type
        elif name == "device_type":
            if value_type == str:
                # Lower the string
                value = value.lower()
                # Check whether the value is a valid argument for bluetoothctl, else set to None
                if value not in ["paired", "trusted", "bonded", "connected"]:
                    syslogs.log(f"An incorrect option was recieved as device type. Either 'paired', 'trusted', 'bonded', or 'connected' (capital letters don't matter) was expected, got '{value}'.", "warning")
                    value = None
            else:
                syslogs.log(f"An incorrect value was recieved as device type. A '{str(str)}' or 'None' was expected, got '{value_type}'.", "warning")
                value = None
            new_kwargs[name] = value
        # Else, just add it to the list without changes
        else:
            new_kwargs[name] = value
            
    return new_kwargs

# Wrapper function to automatically handle retries
def retry_wrapper(retries=2, delay=1):
    # Decorator for the wrapper
    def decorator(f):
        # Wrapper for the function to secure
        def wrapper(*args, **kwargs):
            # The retry attempts done
            attempts = 0
            # Try to run the function for the amount of retries minus the last one, which is handled differently
            while attempts < retries - 1:
                # Try to run the function normally
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    # Attempt to solve any kwargs issues and retry
                    kwargs = solve_kwargs_issues(**kwargs)
                    attempts += 1
                    # Check whether it's the second last attempt
                    if attempts >= retries - 1:
                        # Wait for the delay
                        time.sleep(delay)
                        # Re-init the bluetoothctl CLI in case that's causing problems
                        bluelink.__init__()
                        # Attempt to run it one last time
                        try:
                            return f(*args, **kwargs)
                        except:
                            # If it failed, try to get the process ID from the kwargs
                            process_id = "process_id" in kwargs and kwargs["process_id"] or None
                            # Else, try to find it in the args. If still not found, set it to -1
                            if process_id == None:
                                process_id = args[1] if len(args) > 1 else -1
                            # Get and check whether bluelink exists
                            if bluelink:
                                # Add the exception to the exceptions list
                                bluelink.handle_exceptions(process_id, f.__name__)
                            # Report the exception to the system logs
                            syslogs.log(bluelink.get_exception(process_id), "error")
                            
                    # Wait for the delay
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

# Wrapper for the bluelink class
def apply_retry_wrapper_to_class(cls):
    # Go over all items of the class
    for attr_name, attr_value in cls.__dict__.items():
        # Check whether it's a function
        if isinstance(attr_value, types.FunctionType):
            # Add the retry wrapper to the function
            setattr(cls, attr_name, retry_wrapper()(attr_value))
            
    return cls

@apply_retry_wrapper_to_class
class __Bluelink:
    # List of error messages for every function. The part "Something went wrong while " is added later
    error_messages = {
        "execute_ctl": "executing a command on the bluetooth CLI.",
        "__init__": "setting up the bluetoothctl CLI.",
        "run_threaded": "attempting to thread a certain command. Running it on the main thread.",
        "start_process": "assigning a new process ID.",
        "remove_exception": "attempting to remove an old exception.",
        "handle_exceptions": "attempting to store a new error.",
        "get_exception": "getting an exception from the stored errors.",
        "pair": "attempting to pair with a device.",
        "unpair": "attempting to unpair a device.",
        "connect": "attempting to connect with a device.",
        "auto_connect": "attempting to auto-connect to known devices.",
        "get_devices": "getting the nearby devices.",
        "scan_looped": "scanning for new devices in a loop.",
        "hash_mac": "hashing a MAC address."
    }
    # The number holding the latest process ID
    last_process = 0
    # List of exception messages of processes
    exceptions = {}
    # The CLI of the bluetoothctl
    ctl = None
    # Startup commands to start the CLI
    ctl_startup_commands = [
        "power on",
        "agent on",
        "default-agent",
        "scan on"
    ]
    
    # Function to execute commants with the bluetooth ctl
    def execute_ctl(self, process_id, command, wait: bool = True):
        self.ctl.stdin.write(command + "\n")
        self.ctl.stdin.flush()
        self.ctl.stdout.readline()
        
    def __init__(self):
        try:
            # Set up a bluetoothctl CLI that will continuously scan for devices and allows for connecting, pairing, and trusting devices
            self.ctl = subprocess.Popen(["bluetoothctl"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            # Execute the startup commands in a row
            for command in self.ctl_startup_commands:
                self.execute_ctl(process_id=0, command=command)
                
            syslogs.log("Initialized the bluetoothctl CLI.", "info")
            
            # Handle the SIGTERM and SIGINT signals
            signal.signal(signal.SIGTERM, self.sigterm_shutdown)
            signal.signal(signal.SIGINT, self.sigterm_shutdown)
        except Exception as e:
            # Shut down the class because it can't initialize
            self.shutdown()
            syslogs.log(f"The bluelink class could not initialize. Shutting down. Reason: {str(e)}", "critical")
    
    # Function to run something in a thread
    def run_threaded(self, process_id, function, args: any = None):
        if args:
            threading.Thread(target=function, args=args).start()
        else:
            threading.Thread(target=function).start()
        
    # Function to start a new process and get a process ID
    def start_process(self):
        # Increment the last process and return it as ID
        self.last_process += 1
        return self.last_process
    
    # Function to remove an exception after one minute
    def remove_exception(self, process_id):
        # Wait one minute
        time.sleep(60)
        # Delete the exception from the list if it still exists
        if process_id in self.exceptions:
            del self.exceptions[process_id]
        
    # Function to handle bluetooth exceptions
    def handle_exceptions(self, process_id, func_name):
        # Store the error code to the process ID to the list
        self.exceptions[process_id] = func_name
        # Thread the removal of the exception
        self.run_threaded(process_id=process_id, function=self.remove_exception, args=(process_id,))
        
    # Function to get the exception of a process
    def get_exception(self, process_id):
        # Check whether there's an exception related to the given ID
        if process_id in self.exceptions:
            # Get the function name that caused the error
            func_name = self.exceptions[process_id]
            # Delete the exception from the list
            del self.exceptions[process_id]
            
            # Check whether the function name is known
            if func_name in self.error_messages:
                # Return the error belonging to the function, and add the basic start of the sentence
                return f"Something went wrong while {self.error_messages[func_name]}"
            # An error occurred, but the function that caused isn't in this class
            return f"An unknown error has occurred. This likely happened outside of the bluelink class. The function this happened in was '{func_name}'."
        
        # No error occurred or found
        return None
        
    # Function to pair with devices (store and remember them)
    def pair(self, process_id, mac, name: str = None):
        # Check whether the device doesn't exist already
        if mac not in self.paired_devices:
            self.execute_ctl(process_id=process_id, command=f"pair {mac}")
            self.execute_ctl(process_id=process_id, command=f"trust {mac}")
            
            if name:
                syslogs.log(f"Paired with device '{name}'. MAC: '{mac}'", "info")
            else:
                syslogs.log(f"Paired with device. MAC: '{mac}'", "info")
            
    # Function to unpair with devices
    def unpair(self, process_id, mac, name: str = None):
        # Unpair and untrust the device
        self.execute_ctl(process_id=process_id, command=f"remove {mac}")
        self.execute_ctl(process_id=process_id, command=f"untrust {mac}")
        if name:
            syslogs.log(f"Unpaired from device '{name}'. MAC: '{mac}'", "info")
        else:
            syslogs.log(f"Unpaired from device. MAC: '{mac}'", "info")
        
    # Function to connect to devices
    def connect(self, process_id, mac, name: str = None):
        # Check whether the device isn't already connected
        if mac not in self.get_devices(process_id=process_id, device_type="connected"):
            # Pair with the device if not already done
            self.pair(process_id=process_id, mac=mac, name=name)
            # Connect to the device
            self.execute_ctl(process_id=process_id, command=f"connect {mac}")
            # Add the device to the list
            self.shared_check(shared.add_instance("connected", self.hash_mac(mac)))
            
    # Function to disconnect from devices
    def disconnect(self, process_id, mac, name: str = None):
        if mac in self.get_devices(process_id=process_id, device_type="connected"):
            # Disconnect from the device
            self.execute_ctl(process_id=process_id, command=f"disconnect {mac}")
            # Hash the MAC address
            hashed_mac = self.hash_mac(mac)
            # Remove the device from the list if it's in there
            if hashed_mac in self.shared_check(shared.get_instance("connected")):
                shared.remove_instance("connected", hashed_mac)
            # Add the device to the manually disconnected list
            shared.add_instance("disconnected", hashed_mac)
        
    # Function to automatically connect to known devices
    def auto_connect(self, process_id, devices):
        # Go over all discovered devices
        for mac, name in devices.items():
            # Hash the MAC address
            hashed_mac = self.hash_mac(mac)
            # Check whether the device is paired and not in the connected or manually disconnected list
            if mac in self.get_devices(process_id=process_id, device_type="paired") and hashed_mac not in shared.get_instance("connected") and hashed_mac not in shared.get_instance("disconnected"):
                self.connect(process_id=process_id, mac=mac, name=name)
                
    # Function to get the devices of a specific type, such as paired or trusted
    def get_devices(self, process_id, device_type: str = None):
        # The commands to enter
        input_list = ["bluetoothctl", "devices"]
        # Add the device type if it exists
        if device_type:
            input_list.append(device_type.capitalize())
            
        # Get the output from the paired devices list
        output = subprocess.check_output(input_list).decode("utf-8")
        # Split the output by separating based on newlines
        lines = output.split("\n")
        
        devices = {}
        
        # Go over all lines to extract the MAC and name
        for line in lines:
            # Continue if the line is empty
            if line == "":
                continue
            
            # Get the first and second index of the spaces in the line
            idx_1 = line.find(" ")
            idx_2 = line.find(" ", idx_1 and idx_1 + 1 or 0)
            
            # Make sure the indexes aren't the same
            if idx_1 != idx_2:
                # Extract the MAC address and the host name from the string
                mac = line[idx_1 + 1:idx_2]
                name = line[idx_2 + 1:]
                # And store them to the list
                devices[mac] = name
                
        if device_type and device_type.lower() == "paired":
            self.paired_devices = devices
                
        # Return the list of devices
        return devices
    
    discovering = False
    
    # Function to discover new devices in a loop
    def discover_loop(self, process_id):
        # Auto-connect to new devices every 5 seconds in a loop until the shared memory is up for deletion, indicating shutdown
        while self.shared_check(shared.get_instance()) != -1:
            devices = self.get_devices(process_id=process_id)
            self.auto_connect(process_id=process_id, devices=devices)
            time.sleep(5)
    
    # Function to convert MAC addresses into a hash to store them in the shared memory in a smaller size
    def hash_mac(self, mac):
        # The FNV offset bases and prime
        FNV_offset_basis = 0x811C9DC5
        FNV_prime = 0x01000193
        
        # This will be the hashed value
        hash_value = FNV_offset_basis
        
        # Go over all characters
        for char in mac:
            hash_value ^= ord(char)
            hash_value *= FNV_prime
            
        # Return a 32-bit number of the hash value
        return hash_value & 0xFFFFFFFF
    
    # Function to check whether the shared memory was shut down, indicating we need to shut down entirely
    def shared_check(self, returned_value):
        # If we receive the value -1, it means the memory is up for deletion
        if returned_value == -1:
            # Shut down the class
            self.shutdown()
        else:
            # Pass the return value to continue operation
            return returned_value
        
    # Function to shut down the class entirely
    def shutdown(self, quick: bool = False):
        syslogs.log("Shutting down a process of bluelink.", "info")
        # Stop the bluetoothctl CLI
        if not quick and self.ctl:
            try:
                self.ctl.stdin.write("exit\n")
                self.ctl.stdin.flush()
                self.ctl.terminate()
                del self.ctl
            except Exception as e:
                syslogs.log(f"Error terminating bluetoothctl CLI: {e}", "error")
        
            # Clear any exception states
            self.exceptions.clear()
        
        # Clean up the shared memory
        shared.cleanup()
        
        syslogs.log("Succesfully shut down a process of bluelink.", "info")
        
        # Exit the process entirely
        sys.exit(0)
        
    # Function for SIGINT termination signals
    def sigterm_shutdown(self, sig, frame):
        # Clean up the process quickly
        self.shutdown(quick=True)

# Function to initiate the class
def init(cli: bool = False):
    # Create the class and set it globally
    global bluelink
    bluelink = __Bluelink()
    
    syslogs.log(str(shared.get_instance()), "debug")
    
    # Check whether a discovery loop is already active
    if not shared.get_instance() and not cli:
        # Set the discovery state to True
        shared.set_instance(True)
        # Start the discover loop if it isn't active elsewhere
        bluelink.discover_loop(process_id=bluelink.start_process())
        
        
    # Return nothing if there was a permission error
    if shared.permission_error:
        return None
    # Return the class
    return bluelink

# Initiate the discovery loop for the class
if __name__ == "__main__":
    # Initiate on the main thread to keep the main thread for systemd
    syslogs.log("Initiating the device discovery process on the main thread.", "info")
    init()
elif not shared.get_instance():
    syslogs.log(f"Initiating the device discovery process on thread '{__name__}'.", "info")
    # Start the init on a thread to prevent halting the terminal
    threading.Thread(target=init).start()

