#!/opt/bluelink/venv/bin/python

from manager import Bluelink
import cmd

# The help string for the CLI
help_string = """
\033[32m--  --  Commands:
\033[93mlist | available                  \033[36mList the available devices
\033[93mconnected                         \033[36mList the connected devices
\033[93mpaired                            \033[36mList the paired devices

\033[93mconnect     \033[90m[MAC-addr] | [Num]    \033[36mConnect to a device (automatically pairs if necessary)
\033[93mdisconnect  \033[90m[MAC-addr] | [Num]    \033[36mDisconnect from a device

\033[93mpair        \033[90m[MAC-addr] | [Num]    \033[36mPair with a device
\033[93munpair      \033[90m[MAC-addr] | [Num]    \033[36mUnpair from a device

\033[93mquit | exit                       \033[36mExit the CLI

\033[32m--  --  Arguments:
\033[93m[MAC-addr]                        \033[36mThe MAC address of the device (e.g., AA:BB:CC:DD:EE:FF)
\033[93m[Num]                             \033[36mThe number of the device in its respective list (e.g., from the `paired` list when unpairing)
\033[39m"""

class BluelinkCLI(cmd.Cmd):
    # These will hold the results of the last devices check
    last_available = []
    last_connected = []
    last_paired = []
    
    bl = Bluelink()
    
    print('')
    prompt = f'\033[36m|bluelink: \033[39m'
    
    # Function to list the devices of a specified device type
    def _list_devices(self, device_type: str):
        devices = self.bl.get_devices(device_type)
        
        # Get the keys as the new list
        new_list = list(devices.keys())
        
        # Decor print
        print(f"\033[93m-------------------------------------------\nNum:   MAC address:         Host name:\n\033[39m")
        
        for i, (mac, name) in enumerate(devices.items()):
            # Print the number, MAC, and name of the device
            print(f"\033[93m{i}:{" " * (5 - (i // 10))}\033[90m{mac}    \033[36m{name}\033[39m")
        
        # Decor print
        print(f"\n\033[93m-------------------------------------------\033[39m")
        
        # Update the last devices list
        if device_type == '':
            self.last_available = new_list
        elif device_type == "Connected":
            self.last_connected = new_list
        elif device_type == "Paired":
            self.last_paired = new_list
    
    # Function to get the MAC and name of a device, if available
    def _get_device(self, mac, device_type: str):
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
            if num < 0:
                print(f"\033[91mPlease enter a positive number.\033[39m")
                return None
            elif length <= num:
                print(f"\033[91mNumber ({num}) is not in range ({length == 0 and 'empty' or f'0 - {length - 1}'})\033[39m")
                return None
            else:
                print(devices)
                device = devices[num]
                print(device)
                return device
        
        except:
            if mac in devices:
                return mac
            else:
                print(f"\033[91mMac address ({mac}) was not found\033[39m")
    
    
    def do_list(self, line):
        # List the available devices
        self._list_devices('')
    
    do_avaliable = do_list
    
    def help_list(self, line):
        # Print the usage for list
        print(f"\033[36mUsage: \033[93mlist | available \033[90m(no input)\033[39m")
    
    help_available = help_list
    
    def do_connected(self, line):
        # List the connected devices
        self._list_devices("Connected")
    
    def help_connected(self, line):
        # Print the usage for connected
        print(f"\033[36mUsage: \033[90mconnected (no input)\033[39m")
    
    def do_paired(self, line):
        # List the paired devices
        self._list_devices("Paired")
    
    def help_paired(self, line):
        # Print the usage for paired
        print(f"\033[36mUsage: \033[90mpaired (no input)\033[39m")
    
    def do_connect(self, mac):
        # Connect to a bluetooth device
        if mac:
            # Test the MAC and get the name
            mac = self._get_device(mac, '')
            if mac:
                if self.bl.connect(mac):
                    print(f"\033[92mSuccessfully connected to device ({mac}).\033[39m")
                else:
                    print(f"\033[91mFailed to connect to device ({mac}).\033[39m")
        
        else:
            # Print the help string for connect
            self.help_connect(mac)
    
    def help_connect(self, line):
        print(f"\033[36mUsage: \033[90mconnect [MAC-addr] | [Num]\033[39m")
    
    def do_disconnect(self, mac):
        # Connect to a bluetooth device
        if mac:
            # Test the MAC and get the name
            mac = self._get_device(mac, "Connected")
            if mac:
                if self.bl.disconnect(mac):
                    print(f"\033[92mSuccessfully disconnected from device ({mac}).\033[39m")
                else:
                    print(f"\033[91mFailed to disconnect from device ({mac}).\033[39m")
        
        else:
            # Print the help string for connect
            self.help_disconnect(mac)
    
    def help_disconnect(self, line):
        print(f"\033[36mUsage: \033[90mdisconnect [MAC-addr] | [Num]\033[39m")
    
    def do_pair(self, mac):
        # Pair with a bluetooth device
        if mac:
            # Test the MAC and get the name
            mac = self._get_device(mac, '')
            if mac:
                if self.bl.pair(mac):
                    print(f"\033[92mSuccessfully paired with device ({mac}).\033[39m")
                else:
                    print(f"\033[91mFailed to pair with device ({mac}).\033[39m")

        else:
            # Print the help string for connect
            self.help_pair(mac)
    
    def help_pair(self, line):
        print(f"\033[36mUsage: \033[90mpair [MAC-addr] | [Num]\033[39m")
    
    def do_unpair(self, mac):
        # Unpair from a bluetooth device
        if mac:
            # Test the MAC and get the name
            mac = self._get_device(mac, "Paired")
            if mac:
                if self.bl.unpair(mac):
                    print(f"\033[92mSuccessfully unpaired from device ({mac}).\033[39m")
                else:
                    print(f"\033[91mFailed to unpair from device ({mac}).\033[39m")
    
        else:
            # Print the help string for connect
            self.help_unpair(mac)
    
    def help_unpair(self, line):
        print(f"\033[36mUsage: \033[90munpair [MAC-addr] | [Num]\033[39m")
    
    def do_help(self, line):
        print(help_string)
    
    def do_quit(self, line):
        print(f'\033[36m^\033[39m')
        return True
    
    # Set the exit functions
    do_exit = do_quit
    do_EOF = do_quit

if __name__ == "__main__":
    BluelinkCLI().cmdloop()

