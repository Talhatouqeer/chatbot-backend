import google.generativeai as genai # type: ignore
import asyncio
from app.config import settings
from fastapi import HTTPException, status # type: ignore    
import os
from PIL import Image # type: ignore

# Configure Gemini API
genai.configure(api_key=settings.GEMINI_API_KEY)

# Constants for timeout and retry
GEMINI_TIMEOUT = 60  # 60 seconds timeout instead of 600
MAX_RETRIES = 2  # Retry up to 2 times for network errors
RETRY_DELAY = 1  # Initial delay between retries in seconds


class GeminiService:
    def __init__(self):
        # Use most stable working models for free tier
        # gemini-1.5-flash-latest is the current working free model
        self.text_model = genai.GenerativeModel('gemini-2.5-flash')
        self.vision_model = genai.GenerativeModel('gemini-2.5-flash')
    
    def _generate_text_content_sync(self, message: str) -> str:
        """Synchronous Gemini API call - runs in thread pool to avoid blocking event loop"""
        prompt = f"""You are a helpful bilingual assistant. 
        IMPORTANT: If user writes in Roman Urdu (Urdu in English letters like 'kasay ho'), provide your response in BOTH formats:
        1. First in Urdu script (اردو): میں ٹھیک ہوں
        2. Then in Roman Urdu: (Main theek hoon)
        If user writes in English, reply only in English."""
        prompt += f"\nUser: {message}"
        
        # Optimized config with higher token limit
        generation_config = {
            "temperature": 1.0,
            "max_output_tokens": 2048,  # Higher limit for complete responses
            "top_p": 0.95,
            "top_k": 64
        }
        
        # Safety settings - Allow most content
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        response = self.text_model.generate_content(
            prompt,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        if not response or not response.text:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate response from AI"
            )
        
        return response.text
    
    async def generate_text_response(self, message: str) -> str:
        """
        Generate response for text message - Optimized for speed
        Supports English and Roman Urdu
        """
        last_error = None
        
        # Retry logic for network errors
        for attempt in range(MAX_RETRIES + 1):
            try:
                # Run blocking Gemini API call in thread pool with timeout
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, self._generate_text_content_sync, message),
                    timeout=GEMINI_TIMEOUT
                )
                return result
                
            except asyncio.TimeoutError:
                error_msg = f"Gemini API timeout after {GEMINI_TIMEOUT}s"
                print(f"[ERROR] {error_msg} (attempt {attempt + 1}/{MAX_RETRIES + 1})")
                last_error = HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="AI service timeout. Please try again."
                )
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                    continue
                raise last_error
                
            except HTTPException as e:
                # Re-raise HTTPException immediately, don't retry
                raise e
            except Exception as e:
                error_str = str(e).lower()
                # Check if it's a network/connection error (but not HTTPException)
                is_network_error = any(keyword in error_str for keyword in [
                    '503', 'failed to connect', 'socket', 'connection', 
                    'timeout', 'unreachable', 'dns', 'network', 'failed to connect to all addresses'
                ])
                
                if is_network_error and attempt < MAX_RETRIES:
                    print(f"[WARNING] Network error (attempt {attempt + 1}/{MAX_RETRIES + 1}): {str(e)[:200]}")
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                    last_error = e
                    continue
                else:
                    # Non-retryable error or max retries reached
                    print(f"[ERROR] Error generating text response: {str(e)[:200]}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to generate AI response: {str(e)[:200]}"
                    )
        
        # If we exhausted retries
        if last_error:
            if isinstance(last_error, HTTPException):
                raise last_error
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service temporarily unavailable. Please try again in a moment."
            )
    
    def _generate_image_content_sync(self, message: str, image_path: str) -> str:
        """Synchronous Gemini vision API call - runs in thread pool to avoid blocking event loop"""
        image = None
        try:
            # Open and validate image
            if not os.path.exists(image_path):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Image file not found"
                )
            
            # Open image
            image = Image.open(image_path)
            
            # Simple direct prompt
            prompt = message
            
            # Optimized config with higher token limit
            generation_config = {
                "temperature": 1.0,
                "max_output_tokens": 2048,
                "top_p": 0.95,
                "top_k": 64
            }
            
            # Safety settings - Allow most content
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            # Generate response with image
            response = self.vision_model.generate_content(
                [prompt, image],
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # IMPORTANT: Close image file immediately after use
            if image:
                image.close()
            
            if not response or not response.text:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate response from AI"
                )
            
            return response.text
        except Exception:
            # Make sure to close image on error too
            if image:
                try:
                    image.close()
                except:
                    pass  # Ignore close errors
            raise
    
    async def generate_image_response(self, message: str, image_path: str) -> str:
        """
        Generate response for image with text prompt - Optimized
        """
        last_error = None
        
        # Retry logic for network errors
        for attempt in range(MAX_RETRIES + 1):
            try:
                # Run blocking Gemini API call in thread pool with timeout
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, self._generate_image_content_sync, message, image_path),
                    timeout=GEMINI_TIMEOUT
                )
                return result
                
            except asyncio.TimeoutError:
                error_msg = f"Gemini API timeout after {GEMINI_TIMEOUT}s"
                print(f"[ERROR] {error_msg} (attempt {attempt + 1}/{MAX_RETRIES + 1})")
                last_error = HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="AI service timeout. Please try again."
                )
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                    continue
                raise last_error
                
            except HTTPException as e:
                # Re-raise HTTPException immediately, don't retry
                raise e
            except Exception as e:
                error_str = str(e).lower()
                is_network_error = any(keyword in error_str for keyword in [
                    '503', 'failed to connect', 'socket', 'connection', 
                    'timeout', 'unreachable', 'dns', 'network', 'failed to connect to all addresses'
                ])
                
                if is_network_error and attempt < MAX_RETRIES:
                    print(f"[WARNING] Network error (attempt {attempt + 1}/{MAX_RETRIES + 1}): {str(e)[:200]}")
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                    last_error = e
                    continue
                else:
                    print(f"[ERROR] Error generating image response: {str(e)[:200]}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to generate AI response for image: {str(e)[:200]}"
                    )
        
        if last_error:
            if isinstance(last_error, HTTPException):
                raise last_error
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service temporarily unavailable. Please try again in a moment."
            )
    
    def validate_and_process_message(self, message: str) -> str:
        """
        Validate and process user message
        """
        if not message or len(message.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )
        
        # Limit message length
        if len(message) > 5000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message is too long. Maximum 5000 characters allowed."
            )
        
        return message.strip()


# Create singleton instance
gemini_service = GeminiService()

