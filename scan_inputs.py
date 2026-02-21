import pyaudio
import numpy as np
import time

p = pyaudio.PyAudio()
print("Scanning all input devices for signal...")

working_indices = []
for i in range(p.get_device_count()):
    dev = p.get_device_info_by_index(i)
    if dev.get('maxInputChannels') > 0:
        print(f"Testing Index {i}: {dev.get('name')}...", end=" ", flush=True)
        try:
            stream = p.open(format=pyaudio.paInt16, 
                            channels=1, 
                            rate=int(dev.get('defaultSampleRate')) or 44100, 
                            input=True, 
                            input_device_index=i)
            # Read a bit
            data = stream.read(1024, exception_on_overflow=False)
            audio = np.frombuffer(data, dtype=np.int16)
            rms = np.sqrt(np.mean(audio.astype(np.float32)**2))
            print(f"OK (RMS: {rms:.2f})")
            working_indices.append(i)
            stream.close()
        except Exception as e:
            print(f"FAIL: {e}")

p.terminate()
