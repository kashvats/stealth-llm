import sounddevice as sd
print("--- SOUNDDEVICE AUDIT ---")
print(sd.query_devices())
print("\n--- HOST APIS ---")
print(sd.query_hostapis())

def get_wasapi_loopback():
    devices = sd.query_devices()
    for i, dev in enumerate(devices):
        if dev['hostapi'] == 2 and dev['max_input_channels'] == 0: # Check output devices on WASAPI
             # We can't query loopback directly easily without trying to open it
             print(f"Index {i}: {dev['name']} (WASAPI Output)")
    
get_wasapi_loopback()
