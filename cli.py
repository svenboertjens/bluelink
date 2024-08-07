#!/opt/pypackages/bin/python

import systemlogs as syslogs
from sysframe import membridge as mb
from colorama import Fore
import cmd

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
{Fore.LIGHTYELLOW_EX}[Num]                             {Fore.CYAN}The number of the device in its respective list (e.g., from the `paired` list when unpairing)
{Fore.RESET}"""

class BluelinkCLI(cmd.Cmd):
    # These will hold the results of the last devices check
    last_available = []
    last_connected = []
    last_paired = []
    
    # Function to list the devices of a specified device type
    def _list_devices(self, device_type: str):
        devices = mb.call_function('/bluelink-getdevices-handle', (device_type,))
        # Get the keys as the new list
        new_list = devices.keys()
        
        # Decor print
        print(f"{Fore.LIGHTYELLOW_EX}-------------------------------------------\nNum:   MAC address:         Host name:\n{Fore.RESET}")
        
        for i in range(1, len(new_list) + 1):
            # Print the number, MAC, and name of the device
            print(f"{Fore.LIGHTYELLOW_EX}{i}:{" " * (5 - (num // 10))}{Fore.LIGHTBLACK_EX}{mac}    {Fore.CYAN}{name}{Fore.RESET}")
        
        # Decor print
        print(f"{Fore.LIGHTYELLOW_EX}-------------------------------------------{Fore.RESET}")
        
        # Update the last devices list
        if device_type == '':
            self.last_available = new_list
        elif device_type == "Connected":
            self.last_connected = new_list
        elif device_type == "Paired":
            self.last_paired = new_list
    
    # Function to get the MAC and name of a device, if available
    def _get_device(self, mac, device_type: str = None):
        devices = {}
        
        # Get the last devices based on the device type
        if device_type == '':
            devices = self.last_available
        elif device_type == "Connected":
            devices = self.last_connected
        elif device_type == "Paired":
            devices = self.last_paired
        
        # Try to use it as a number
        try:
            num = int(mac)
            length = len(devices)
            
            # Check whether the number is valid
            if num < 1:
                print(f"{Fore.LIGHTRED_EX}Please enter a number larger than 0{Fore.RESET}")
                return None, None
            elif length < num:
                print(f"{Fore.LIGHTRED_EX}Number ({num}) is not in range ({length == 0 and 'empty' or f'1 - {length}'}){Fore.RESET}")
                return None, None
            else:
                device = devices[num - 1]
                return device[0], device[1]
        
        except:
            if mac in devices.keys():
                return devices[mac]
            else:
                print(f"{Fore.LIGHTRED_EX}Mac address ({mac}) was not found{Fore.RESET}")
    
    
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
                mb.call_function('/bluelink-connect-handle', (mac,))
        
        else:
            # Print the help string for connect
            self.help_connect(mac)
    
    def help_connect(self, line):
        print(f"{Fore.CYAN}Usage: {Fore.LIGHTBLACK_EX}connect [MAC-addr] | [Num]{Fore.RESET}")
    
    def do_disconnect(self, mac):
        # Connect to a bluetooth device
        if mac:
            # Test the MAC and get the name
            mac, name = self._get_device(mac, "Connected")
            if mac:
                mb.call_function('/bluelink-disconnect-handle', (mac,))
        
        else:
            # Print the help string for connect
            self.help_disconnect(mac)
    
    def help_disconnect(self, line):
        print(f"{Fore.CYAN}Usage: {Fore.LIGHTBLACK_EX}disconnect [MAC-addr] | [Num]{Fore.RESET}")
    
    def do_pair(self, mac):
        # Pair with a bluetooth device
        if mac:
            # Test the MAC and get the name
            mac, name = self._get_device(mac, '')
            if mac:
                mb.call_function('/bluelink-pair-handle', (mac,))

        else:
            # Print the help string for connect
            self.help_pair(mac)
    
    def help_pair(self, line):
        print(f"{Fore.CYAN}Usage: {Fore.LIGHTBLACK_EX}pair [MAC-addr] | [Num]{Fore.RESET}")
    
    def do_unpair(self, mac):
        # Unpair from a bluetooth device
        if mac:
            # Test the MAC and get the name
            mac, name = self._get_device(mac, "Paired")
            if mac:
                mb.call_function('/bluelink-unpair-handle', (mac,))
    
        else:
            # Print the help string for connect
            self.help_unpair(mac)
    
    def help_unpair(self, line):
        print(f"{Fore.CYAN}Usage: {Fore.LIGHTBLACK_EX}unpair [MAC-addr] | [Num]{Fore.RESET}")
    
    def do_help(self, line):
        print(help_string)
    
    def do_quit(self, line):
        return True
    
    # Set the exit functions
    do_exit = do_quit
    do_EOF = do_quit

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    BluelinkCLI().cmdloop()
    
    