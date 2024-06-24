from bluelink_shared import Shared

shared = Shared()

shared.add_instance("connected", 123)

import time
time.sleep(10)

result = shared.add_instance("connected", 456)

if result == -1:
    print("Cleaning up..")
    shared.cleanup()
    print("Cleaned up!")

