# Manager usage

This is the documentation on how you could use the `bluelink_manager.py` for your own projects.


## Initiation

To initiate the manager, you should either run the script directly, or import and call the `init` function.
This will handle the setting up of the device discovery loop for you, if it's not already active.
The `init` function will return the bluelink class.

If you want to get the class using `init` for simplified use (e.g. CLI mode), You can pass True when initiating: `init(True)`.

If you want to use the class in a more custom controlled way, you can simply get the class by importing the `__Bluelink` class.


Note: calling `init(True?)` will return `None` if there's a permission error, so handle that appropriately if permission can be a concern.


## Functions

Here I'll explain how you should use the functions provided by the bluelink class.


### `__init__(): <class>`

Called when creating the class.

#### Parameters:
The init function does not accept any arguments.

#### Returns:
Returns the class, obviously. Sets the `<class>.has_shutdown` variable to True if a shutdown occurs during initiation, indicating problems.


### `start_process(): <number>`

Get a process ID for exception retrieval.

#### Parameters:
This function does not accept any arguments.

#### Returns:
A session ID that you have to provide as argument in other function calls. This ID allows you to retrieve errors that occurred with your process.


### `get_exception(process_id: <number>): <string> | <none>`

Get the exception that occurred with your process.

#### Parameters:
- `process_id`: The ID of your process.

#### Returns:
The error message that was found at your ID, or `None` if there was no exception.


### `pair(process_id: <number>, mac: <string>, name: <string?> = None): <boolean>`

Pair and trust a device.

#### Parameters:
- `process_id`: The ID of your process.
- `mac`       : The MAC address of the device.
- `name:`     : The name of the device (optional, for logging purposes).

#### Returns:
A boolean indicating success or failure with True and False, respectively.


### `unpair(process_id: <number>, mac: <string>, name: <string?> = None): <boolean>`

Unpair and untrust a device.

#### Parameters:
- `process_id`: The ID of your process.
- `mac`       : The MAC address of the device.
- `name:`     : The name of the device (optional, for logging purposes).

#### Returns:
A boolean indicating success or failure with True and False, respectively.


### `connect(process_id: <number>, mac: <string>, name: <string?> = None): <boolean>`

Connect to a device. Automatically pairs to the device as well.

#### Parameters:
- `process_id`: The ID of your process.
- `mac`       : The MAC address of the device.
- `name:`     : The name of the device (optional, for logging purposes).

#### Returns:
A boolean indicating success or failure with True and False, respectively.


### `disconnect(process_id: <number>, mac: <string>, name: <string?> = None): <boolean>`

Disconnect from a device.

#### Parameters:
- `process_id`: The ID of your process.
- `mac`       : The MAC address of the device.
- `name:`     : The name of the device (optional, for logging purposes).

#### Returns:
A boolean indicating success or failure with True and False, respectively.


### `get_devices(process_id: <number>, device_type: <string?> = None): <dict<string>: <string>>`

Get the devices of a specific type.

#### Parameters:
- `process_id` : The ID of your process.
- `device_type`: The type of device state. Accepts `None` for available devices, or `paired`, `bonded`, `trusted`, or `connected`.

#### Returns:
A dict of the devices with the MAC address as key and the name as value: `{ mac: name }`.


### `shutdown(quick: <boolean?> = False): <void>`

Shut down all processes of bluelink.

#### Parameters:
- `quick`: Whether to clean up bluelink faster. This skips waiting for the internally used CLI to terminate.

#### Returns:
This function does not return anything.

