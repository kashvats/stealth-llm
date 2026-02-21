import threading
import time
import queue
import collections
import numpy as np
import pyaudio
import logging
import platform
from typing import Callable, Optional

# Try to import faster_whisper, handle explicit failure if missing
try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

logger = logging.getLogger(__name__)

class AudioTranscriber:
    def __init__(self, 
                 model_size: str = "tiny.en", 
                 device: str = "cpu", 
                 compute_type: str = "int8",
                 on_partial: Optional[Callable[[str], None]] = None,
                 on_final: Optional[Callable[[str], None]] = None,
                 on_volume: Optional[Callable[[float], None]] = None):
        
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.on_partial = on_partial
        self.on_final = on_final
        self.on_volume = on_volume
        
        self.running = False
        self.audio_queue = queue.Queue()
        self.speech_buffer = collections.deque(maxlen=int(16000 * 5 / 1024)) # 5s hard cap
        self.samplerate = 16000
        self.chunk_size = 1024
        
        # VAD Parameters
        self.vad_threshold_base = 0.002
        self.vad_threshold = self.vad_threshold_base
        self.noise_gate_alpha = 0.05
        self.ambient_noise_level = 0.0005
        
        self.silence_duration_trigger = 0.8 # 800ms silence for sentence finalization
        self.max_record_time = 30.0
        
        self.last_speech_time = 0
        self.is_speaking = False
        self.last_partial_time = 0
        self.partial_interval = 0.5
        
        self.model = None
        self.paused = False

    def _load_model(self):
        if not WhisperModel:
            logger.error("faster_whisper not installed.")
            return
            
        logger.info(f"Loading Whisper Model: {self.model_size} on {self.device}...")
        try:
            self.model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
            logger.info("Whisper Model Loaded.")
        except Exception as e:
            logger.error(f"Failed to load Whisper Model: {e}")

    def pause(self):
        logger.info("Audio capture paused.")
        self.paused = True

    def resume(self):
        logger.info("Audio capture resumed.")
        self.paused = False

    def start(self):
        if not WhisperModel:
            logger.error("Cannot start: faster_whisper missing.")
            return

        self.running = True
        self._load_model()
        
        self.record_thread = threading.Thread(target=self._record_loop, daemon=True)
        self.process_thread = threading.Thread(target=self._process_loop, daemon=True)
        
        self.record_thread.start()
        self.process_thread.start()
        logger.info("AudioTranscriber started.")

    def stop(self):
        self.running = False
        if hasattr(self, 'record_thread'):
            self.record_thread.join(timeout=1)
        if hasattr(self, 'process_thread'):
            self.process_thread.join(timeout=1)
        logger.info("AudioTranscriber stopped.")

    def _get_potential_loopback_devices(self, p):
        """Returns a list of device indices that might be loopbacks."""
        candidates = []
        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            name = dev.get('name').lower()
            if dev.get('maxInputChannels') > 0:
                # Priority 1: PC Speaker or Stereo Mix
                if "pc speaker" in name or "stereo mix" in name or "loopback" in name or "what u hear" in name:
                    candidates.insert(0, i)
                # Priority 2: Non-mic input (Strictly exclude keywords)
                elif not any(k in name for k in ["mic", "microphon", "hands-free", "array"]):
                    # Only add if it's not a mapper or generic capture driver which usually defaults to mic
                    if "mapper" not in name and "primary" not in name:
                         candidates.append(i)
        return candidates

    def _record_loop(self):
        try:
            import pyaudiowpatch as pyaudio
            p = pyaudio.PyAudio()
            
            # Find all loopback candidates
            candidates = list(p.get_loopback_device_info_generator())
            
            # Find Default WASAPI Speakers to prioritize
            wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_speakers_idx = wasapi_info["defaultOutputDevice"]
            default_speakers = p.get_device_info_by_index(default_speakers_idx)
            
            # Sort candidates: Default first
            candidates.sort(key=lambda x: 0 if default_speakers["name"] in x["name"] else 1)
            
            logger.info(f"Scanning {len(candidates)} loopback candidates for signal...")
            selected_dev = None
            rate, channels = 48000, 1
            
            # Test each for signal
            for dev in candidates:
                try:
                    logger.info(f"  Testing {dev['name']} (Index {dev['index']})...")
                    # Using a very short duration for the test read
                    temp_stream = p.open(format=pyaudio.paInt16,
                                         channels=dev["maxInputChannels"],
                                         rate=int(dev["defaultSampleRate"]),
                                         input=True,
                                         input_device_index=dev["index"])
                    
                    frames = []
                    # Read only 2 chunks for speed
                    for _ in range(2):
                        frames.append(temp_stream.read(self.chunk_size, exception_on_overflow=False))
                    temp_stream.close()
                    
                    audio_data = np.frombuffer(b''.join(frames), dtype=np.int16).astype(np.float32)
                    rms = np.sqrt(np.mean(audio_data**2))
                    logger.info(f"    Signal RMS: {rms:.2f}")
                    
                    if rms > 10.0: 
                         selected_dev = dev
                         rate, channels = int(dev["defaultSampleRate"]), dev["maxInputChannels"]
                         logger.info(f"  >>> ACTIVE SIGNAL DETECTED on {dev['name']}. Prioritizing.")
                         break
                except Exception as e:
                    logger.debug(f"    Scan failed on {dev['index']}: {e}")
                    continue
            
            # Absolute fallback
            if not selected_dev:
                selected_dev = candidates[0]
                rate, channels = int(selected_dev["defaultSampleRate"]), selected_dev["maxInputChannels"]
                logger.info(f"No active signal found during startup. Defaulting to: {selected_dev['name']}")
            
            logger.info(f"Final Selection: {selected_dev['name']} (Channels: {channels}, Rate: {rate})")
            
            # Explicitly mark offline
            logger.info("Transcription Engine (Whisper) is operating in LOCAL mode (Offline).")
            
            stream = p.open(format=pyaudio.paInt16,
                             channels=channels,
                             rate=rate,
                             input=True,
                             input_device_index=selected_dev["index"],
                             frames_per_buffer=self.chunk_size)

        except Exception as e:
            logger.warning(f"Loopback auto-scan failed: {e}")
            import pyaudio
            p = pyaudio.PyAudio()
            # Standard Fallback
            stream = None
            for i in range(p.get_device_count()):
                dev = p.get_device_info_by_index(i)
                if dev.get('maxInputChannels') > 0 and any(k in dev.get('name').lower() for k in ["mix", "speaker", "loopback"]):
                     try:
                         stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, input_device_index=i)
                         channels, rate = 1, 44100
                         break
                     except: pass
            
        if stream is None:
            logger.error("ABORT: No functional capture device.")
            self.running = False
            return

        chunks_read = 0
        while self.running:
            if self.paused:
                time.sleep(0.1)
                continue
            try:
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                chunks_read += 1
                if chunks_read % 50 == 0:
                    logger.debug(f"Audio Heartbeat: Read {chunks_read} chunks...")
                
                raw = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                chunk = np.clip(raw, -1.0, 1.0)
                
                if channels > 1:
                    chunk = chunk.reshape(-1, channels).mean(axis=1)
                
                if rate != self.samplerate:
                    chunk = np.interp(np.linspace(0.0, 1.0, int(len(chunk) * self.samplerate / rate)),
                                      np.linspace(0.0, 1.0, len(chunk)), chunk).astype(np.float32)

                if self.on_volume:
                    self.on_volume(float(np.sqrt(np.mean(chunk**2))))

                self.audio_queue.put(chunk)
            except Exception as e:
                logger.error(f"Read error: {e}")
                time.sleep(0.1)
        
        stream.stop_stream()
        stream.close()
        p.terminate()

    def _process_loop(self):
        logger.info("Processing loop started.")
        silence_start_time = None
        
        while self.running:
            try:
                chunks = []
                while not self.audio_queue.empty():
                    chunks.append(self.audio_queue.get())
                
                if not chunks:
                    time.sleep(0.05)
                    if self.speech_buffer and silence_start_time and (time.time() - silence_start_time > self.silence_duration_trigger):
                        self._finalize()
                        silence_start_time = None
                    continue
                
                current_audio = np.concatenate(chunks)
                # Safety check for NaN/Inf
                if not np.all(np.isfinite(current_audio)):
                    continue
                    
                rms = np.sqrt(np.mean(current_audio**2))
                
                # Dynamic VAD
                if rms < self.vad_threshold:
                    self.ambient_noise_level = (1 - self.noise_gate_alpha) * self.ambient_noise_level + self.noise_gate_alpha * rms
                
                self.vad_threshold = max(self.vad_threshold_base, self.ambient_noise_level * 1.5)

                if rms > self.vad_threshold:
                    self.is_speaking = True
                    self.speech_buffer.append(current_audio)
                    self.last_speech_time = time.time()
                    silence_start_time = None
                else:
                    if self.is_speaking:
                        self.speech_buffer.append(current_audio)
                        if silence_start_time is None:
                             silence_start_time = time.time()
                    else:
                        if self.speech_buffer:
                             self.speech_buffer.append(current_audio)
                             if silence_start_time is None:
                                 silence_start_time = time.time()
                
                now = time.time()
                if self.is_speaking and self.speech_buffer and (now - self.last_partial_time > self.partial_interval):
                    self._transcribe_partial()
                    self.last_partial_time = now
                
                # Max duration safety or sentence detection
                buffer_duration = sum(len(c) for c in self.speech_buffer) / self.samplerate
                if buffer_duration > self.max_record_time:
                     self._finalize()
                     silence_start_time = None

            except Exception as e:
                logger.error(f"Error in process loop: {e}")
                time.sleep(0.1)

    def _get_audio_for_whisper(self):
        if not self.speech_buffer:
            return None
        return np.concatenate(list(self.speech_buffer))

    def _should_discard(self, text: str) -> bool:
        if not text: return True
        t = text.strip().lower()
        if len(t) < 2 and not t.isalnum(): return True
        hallucinations = ["subtitle by", "amara", "transcribed by", "captioned by", "thank you", "bye"]
        for h in hallucinations:
            if h in t: return True
        if t.count(".") >= 3 or t.count("?") >= 3: return True
        return False

    def _transcribe_partial(self):
        if not self.model or self.paused: return
        audio = self._get_audio_for_whisper()
        if audio is None or len(audio) < 1000: return
        try:
            segments, _ = self.model.transcribe(audio, beam_size=1, temperature=0.0, language="en", condition_on_previous_text=False)
            text = " ".join([s.text for s in segments if s.no_speech_prob < 0.6]).strip()
            if text:
                logger.debug(f"[Partial] {text}")
            if not self._should_discard(text) and self.on_partial:
                self.on_partial(text)
        except Exception as e:
            logger.warning(f"Partial failed: {e}")

    def _finalize(self):
        if not self.model or not self.speech_buffer or self.paused: return
        audio = self._get_audio_for_whisper()
        self.speech_buffer.clear()
        self.is_speaking = False
        if audio is None or len(audio) < 4000: return

        try:
            segments, _ = self.model.transcribe(audio, beam_size=5, language="en", condition_on_previous_text=False)
            text = " ".join([s.text for s in segments if s.no_speech_prob < 0.6 and s.avg_logprob > -1.0]).strip()
            if not self._should_discard(text) and self.on_final:
                self.on_final(text)
        except Exception as e:
            logger.error(f"Final failed: {e}")

