
import threading
import time
import queue
import collections
import numpy as np
import pyaudio
import logging
from typing import Callable, Optional

# Try to import faster_whisper, handle explicit failure if missing (though we installed it)
try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

logger = logging.getLogger(__name__)

class AudioTranscriber:
    def __init__(self, 
                 model_size: str = "base.en", 
                 device: str = "cpu", 
                 compute_type: str = "int8",
                 on_partial: Optional[Callable[[str], None]] = None,
                 on_final: Optional[Callable[[str], None]] = None):
        
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.on_partial = on_partial
        self.on_final = on_final
        
        self.running = False
        self.audio_queue = queue.Queue()
        self.speech_buffer = [] # List of float32 chunks
        self.samplerate = 16000
        self.chunk_size = 1024
        
        # VAD Parameters
        self.vad_threshold_base = 0.005 # Lower base threshold
        self.vad_threshold = self.vad_threshold_base
        self.noise_gate_alpha = 0.05 # Learning rate for noise floor
        self.ambient_noise_level = 0.001 # Initial guess
        
        self.silence_duration_trigger = 0.8 # seconds of silence to trigger finalization
        self.max_record_time = 30.0 # max seconds before forcing finalization
        
        self.last_speech_time = 0
        self.is_speaking = False
        self.last_partial_time = 0
        self.partial_interval = 0.5 # seconds
        
        self.model = None

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

    def start(self):
        if not WhisperModel:
            logger.error("Cannot start: faster_whisper missing.")
            return

        self.running = True
        
        # Load model in a thread or blocking? Blocking is safer for initialization.
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

    def _record_loop(self):
        p = pyaudio.PyAudio()
        try:
            stream = p.open(format=pyaudio.paFloat32,
                            channels=1,
                            rate=self.samplerate,
                            input=True,
                            frames_per_buffer=self.chunk_size)
        except Exception as e:
            logger.error(f"Failed to open audio stream: {e}")
            return

        logger.info("Recording loop started.")
        while self.running:
            try:
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                # Convert to numpy array
                audio_chunk = np.frombuffer(data, dtype=np.float32)
                self.audio_queue.put(audio_chunk)
            except Exception as e:
                logger.error(f"Audio read error: {e}")
                time.sleep(0.1)
        
        stream.stop_stream()
        stream.close()
        p.terminate()

    def _process_loop(self):
        logger.info("Processing loop started.")
        silence_start_time = None
        
        while self.running:
            try:
                # Get all available chunks
                chunks = []
                while not self.audio_queue.empty():
                    chunks.append(self.audio_queue.get())
                
                if not chunks:
                    time.sleep(0.05)
                    # Check silence timeout if we have buffered speech
                    if self.speech_buffer and silence_start_time and (time.time() - silence_start_time > self.silence_duration_trigger):
                        self._finalize()
                        silence_start_time = None
                    continue
                
                # Concatenate current chunks
                current_audio = np.concatenate(chunks)
                
                # Simple VAD: Check RMS energy
                rms = np.sqrt(np.mean(current_audio**2))
                
                # Dynamic Noise Gate
                # Update ambient noise level if RMS is low (likely silence)
                if rms < self.vad_threshold:
                    self.ambient_noise_level = (1 - self.noise_gate_alpha) * self.ambient_noise_level + self.noise_gate_alpha * rms
                
                # Set threshold relative to ambient noise (e.g. +3dB or fixed margin)
                # Keep a minimum floor to avoid triggering on total silence noise
                self.vad_threshold = max(self.vad_threshold_base, self.ambient_noise_level * 1.5)

                if rms > self.vad_threshold:
                    self.is_speaking = True
                    self.speech_buffer.append(current_audio)
                    self.last_speech_time = time.time()
                    silence_start_time = None
                else:
                    # Silence
                    if self.is_speaking:
                        # We were speaking, now silence -> potential pause
                        self.speech_buffer.append(current_audio) # Keep trailing low energy/silence briefly
                        if silence_start_time is None:
                             silence_start_time = time.time()
                    else:
                        # Continous silence, ignore unless we have a buffer (trailing silence)
                        if self.speech_buffer:
                             self.speech_buffer.append(current_audio)
                             if silence_start_time is None:
                                 silence_start_time = time.time()
                
                # Partial Transcription Trigger
                now = time.time()
                if self.is_speaking and self.speech_buffer and (now - self.last_partial_time > self.partial_interval):
                    self._transcribe_partial()
                    self.last_partial_time = now
                
                # Max duration safety
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
        return np.concatenate(self.speech_buffer)

    def _should_discard(self, text: str) -> bool:
        """New: Filter out common hallucinations and empty noise."""
        if not text: return True
        
        t = text.strip().lower()
        
        # 1. Empty or single punctuation
        if len(t) < 2 and not t.isalnum(): return True
        
        # 2. Known hallucinations (Whisper artifacts)
        hallucinations = [
            "subtitle by", "amara", "transcribed by", "captioned by", 
            "thank you", "thanks for watching", "bye", "invalid",
            ". . .", "? ?"
        ]
        
        for h in hallucinations:
            if h in t:
                return True
                
        # 3. Repetitive noise (e.g. " . . . " or " ? ? ? ")
        if t.count(".") > 3 or t.count("?") > 3:
             return True
             
        return False

    def _transcribe_partial(self):
        if not self.model: return
        
        audio = self._get_audio_for_whisper()
        if audio is None or len(audio) < 1000: return

        # Faster whisper partial
        try:
            # Condition on previous text = False helps prevent loops
            segments, info = self.model.transcribe(
                audio, 
                beam_size=1, 
                temperature=0.0, 
                language="en",
                condition_on_previous_text=False 
            )
            
            # Collect text
            text_segments = []
            for segment in segments:
                # Check probs if available (partial might not have full info)
                if segment.no_speech_prob > 0.6: # High probability of silence
                    continue
                text_segments.append(segment.text)
                
            text = " ".join(text_segments).strip()
            
            if not self._should_discard(text) and self.on_partial:
                self.on_partial(text)
        except Exception as e:
            logger.warning(f"Partial transcription failed: {e}")

    def _finalize(self):
        if not self.model or not self.speech_buffer: return
        
        logger.info("Finalizing speech segment...")
        audio = self._get_audio_for_whisper()
        
        # Reset buffer immediately to catch next phrase
        self.speech_buffer = []
        self.is_speaking = False
        
        if audio is None or len(audio) < 4000: # Ignore very short blips (<0.25s)
             return

        try:
            # Better quality for final
            segments, info = self.model.transcribe(
                audio, 
                beam_size=5, 
                language="en", 
                condition_on_previous_text=False
            )
            
            text_segments = []
            for segment in segments:
                if segment.no_speech_prob > 0.6:
                    continue
                if segment.avg_logprob < -1.0: # Low confidence
                    continue
                text_segments.append(segment.text)

            text = " ".join(text_segments).strip()
            
            if not self._should_discard(text) and self.on_final:
                logger.info(f"Final Text: {text}")
                self.on_final(text)
            else:
                logger.info(f"Discarded text: {text}")

        except Exception as e:
            logger.error(f"Final transcription failed: {e}")

