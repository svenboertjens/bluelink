#!/usr/bin/env python3

import bluelink_system_logs as syslogs
from bluelink_shared import Shared
from bluelink_manage import init
from colorama import Fore
import warnings
import signal
import types
import sys
import cmd

# Suppress the memory leak warning, as the memory is still in use elsewhere when received
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# This will hold the bluelink class
bluelink = None

def status():
    shared = Shared(test=True)
    
    # Check if there was a permission error and return if that's the case
    if shared.permission_error:
        print("Could not access shared data, please try running this with root.")
    
    print("Checking the status of bluelink...")
    
    if shared._is_active:
        # Bluelink is active
        print("Bluelink is active.")
        
        # Get the values of the shared memory
        discovering = shared._discovering
        connected = shared._connected
        disconnected = shared._disconnected
        
        # Delete the shared memory access point
        del shared
        
        # Print the state of the discovery loop
        print(f"Bluelink is {discovering and "discovering" or "not discovering"}.")
        
        # Print how many devices bluelink has connected to
        if len(connected) == 0:
            print("Bluelink has not connected to any devices")
        else:
            print(f"Bluelink has connected to {len(connected)} devices.")
        
        # Print how many devices the user has disconnected from
        if len(disconnected) == 0:
            print("You have not disconnected from any devices using bluelink.")
        else:
            print(f"You have disconnected from {len(disconnected)} devices using bluelink.")
        
    else:
        # Bluelink isn't active
        print("Bluelink is not active.")
        
# The help string for the CLI
help_string = f"""
{Fore.GREEN}--  --  Commands:
{Fore.LIGHTYELLOW_EX}list                              {Fore.CYAN}List the available devices
{Fore.LIGHTYELLOW_EX}connected                         {Fore.CYAN}List the connected devices
{Fore.LIGHTYELLOW_EX}paired                            {Fore.CYAN}List the paired devices

{Fore.LIGHTYELLOW_EX}connect     {Fore.LIGHTBLACK_EX}[MAC-addr] | [Num]    {Fore.CYAN}Connect to a device (automatically pairs if necessary)
{Fore.LIGHTYELLOW_EX}disconnect  {Fore.LIGHTBLACK_EX}[MAC-addr] | [Num]    {Fore.CYAN}Disconnect from a device

{Fore.LIGHTYELLOW_EX}pair        {Fore.LIGHTBLACK_EX}[MAC-addr] | [Num]    {Fore.CYAN}Pair with a device
{Fore.LIGHTYELLOW_EX}unpair      {Fore.LIGHTBLACK_EX}[MAC-addr] | [Num]    {Fore.CYAN}Unpair from a device


{Fore.LIGHTYELLOW_EX}status                            {Fore.CYAN}Print the state of the client and some other stuff
{Fore.LIGHTYELLOW_EX}quit | exit                       {Fore.CYAN}Exit the CLI

{Fore.GREEN}--  --  Arguments:
{Fore.LIGHTYELLOW_EX}[MAC-addr]                        {Fore.CYAN}The MAC address of the device (e.g., AA:BB:CC:DD:EE:FF)
{Fore.LIGHTYELLOW_EX}[Num]                             {Fore.CYAN}The number of the device in its respective list (e.g., from the `paired` list when unpairing){Fore.RESET}
"""

# Set the process ID to -2 to ensure an unused one is used if we haven't gotten a new one yet
process_id = -2

# Function to set the process ID
def set_process_id():
    # Get bluelink and check if it exists
    global bluelink
    if bluelink:
        # Get and assign the new process ID
        global process_id
        process_id = bluelink.start_process()

