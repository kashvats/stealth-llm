import sounddevice as sd
import numpy as np

def test_stereomix_v2():
    devices = sd.query_devices()
    for i, dev in enumerate(devices):
        if ('stereo mix' in dev['name'].lower() or 'loopback' in dev['name'].lower()) and dev['max_input_channels'] > 0:
            print(f"Testing Device {i}: {dev['name']}")
            max_in = int(dev['max_input_channels'])
            for ch in range(1, max_in + 1):
                for sr in [16000, 44100, 48000]:
                    try:
                        with sd.InputStream(device=i, channels=ch, samplerate=sr):
                            print(f"  SUCCESS at {ch} channels, {sr}Hz!")
                            return
                    except Exception as e:
                        # print(f"  FAIL {ch}ch {sr}Hz: {e}")
                        pass
    print("ALL FAILED.")

if __name__ == "__main__":
    test_stereomix_v2()
