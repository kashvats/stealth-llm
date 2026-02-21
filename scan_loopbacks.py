import pyaudiowpatch as pyaudio
import numpy as np
import time

p = pyaudio.PyAudio()

print("Scanning all WASAPI Loopback devices for signal...")
print("Please ensure you are playing audio (music/video) right now.")

found_working = False
for loopback in p.get_loopback_device_info_generator():
    print(f"Testing: {loopback['name']} (Index {loopback['index']})...", end=" ", flush=True)
    try:
        stream = p.open(format=pyaudio.paInt16,
                        channels=loopback["maxInputChannels"],
                        rate=int(loopback["defaultSampleRate"]),
                        input=True,
                        input_device_index=loopback["index"])
        
        # Read a few chunks to get a good RMS
        max_rms = 0
        for _ in range(10):
            data = stream.read(1024, exception_on_overflow=False)
            audio = np.frombuffer(data, dtype=np.int16)
            rms = np.sqrt(np.mean(audio.astype(np.float32)**2))
            max_rms = max(max_rms, rms)
        
        print(f"Max RMS: {max_rms:.2f}")
        if max_rms > 50: # Heuristic for "actual sound"
            print(f"  >>> SIGNAL DETECTED on index {loopback['index']}!")
            found_working = True
        
        stream.close()
    except Exception as e:
        print(f"FAIL: {e}")

if not found_working:
    print("\nNo active signal found on any loopback device.")
    print("Possibilities:")
    print("1. No audio is currently playing.")
    print("2. The audio is playing through a device not listed in WASAPI (unlikely).")
    print("3. System volume is extremely low.")

p.terminate()
