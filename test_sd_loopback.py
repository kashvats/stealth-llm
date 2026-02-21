import sounddevice as sd
import numpy as np
import time

device_index = 10 # Speaker (Realtek(R) Audio) on WASAPI
samplerate = 48000

print(f"Testing Loopback on Device {device_index}...")

def callback(indata, frames, time, status):
    if status:
        print(status)
    print(f"Captured {len(indata)} frames. RMS: {np.sqrt(np.mean(indata**2)):.6f}")

try:
    # Use WasapiSettings for loopback
    wasapi_settings = sd.WasapiSettings(loopback=True)
    
    with sd.InputStream(samplerate=samplerate,
                        device=device_index,
                        channels=2,
                        extra_settings=wasapi_settings,
                        callback=callback):
        print("Success! Capturing for 2 seconds...")
        time.sleep(2)
except Exception as e:
    print(f"Failed: {e}")
