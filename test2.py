from bluelink_shared import Shared

shared = Shared()

print(shared.get_instance("connected"))

print("Cleaning up..")
shared.cleanup()
print("Cleaned up!")

