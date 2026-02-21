import pyaudiowpatch as pyaudio
import numpy as np
import time

p = pyaudio.PyAudio()

# Indices from previous audits
# 5: Primary Sound Capture Driver (DirectSound)
# 13: Speaker (Realtek(R) Audio) [Loopback] (WASAPI)

def get_rms(idx, rate=44100):
    try:
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=rate, input=True, input_device_index=idx)
        data = stream.read(1024, exception_on_overflow=False)
        audio = np.frombuffer(data, dtype=np.int16)
        rms = np.sqrt(np.mean(audio.astype(np.float32)**2))
        stream.close()
        return rms
    except:
        return -1

print("Comparison Test (Play audio now!)")
for _ in range(5):
    rms_5 = get_rms(5)
    rms_13 = get_rms(13, rate=48000)
    print(f"DirectSound (5): {rms_5:.2f} | WASAPI Loopback (13): {rms_13:.2f}")
    time.sleep(0.5)

p.terminate()
