import pyaudio
import sys

def final_attempt():
    p = pyaudio.PyAudio()
    idx = 16
    try:
        dev = p.get_device_info_by_index(idx)
        print(f"Testing Device {idx}: {dev['name']}")
        # Try everything
        for rate in [44100, 48000]:
            for ch in [1, 2]:
                try:
                    stream = p.open(format=pyaudio.paInt16,
                                    channels=ch,
                                    rate=rate,
                                    input=True,
                                    input_device_index=idx)
                    print(f"SUCCESS: rate={rate}, channels={ch}")
                    stream.close()
                    p.terminate()
                    return
                except Exception as e:
                    print(f"FAIL (rate={rate}, ch={ch}): {e}")
    except Exception as e:
        print(f"Setup Error: {e}")
    p.terminate()

if __name__ == "__main__":
    final_attempt()
