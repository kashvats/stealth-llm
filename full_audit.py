import pyaudio
p = pyaudio.PyAudio()

print(f"{'Index':<5} {'HostAPI':<15} {'Channels':<10} {'Rate':<10} {'Name'}")
print("-" * 80)

for i in range(p.get_device_count()):
    dev = p.get_device_info_by_index(i)
    host_api = p.get_host_api_info_by_index(dev.get('hostApi')).get('name')
    print(f"{i:<5} {host_api:<15} {dev.get('maxInputChannels'):<10} {dev.get('defaultSampleRate'):<10} {dev.get('name')}")

p.terminate()
