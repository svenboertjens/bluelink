from multiprocessing import shared_memory
import warnings
import pickle

# Suppress the memory leak warning, as the memory is still in use elsewhere when received
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# This will hold theconnected devices shared memory for the wrapper
connected_devices = None

# Wrapper function to return -1 if the memory is up for deletion
def unlinked_wrapper(f):
    def wrapper(*args, **kwargs):
        # Check whether the first byte is zeroed out
        if not connected_devices or bytes(connected_devices.buf[:1]) == b"\x00":
            # Return -1 to indicate closed memory
            return -1
        # Call the function normally if the memory is open
        return f(*args, **kwargs)
    return wrapper

class Shared:
    def __init__(self, test: bool = False):
        # The max amount of bytes
        self.max_size = 256
        
        # Get the global connected_devices to assign to that one
        global connected_devices
        
        # Set a permission error variable to indicate whether this occurs later
        self.permission_error = False
        
        if test:
            try:
                # Try to link to the shared memory
                discovery_state = shared_memory.SharedMemory(name="BLUELINK-DISCOVERY-STATE")
                connected_devices = shared_memory.SharedMemory(name="BLUELINK-CONNECTED-DEVICES")
                manually_disconnected = shared_memory.SharedMemory(name="BLUELINK-MANUALLY-DISCONNECTED-DEVICES")
                
                # Check whether the connected devices is zeroed out
                if connected_devices.buf[0] == b"\x00":
                    self._is_active = False
                else:
                    self._is_active = True
                    # Get whether we are discovering
                    self._discovering = discovery_state.buf[0] == 1
                    # Get the connected and disconnected devices
                    self._connected = self.buffer_to_array(connected_devices)
                    self._disconnected = self.buffer_to_array(connected_devices)
                    
            except FileNotFoundError:
                # The class is not active because the shared memory doesn't exist
                self._is_active = False
            except PermissionError:
                # Set a variable to indicate we couldn't open shared mamory
                self.permission_error = True
                
        else:
            try:
                # Attempt to get the existing shared memory files
                self.discovery_state = shared_memory.SharedMemory(name="BLUELINK-DISCOVERY-STATE")
                self.connected_devices = shared_memory.SharedMemory(name="BLUELINK-CONNECTED-DEVICES")
                self.manually_disconnected = shared_memory.SharedMemory(name="BLUELINK-MANUALLY-DISCONNECTED-DEVICES")
            except FileNotFoundError:
                # Create the instances because they don't exist
                self.discovery_state = shared_memory.SharedMemory(name="BLUELINK-DISCOVERY-STATE", create=True, size=1)
                self.connected_devices = shared_memory.SharedMemory(name="BLUELINK-CONNECTED-DEVICES", create=True, size=self.max_size)
                self.manually_disconnected = shared_memory.SharedMemory(name="BLUELINK-MANUALLY-DISCONNECTED-DEVICES", create=True, size=self.max_size)
                # Assign False to the boolean instance (0 = False, 1 = True)
                self.discovery_state.buf[0] = 0
                
                # Make an empty array as bytes
                empty_pickle_arr = pickle.dumps([])
                # Fill the bytes array with
                empty_arr = empty_pickle_arr + b'\x00' * (self.max_size - len(empty_pickle_arr))
                self.connected_devices.buf[:self.max_size] = empty_arr
                self.manually_disconnected.buf[:self.max_size] = empty_arr
                
                # Set the global conencted devices shm for the wrapper
                connected_devices = self.connected_devices
                
                # Make a list of the list instances to get them by key
                self.lists = {
                    "connected": self.connected_devices,
                    "disconnected": self.manually_disconnected
                }
            except PermissionError:
                # Set a variable to indicate we couldn't open shared mamory
                self.permission_error = True
                
    
    def buffer_to_array(self, shm):
        # Create an array out of the bytes
        bytes_array = bytes(shm.buf[:self.max_size])
        # Get and return the array from the bytes
        arr = pickle.loads(bytes_array)
        return arr
    
    def array_to_buffer(self, shm, arr):
        # Convert the array into a bytes array
        bytes_array = pickle.dumps(arr)
        # Calculate how many bytes need to be added and fill them with zeroes
        to_add = self.max_size - len(bytes_array)
        bytes_array = bytes_array + b"\x00" * to_add
        # Set the bytes array to the buffer
        shm.buf[:self.max_size] = bytes_array
    
    # Zero out the memory of a buffer by writing all zeroes
    def clean_buffer(self, shm, size = None):
        # Set the size to the max size if it isn't set
        size = size and size or self.max_size
        try:
            # Attempt to zero out, close, and unlink the memory
            shm.buf[:size] = b"\x00" * size
            shm.close()
            shm.unlink()
        except:
            # Pass if it doesn't work because it's non-existent already
            pass
    
    @unlinked_wrapper
    def get_instance(self, value_type = None):
        if value_type in self.lists:
            return self.buffer_to_array(self.lists[value_type])
        else:
            return self.discovery_state.buf[0] == 1
    
    @unlinked_wrapper
    def add_instance(self, value_type, value):
        # Get the current values
        values = self.buffer_to_array(self.lists[value_type])
        
        # Check whether the value doesn't already exist
        if value not in values:
            # Add the value to the list
            values.append(value)
            # Update the shared list
            self.array_to_buffer(self.lists[value_type], values)
    
    @unlinked_wrapper
    def remove_instance(self, value_type, value):
        try:
            # Get the values
            values = self.buffer_to_array(self.items[value_type])
            # Try to remove the value
            values.remove(value)
            # Update the shared list
            self.array_to_buffer(self.lists[value_type], values)
        except Exception as e:
            # Catch the error if it doesn't exist
            pass
    
    @unlinked_wrapper
    def set_instance(self, value):
        self.discovery_state.buf[0] = value and 1 or 0
    
    def cleanup(self):
        # Clean up all memory addresses
        self.clean_buffer(self.discovery_state, 1)
        self.clean_buffer(self.connected_devices)
        self.clean_buffer(self.manually_disconnected)

