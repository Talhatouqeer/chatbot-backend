import os
import asyncio
from fastapi import HTTPException, status
from app.config import get_settings  # import your Pydantic settings

# Constants for timeout
TTS_TIMEOUT = 30  # 30 seconds timeout for TTS
STT_TIMEOUT = 60  # 60 seconds timeout for STT

# Try AssemblyAI for STT (free, MP3 support, no FFmpeg)
try:
    import assemblyai as aai  # type: ignore
    ASSEMBLYAI_AVAILABLE = True
    print("[OK] AssemblyAI loaded successfully")
except ImportError:
    print("[WARNING] AssemblyAI not available. Install: pip install assemblyai")
    ASSEMBLYAI_AVAILABLE = False
    aai = None

# Try gTTS for TTS (free, no API key needed)
try:
    from gtts import gTTS  # type: ignore
    import pygame  # type: ignore
    GTTS_AVAILABLE = True
    print("[OK] gTTS loaded successfully")
except ImportError:
    print("[WARNING] gTTS not available. Install: pip install gtts pygame")
    GTTS_AVAILABLE = False
    gTTS = None

class SpeechService:
    def __init__(self):
        self.settings = get_settings()
        
        # Initialize AssemblyAI for STT
        if ASSEMBLYAI_AVAILABLE and aai:
            api_key = self.settings.ASSEMBLYAI_API_KEY
            if api_key:
                aai.settings.api_key = api_key
                print("[OK] AssemblyAI API key configured")
            else:
                print("[WARNING] ASSEMBLYAI_API_KEY not set in .env")

    def _transcribe_sync(self, audio_file_path: str) -> str:
        """Synchronous transcription - runs in thread pool to avoid blocking event loop"""
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_file_path)
        
        if transcript.status == aai.TranscriptStatus.error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Transcription error: {transcript.error}"
            )
        
        text = transcript.text.strip()
        if not text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not transcribe audio. Please ensure audio is clear and contains speech."
            )
        
        return text
    
    async def convert_voice_to_text(self, audio_file_path: str) -> str:
        """STT: Convert voice note (MP3) to text using AssemblyAI"""
        if not ASSEMBLYAI_AVAILABLE or not aai:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AssemblyAI not available. Please install: pip install assemblyai"
            )
        
        try:
            print(f"[STT] Transcribing audio: {audio_file_path}")
            # Run blocking operation in thread pool with timeout
            loop = asyncio.get_event_loop()
            text = await asyncio.wait_for(
                loop.run_in_executor(None, self._transcribe_sync, audio_file_path),
                timeout=STT_TIMEOUT
            )
            print(f"[OK] STT transcribed ({len(text)} chars): {text[:100]}...")
            return text
        except asyncio.TimeoutError:
            print(f"[ERROR] STT timeout after {STT_TIMEOUT}s")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Transcription timeout. Please try again."
            )
        except HTTPException:
            raise
        except Exception as e:
            print(f"[ERROR] STT error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error transcribing audio: {str(e)}"
            )
    
    def _generate_tts_sync(self, text: str, output_path: str) -> str:
        """Synchronous TTS generation - runs in thread pool to avoid blocking event loop"""
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(output_path)
        return output_path
    
    async def convert_text_to_speech(self, text: str, output_path: str) -> str:
        """TTS: Convert text to audio file using gTTS"""
        if not GTTS_AVAILABLE or not gTTS:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="gTTS not available. Please install: pip install gTTS"
            )
        
        try:
            print(f"[TTS] Converting text to speech ({len(text)} chars)")
            # Run blocking gTTS operation in thread pool with timeout
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, self._generate_tts_sync, text, output_path),
                timeout=TTS_TIMEOUT
            )
            print(f"[OK] TTS audio saved: {output_path}")
            return result
        except asyncio.TimeoutError:
            print(f"[ERROR] TTS timeout after {TTS_TIMEOUT}s")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Text-to-speech timeout. Please try again."
            )
        except Exception as e:
            print(f"[ERROR] TTS error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error converting text to speech: {str(e)}"
            )

# Singleton instance
speech_service = SpeechService()
