import pyaudio
import numpy as np

def test_stereomix_v3():
    p = pyaudio.PyAudio()
    idx = 16 # Stereo Mix
    print(f"Testing Device 16: Stereo Mix")
    for ch in [1, 2]:
        for sr in [16000, 44100, 48000]:
            for fmt in [pyaudio.paInt16, pyaudio.paFloat32]:
                try:
                    stream = p.open(format=fmt, channels=ch, rate=sr, input=True, input_device_index=idx)
                    print(f"  SUCCESS: ch={ch}, sr={sr}, fmt={fmt}")
                    stream.close()
                except:
                    pass
    p.terminate()

if __name__ == "__main__":
    test_stereomix_v3()
