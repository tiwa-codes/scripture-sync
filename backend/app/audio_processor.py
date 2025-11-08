"""
Audio processing with Whisper for real-time transcription
Supports both microphone input and PA system audio
"""
import asyncio
import queue
import threading
from typing import Optional, Callable
import numpy as np

class AudioProcessor:
    def __init__(self, callback: Optional[Callable] = None):
        self.callback = callback
        self.is_running = False
        self.audio_queue = queue.Queue()
        self.whisper_model = None
        
    def load_whisper_model(self, model_name: str = "base"):
        """Load Whisper model"""
        try:
            import whisper
            self.whisper_model = whisper.load_model(model_name)
            print(f"Loaded Whisper model: {model_name}")
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            raise
    
    def start_listening(self, device_index: Optional[int] = None):
        """Start listening to audio input"""
        try:
            import pyaudio
            
            self.is_running = True
            
            # Audio settings
            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 16000
            
            p = pyaudio.PyAudio()
            
            # Open audio stream
            stream = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=CHUNK
            )
            
            print("Audio stream started. Listening...")
            
            audio_buffer = []
            buffer_duration = 3.0  # Process every 3 seconds
            frames_to_collect = int(RATE * buffer_duration / CHUNK)
            
            while self.is_running:
                try:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    audio_buffer.append(data)
                    
                    if len(audio_buffer) >= frames_to_collect:
                        # Convert to numpy array
                        audio_data = np.frombuffer(b''.join(audio_buffer), dtype=np.int16)
                        audio_float = audio_data.astype(np.float32) / 32768.0
                        
                        # Put in queue for processing
                        self.audio_queue.put(audio_float)
                        audio_buffer = []
                        
                except Exception as e:
                    print(f"Error reading audio: {e}")
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            
        except Exception as e:
            print(f"Error in audio listener: {e}")
            self.is_running = False
    
    def process_audio(self):
        """Process audio from queue using Whisper"""
        while self.is_running:
            try:
                if not self.audio_queue.empty():
                    audio_data = self.audio_queue.get()
                    
                    if self.whisper_model:
                        # Transcribe with Whisper
                        result = self.whisper_model.transcribe(
                            audio_data,
                            language='en',
                            fp16=False
                        )
                        
                        text = result.get('text', '').strip()
                        
                        if text and self.callback:
                            # Call callback with transcribed text
                            asyncio.run(self.callback(text))
                else:
                    threading.Event().wait(0.1)
                    
            except Exception as e:
                print(f"Error processing audio: {e}")
    
    def start(self, device_index: Optional[int] = None):
        """Start audio processing in background threads"""
        # Start listener thread
        listener_thread = threading.Thread(
            target=self.start_listening,
            args=(device_index,),
            daemon=True
        )
        listener_thread.start()
        
        # Start processor thread
        processor_thread = threading.Thread(
            target=self.process_audio,
            daemon=True
        )
        processor_thread.start()
        
        return listener_thread, processor_thread
    
    def stop(self):
        """Stop audio processing"""
        self.is_running = False

class MockAudioProcessor(AudioProcessor):
    """Mock audio processor for testing without actual audio hardware"""
    
    def __init__(self, callback: Optional[Callable] = None):
        super().__init__(callback)
        self.test_mode = True
    
    async def simulate_transcription(self, text: str):
        """Simulate a transcription for testing"""
        if self.callback:
            await self.callback(text)
    
    def start(self, device_index: Optional[int] = None):
        """Mock start - doesn't actually start audio processing"""
        print("Mock audio processor started (test mode)")
        return None, None