# Wrapper function to print errors
def error_wrapper():
    def decorator(f):
        def wrapper(*args, **kwargs):
            # Call the original function and get what it returns
            return_value = f(*args, **kwargs)
            
            # Get bluelink
            global bluelink
            # Check whether bluelink exists
            if bluelink:
                # Get the process ID
                global process_id
                # Get the exception
                exception = bluelink.get_exception(process_id=process_id)
                # Check whether the exception exists
                if exception:
                    # Print the exception
                    print(f"{Fore.RED}{exception}{Fore.RESET}")
            else:
                # Return True to exit if bluelink doesn't exist
                return True
                    
            # Return what the original value returned
            return return_value
        return wrapper
    return decorator

# Wrapper for the cmd.Cmd class
def apply_wrapper_to_class(cls):
    # Go over all items of the class
    for attr_name, attr_value in cls.__dict__.items():
        # Check whether it's a function
        if isinstance(attr_value, types.FunctionType):
            # Add the retry wrapper to the function
            setattr(cls, attr_name, error_wrapper()(attr_value))
            
    return cls

def signal_handler(sig, frame):
    print(f"{Fore.LIGHTBLACK_EX}Exiting...{Fore.RESET}")
    sys.exit(0)

@apply_wrapper_to_class
class BluelinkCLI(cmd.Cmd):
    # Ensure bluelink exists
    global bluelink
    if not bluelink:
        bluelink = init(cli=True)
        
        # Print a message and exit if we didn't receive bluelink, possibly due to a permission error
        if not bluelink:
            print("It appears root is required to run bluelink commands. Please try running this with root.")
            sys.exit(0)
            
    prompt = f"{Fore.LIGHTBLUE_EX}bluelink>{Fore.RESET} "
    
    # Set a new process ID
    set_process_id()
    
    # These can hold the list of the last available devices
    last_available = None
    last_connected = None
    last_paired = None
    
    def do_status(self, line):
        status()
    
    # Function to list the devices of a specified device type
    def _list_devices(self, device_type: str = None):
        # List the devices of the device type
        # Get the available devices from bluelink
        global process_id
        devices = bluelink.get_devices(process_id=process_id, device_type=device_type)
        # List of the devices stored based on numbers
        new_list = []
        
        # The number of the device
        num = 1
        
        # Print what each output means
        print(f"{Fore.LIGHTYELLOW_EX}Num:   MAC address:         Host name:\n{Fore.RESET}")
        
        # Go over all devices
        for mac, name in devices.items():
            # Print the number, MAC, and name of the device
            print(f"{Fore.LIGHTYELLOW_EX}{num}:{" " * (5 - int(num / 10))}{Fore.LIGHTBLACK_EX}{mac}    {Fore.CYAN}{name}{Fore.RESET}")
            num += 1
            # Store the device based on the number index
            new_list.append([mac, name])
        
        # Update the last devices list
        if not device_type:
            self.last_available = new_list
        elif device_type == "connected":
            self.last_connected = new_list
        elif device_type == "paired":
            self.last_paired = new_list
            
    # Function to get the MAC and name of a device, if available
    def _get_device(self, mac, device_type: str = None):
        devices = {}
        # Get the last devices based on the device type
        if not device_type:
            devices = self.last_available
        elif device_type == "connected":
            devices = self.last_connected
        elif device_type == "paired":
            devices = self.last_paired
            
        # Try to use it as a number
        try:
            # Convert to a number
            num = int(mac)
            # Check whether there's the last devices
            if not devices:
                print(f"{Fore.LIGHTRED_EX}Devices have not been assigned numbers yet, try listing them first.{Fore.RESET}")
                return None, None
            else:
                device = devices[num - 1]
                
                # Check whether the device exists
                if not device:
                    print(f"{Fore.LIGHTRED_EX}Number out of range. The range is from 1 to {len(devices)}.{Fore.RESET}")
                    return None, None
                else:
                    # Return the MAC addr and host name
                    return device[0], device[1]
        except:
            # Go over all available devices to see if it's found
            for device in devices:
                if device[0] == mac:
                    # Return the MAC address and the host name
                    return mac, device[1]
                    
            # Go over the available devices if not found in listed devices
            global process_id
            for device in bluelink.get_devices(process_id=process_id, device_type=device_type):
                if device[0] == mac:
                    # Return the MAC and name
                    return mac, device[1]
                        
            # If still not found
            print(f"{Fore.LIGHTRED_EX}MAC address is not available.{Fore.RESET}")
            return None, None
            
    def do_list(self, line):
        # List the available devices
        self._list_devices(None)
        
    def help_list(self, line):
        # Print the usage for list
        print(f"{Fore.CYAN}Usage: {Fore.LIGHTYELLOW_EX}list {Fore.LIGHTBLACK_EX}(no input){Fore.RESET}")
        
    def do_connected(self, line):
        # List the connected devices
        self._list_devices("connected")
        
    def help_connected(self, line):
        # Print the usage for connected
        print(f"{Fore.CYAN}Usage: {Fore.LIGHTBLACK_EX}connected (no input){Fore.RESET}")
        
    def do_paired(self, line):
        # List the paired devices
        self._list_devices("paired")
        
    def help_paired(self, line):
        # Print the usage for paired
        print(f"{Fore.CYAN}Usage: {Fore.LIGHTBLACK_EX}paired (no input){Fore.RESET}")

    def do_connect(self, mac):
        # Connect to a bluetooth device
        if mac:
            # Test the MAC and get the name
            mac, name = self._get_device(mac, None)
            if mac:
                # Connect to the device if the MAC exists
                global process_id
                bluelink.connect(process_id=process_id, mac=mac, name=name)
        else:
            # Print the help string for connect
            self.help_connect(mac)
            
    def help_connect(self, line):
        print(f"{Fore.CYAN}Usage: {Fore.LIGHTBLACK_EX}connect [MAC-addr] | [Num]{Fore.RESET}")
        
    def do_disconnect(self, mac):
        # Connect to a bluetooth device
        if mac:
            # Test the MAC and get the name
            mac, name = self._get_device(mac, "connected")
            if mac:
                # Connect to the device if the MAC exists
                global process_id
                bluelink.disconnect(process_id=process_id, mac=mac, name=name)
        else:
            # Print the help string for connect
            self.help_disconnect(mac)
            
    def help_disconnect(self, line):
        print(f"{Fore.CYAN}Usage: {Fore.LIGHTBLACK_EX}disconnect [MAC-addr] | [Num]{Fore.RESET}")
        
    def do_pair(self, mac):
        # Pair with a bluetooth device
        if mac:
            # Test the MAC and get the name
            mac, name = self._get_device(mac, None)
            if mac:
                # Pair with the device if the MAC exists
                global process_id
                bluelink.pair(process_id=process_id, mac=mac, name=name)
        else:
            # Print the help string for connect
            self.help_pair(mac)
            
    def help_pair(self, line):
        print(f"{Fore.CYAN}Usage: {Fore.LIGHTBLACK_EX}pair [MAC-addr] | [Num]{Fore.RESET}")
        
    def do_unpair(self, mac):
        # Unpair from a bluetooth device
        if mac:
            # Test the MAC and get the name
            mac, name = self._get_device(mac, "paired")
            if mac:
                # Unpair from the device if the MAC exists
                global process_id
                bluelink.unpair(process_id=process_id, mac=mac, name=name)
        else:
            # Print the help string for connect
            self.help_unpair(mac)
            
    def help_unpair(self, line):
        print(f"{Fore.CYAN}Usage: {Fore.LIGHTBLACK_EX}unpair [MAC-addr] | [Num]{Fore.RESET}")
    
    def do_help(self, line):
        # Print the help string
        print(help_string)
    
    def do_quit(self, line):
        # Exit the program
        print(f"{Fore.LIGHTBLACK_EX}Exiting...{Fore.RESET}")
        return True
    
    # Set the exit functions
    do_exit = do_quit
    do_EOF = do_quit

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    BluelinkCLI().cmdloop()
    
    