import sounddevice as sd
import platform

def audit_wasapi_v2():
    if platform.system() != "Windows": return
    
    try:
        wasapi_idx = next((idx for idx, h in enumerate(sd.query_hostapis()) if 'WASAPI' in h['name']), None)
        if wasapi_idx is None:
            print("No WASAPI host API.")
            return
            
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            if dev['hostapi'] == wasapi_idx and dev['max_output_channels'] > 0:
                print(f"Testing Device {i}: {dev['name']}")
                # Attempt to set loopback=True on WasapiSettings
                try:
                    # In some versions it might be sd.WasapiSettings(loopback=True)
                    # In others, we might need to use a different approach.
                    # Let's try every possible way.
                    
                    # Try 1: Constructor (already failed but let's be sure about the error)
                    try:
                        extra = sd.WasapiSettings(loopback=True)
                        with sd.InputStream(device=i, channels=2, samplerate=48000, extra_settings=extra):
                            print("    SUCCESS: Constructor loopback=True")
                            continue
                    except Exception as e:
                        print(f"    FAIL Constructor: {e}")

                    # Try 2: Attribute
                    try:
                        extra = sd.WasapiSettings()
                        # Use setattr to be safe
                        if hasattr(extra, 'loopback'):
                            extra.loopback = True
                            with sd.InputStream(device=i, channels=2, samplerate=48000, extra_settings=extra):
                                print("    SUCCESS: Attribute loopback=True")
                                continue
                        else:
                            print("    FAIL: No 'loopback' attribute on WasapiSettings")
                    except Exception as e:
                        print(f"    FAIL Attribute: {e}")

                except Exception as e:
                    print(f"    Critical error on device {i}: {e}")
                                
    except Exception as e:
        print(f"Audit Error: {e}")

if __name__ == "__main__":
    audit_wasapi_v2()
