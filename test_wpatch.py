import pyaudiowpatch as pyaudio
import numpy as np
import time

p = pyaudio.PyAudio()

try:
    # Get default WASAPI info
    wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
except OSError:
    print("WASAPI not found.")
    p.terminate()
    exit()

# Find loopback device
default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
if not default_speakers["isLoopbackDevice"]:
    for loopback in p.get_loopback_device_info_generator():
        if default_speakers["name"] in loopback["name"]:
            default_speakers = loopback
            break

print(f"Capturing from: {default_speakers['name']}")

stream = p.open(format=pyaudio.paInt16,
                channels=default_speakers["maxInputChannels"],
                rate=int(default_speakers["defaultSampleRate"]),
                input=True,
                input_device_index=default_speakers["index"])

print("Listening for 2s...")
for _ in range(20):
    data = stream.read(1024, exception_on_overflow=False)
    audio = np.frombuffer(data, dtype=np.int16)
    rms = np.sqrt(np.mean(audio.astype(np.float32)**2))
    print(f"RMS: {rms:.2f}")
    time.sleep(0.1)

stream.close()
p.terminate()
