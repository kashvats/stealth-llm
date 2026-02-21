import pyaudio
p = pyaudio.PyAudio()

print("--- HOST APIS ---")
for i in range(p.get_host_api_count()):
    print(p.get_host_api_info_by_index(i))

print("\n--- POTENTIAL LOOPBACK DEVICES ---")
targets = []
for i in range(p.get_device_count()):
    dev = p.get_device_info_by_index(i)
    name = dev.get('name').lower()
    if "stereo mix" in name or "pc speaker" in name or "loopback" in name:
        print(f"Index {i}: {dev.get('name')} (HostAPI: {dev.get('hostApi')}, Inputs: {dev.get('maxInputChannels')}, Rate: {dev.get('defaultSampleRate')})")
        targets.append(i)

print("\n--- TESTING ---")
rates = [48000, 44100, 16000]
channels = [2, 1]
formats = [pyaudio.paInt16, pyaudio.paFloat32]

for idx in targets:
    dev_info = p.get_device_info_by_index(idx)
    print(f"\nTesting Device {idx}: {dev_info.get('name')}")
    success = False
    for r in rates:
        for c in channels:
            for f in formats:
                try:
                    stream = p.open(format=f, channels=c, rate=r, input=True, input_device_index=idx)
                    print(f"  [WORKS] Rate: {r}, Ch: {c}, Format: {f}")
                    stream.close()
                    success = True
                except Exception as e:
                    # print(f"  [FAIL] Rate: {r}, Ch: {c}: {e}")
                    pass
    if not success:
        print("  [ALL COMBINATIONS FAILED]")

p.terminate()
