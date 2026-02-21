import pyaudiowpatch as pyaudio
import numpy as np
import wave
import time

p = pyaudio.PyAudio()
try:
    wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
    default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
    
    if not default_speakers["isLoopbackDevice"]:
        for loopback in p.get_loopback_device_info_generator():
            if default_speakers["name"] in loopback["name"]:
                default_speakers = loopback
                break
    
    print(f"DEBUG: Default Speakers: {default_speakers['name']}")
    
    CHANNELS = default_speakers["maxInputChannels"]
    RATE = int(default_speakers["defaultSampleRate"])
    CHUNK = 1024
    RECORD_SECONDS = 3
    WAVE_OUTPUT_FILENAME = "debug_audio.wav"

    stream = p.open(format=pyaudio.paInt16,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    input_device_index=default_speakers["index"],
                    frames_per_buffer=CHUNK)

    print("* recording")
    frames = []
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
        # RMS check
        audio = np.frombuffer(data, dtype=np.int16)
        rms = np.sqrt(np.mean(audio.astype(np.float32)**2))
        if i % 10 == 0: print(f"RMS: {rms:.2f}")

    print("* done recording")

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    print(f"Saved to {WAVE_OUTPUT_FILENAME}")

except Exception as e:
    print(f"Error: {e}")
    p.terminate()
